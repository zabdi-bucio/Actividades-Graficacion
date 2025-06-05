import glfw 
from OpenGL.GL import *
from OpenGL.GLU import *
import math

quad = None

# Inicialización de GLFW
def init_window():
    if not glfw.init():
        return None
    window = glfw.create_window(800, 600, "Piezas de Ajedrez en OpenGL", None, None)
    if not window:
        glfw.terminate()
        return None
    glfw.make_context_current(window)
    return window

def draw_cube(size):
    s = size / 2.0
    vertices = [
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
        [-s, -s,  s], [s, -s,  s], [s, s,  s], [-s, s,  s],
    ]
    faces = [
        [0, 1, 2, 3], [4, 5, 6, 7],
        [0, 4, 7, 3], [1, 5, 6, 2],
        [3, 2, 6, 7], [0, 1, 5, 4],
    ]
    glBegin(GL_QUADS)
    for face in faces:
        for v in face:
            glVertex3fv(vertices[v])
    glEnd()

def draw_crown():
    glPushMatrix()
    glTranslatef(0, 1.2, 0)
    for i in range(8):
        glPushMatrix()
        angle = 360 / 8 * i
        glRotatef(angle, 0, 1, 0)
        glTranslatef(0.3, 0, 0)
        gluSphere(quad, 0.05, 10, 10)
        glPopMatrix()
    glPopMatrix()

def draw_rook_top():
    for i in range(4):
        glPushMatrix()
        angle = 360 / 4 * i
        glRotatef(angle, 0, 1, 0)
        glTranslatef(0.25, 1.1, 0)
        draw_cube(0.1)
        glPopMatrix()

def draw_pawn():
    glPushMatrix()
    gluCylinder(quad, 0.3, 0.3, 1, 32, 32)
    glTranslatef(0, 0, 1)
    gluSphere(quad, 0.3, 32, 32)
    glPopMatrix()

def draw_queen():
    glPushMatrix()
    gluCylinder(quad, 0.4, 0.3, 1, 32, 32)
    glTranslatef(0, 0, 1)
    gluSphere(quad, 0.3, 32, 32)
    draw_crown()
    glPopMatrix()

def draw_king():
    glPushMatrix()
    gluCylinder(quad, 0.4, 0.3, 1, 32, 32)
    glTranslatef(0, 0, 1)
    gluSphere(quad, 0.3, 32, 32)
    draw_crown()
    glPushMatrix()
    glTranslatef(0, 0.4, 0)
    glScalef(0.02, 0.2, 0.02)
    draw_cube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0.4, 0)
    glScalef(0.2, 0.02, 0.02)
    draw_cube(1)
    glPopMatrix()
    glPopMatrix()

def draw_bishop():
    glPushMatrix()
    gluCylinder(quad, 0.35, 0.3, 1, 32, 32)
    glTranslatef(0, 0, 1)
    glScalef(1, 1.5, 1)
    gluSphere(quad, 0.3, 32, 32)
    glPopMatrix()

def draw_knight():
    glPushMatrix()
    gluCylinder(quad, 0.35, 0.3, 1, 32, 32)
    glTranslatef(0, 0, 1)
    glPushMatrix()
    glRotatef(-45, 1, 0, 0)
    gluCylinder(quad, 0.1, 0.0, 0.6, 32, 32)
    glPopMatrix()
    glPopMatrix()

def draw_rook():
    glPushMatrix()
    gluCylinder(quad, 0.35, 0.35, 1, 32, 32)
    glTranslatef(0, 0, 1)
    draw_rook_top()
    glPopMatrix()

def draw_all_pieces():
    spacing = 1.5
    draw_functions = [draw_pawn, draw_queen, draw_king, draw_bishop, draw_knight, draw_rook]
    for i, func in enumerate(draw_functions):
        glPushMatrix()
        glTranslatef(-4.0 + i * spacing, 0, 0)
        # Rota para poner vertical la pieza (altura eje Y)
        glRotatef(-90, 1, 0, 0)
        func()
        glPopMatrix()

def main():
    global quad
    window = init_window()
    if not window:
        return

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.2, 1.0)  # Fondo gris

    # Proyección
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 800 / 600, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    # Luz
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION,  (5, 5, 5, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE,   (1.0, 1.0, 1.0, 1.0))

    quad = gluNewQuadric()

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(0, 5, 12, 0, 0, 0, 0, 1, 0)

        # Material azul para las piezas con iluminación
        blue = [0.0, 0.0, 1.0, 1.0]
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, blue)

        draw_all_pieces()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
