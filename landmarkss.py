import cv2
import mediapipe as mp
import time
import numpy as np

mp_manos = mp.solutions.hands
manos = mp_manos.Hands(
    static_image_mode=False,  
    max_num_hands=1,         
    min_detection_confidence=0.9,  
    min_tracking_confidence=0.8   
)
mp_dibujo = mp.solutions.drawing_utils

GUIA_GESTOS = {
    'A': "Dedos cerrados + pulgar encima",
    'K': "Indice + medio levantados y separados",
    'T': "Solo indice levantado",
    '5': "Mano abierta",
    '22': "Indice + medio juntos levantados",
    '37': "Indice + medio + anular levantados juntos",
    'G': "Indice levantado + pulgar arriba",
    'U': "Indice + medio juntos levantados"
}

TIEMPO_CONFIRMACION_GESTO = 1.0
TIEMPO_MAXIMO_AGUA = 5.0
TIEMPO_MOSTRAR_AGUA = 1.5

def dibujar_guia_compacta(frame):
    ancho_guia = 250
    pos_x = frame.shape[1] - ancho_guia - 20
    altura_guia = 220 
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (pos_x-10, 10), (frame.shape[1]-10, 10 + altura_guia), (50, 50, 50), -1)
    alpha = 0.7
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    cv2.putText(frame, "GUIA DE GESTOS:", (pos_x, 35), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA) 
    
    y_inicial = 60  
    for i, (gesto, descripcion) in enumerate(GUIA_GESTOS.items()):
        cv2.putText(frame, f"{gesto}:", (pos_x, y_inicial + i*22),  
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(frame, descripcion, (pos_x + 30, y_inicial + i*22),  
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

def dedo_extendido(puntos_mano, punta, base, umbral=0.03):
    """Determina si un dedo está extendido"""
    return puntos_mano[punta].y < puntos_mano[base].y - umbral

def pulgar_extendido(puntos_mano, umbral=0.03):
    """Determina si el pulgar está extendido"""
    return puntos_mano[4].x > puntos_mano[3].x + umbral

def detectar_gesto(puntos_mano):
    """Identifica el gesto basado en la posición de los dedos"""
    if not puntos_mano:
        return None
    
    dedos = [
        dedo_extendido(puntos_mano, 8, 6), 
        dedo_extendido(puntos_mano, 12, 10), 
        dedo_extendido(puntos_mano, 16, 14), 
        dedo_extendido(puntos_mano, 20, 18)  
    ]
    pulgar = pulgar_extendido(puntos_mano)
    distancia_indice_medio = abs(puntos_mano[8].x - puntos_mano[12].x)
    
    # Lógica de detección para cada gesto
    if not any(dedos) and pulgar:
        return 'A'
    if dedos[0] and dedos[1] and not any(dedos[2:]):
        if distancia_indice_medio < 0.05:
            return '22' if pulgar else 'U'
    if all(dedos[:3]) and not dedos[3]:
        return '37'
    if all(dedos):
        return '5'
    if dedos[0] and not any(dedos[1:]):
        return 'G' if not pulgar else 'T'
    if dedos[0] and dedos[1] and not dedos[2]:
        return 'K'
    return None

# Estado del programa
gesto_actual = None
tiempo_inicio_gesto = 0
secuencia_agua = []
ultimo_tiempo_agua = 0
tiempo_agua_completa = 0
mostrar_agua_completa = False

# Inicializar cámara
camara = cv2.VideoCapture(0)
camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while camara.isOpened():
    exito, frame = camara.read()
    if not exito:
        continue
    
    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    resultados = manos.process(frame_rgb)
    
    tiempo_actual = time.time()
    gesto_detectado = None
    mano_detectada = False
    
    if resultados.multi_hand_landmarks:
        mano_detectada = True
        for puntos_mano in resultados.multi_hand_landmarks:
            # Dibujar landmarks con sus números
            for idx, punto in enumerate(puntos_mano.landmark):
                x = int(punto.x * frame.shape[1])
                y = int(punto.y * frame.shape[0])
                cv2.putText(frame, str(idx), (x, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Dibujar conexiones entre landmarks
            mp_dibujo.draw_landmarks(
                frame, 
                puntos_mano, 
                mp_manos.HAND_CONNECTIONS,
                mp_dibujo.DrawingSpec(color=(128, 23, 8), thickness=2, circle_radius=3),
                mp_dibujo.DrawingSpec(color=(243, 182, 145), thickness=2, circle_radius=2))
            
            # Detectar gesto actual
            gesto_detectado = detectar_gesto(puntos_mano.landmark)
            
            if gesto_detectado:
                if gesto_detectado != gesto_actual:
                    gesto_actual = gesto_detectado
                    tiempo_inicio_gesto = tiempo_actual
                    # Guardar posición del dedo índice como referencia
                    ultima_posicion_detectada = (
                        int(puntos_mano.landmark[8].x * frame.shape[1]),
                        int(puntos_mano.landmark[8].y * frame.shape[0])
                    )
                
                # Confirmar gesto después del tiempo establecido
                if tiempo_actual - tiempo_inicio_gesto > TIEMPO_CONFIRMACION_GESTO:
                    # Procesar secuencia AGUA
                    if gesto_actual in ['A', 'G', 'U'] and not mostrar_agua_completa:
                        if not secuencia_agua and gesto_actual == 'A':
                            secuencia_agua = ['A']
                            ultimo_tiempo_agua = tiempo_actual
                        elif secuencia_agua:
                            siguiente_letra = 'G' if secuencia_agua[-1] == 'A' else 'U' if secuencia_agua[-1] == 'G' else 'A' if secuencia_agua[-1] == 'U' else None
                            if gesto_actual == siguiente_letra:
                                secuencia_agua.append(gesto_actual)
                                ultimo_tiempo_agua = tiempo_actual
                                # Verificar si se completó AGUA (A-G-U-A)
                                if len(secuencia_agua) >= 4 and secuencia_agua[-4:] == ['A', 'G', 'U', 'A']:
                                    mostrar_agua_completa = True
                                    tiempo_agua_completa = tiempo_actual
                                    secuencia_agua = []
    
    # Reiniciar estados si no se detecta mano o pasa el tiempo máximo
    if not mano_detectada or (secuencia_agua and (tiempo_actual - ultimo_tiempo_agua) > TIEMPO_MAXIMO_AGUA):
        secuencia_agua = []
        gesto_actual = None
        tiempo_inicio_gesto = 0
    
    # Ocultar "AGUA" después del tiempo de visualización
    if mostrar_agua_completa and (tiempo_actual - tiempo_agua_completa) > TIEMPO_MOSTRAR_AGUA:
        mostrar_agua_completa = False
    
    dibujar_guia_compacta(frame)
    
    # Mostrar gesto detectado actual
    if gesto_actual and (tiempo_actual - tiempo_inicio_gesto > TIEMPO_CONFIRMACION_GESTO) and not mostrar_agua_completa:
        texto_mostrar = f"{gesto_actual} ({ultima_posicion_detectada[0]}, {ultima_posicion_detectada[1]})"
        cv2.putText(frame, "Detectado:", (30, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, texto_mostrar, (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    
    # Mostrar progreso de AGUA
    if secuencia_agua and not mostrar_agua_completa:
        texto_progreso = "".join(secuencia_agua)
        cv2.putText(frame, "Formando AGUA:", (30, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 12, 0), 2)
        cv2.putText(frame, texto_progreso, (50, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 12, 0), 3)
        tiempo_restante = max(0, TIEMPO_MAXIMO_AGUA - (tiempo_actual - ultimo_tiempo_agua))
        cv2.putText(frame, f"Tiempo: {tiempo_restante:.1f}s", (50, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 12, 0), 2)
    
    # Mostrar AGUA completa brevemente
    if mostrar_agua_completa:
        cv2.putText(frame, "AGUA", 
                   (frame.shape[1]//2 - 60, frame.shape[0]//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 0), 4)
    
    # Mostrar ventana
    cv2.imshow('Detección de Lenguaje de Señas', frame)
    
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

camara.release()
cv2.destroyAllWindows()