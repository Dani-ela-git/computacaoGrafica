"""Script de teste para verificar se a textura está sendo 
carregada corretamente e aplicada ao modelo 3D."""

import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glm
import numpy as np
import math

from shaders import vertex_code, fragment_code
from mesh import Mesh


# Inicializa janela
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
window = glfw.create_window(800, 600, "Teste Mesh Texturizada", None, None)
if not window:
    glfw.terminate()
    raise RuntimeError("Falha ao criar janela")
glfw.make_context_current(window)
glfw.show_window(window)


# Compila shader 
program = compileProgram(
    compileShader(vertex_code, GL_VERTEX_SHADER),
    compileShader(fragment_code, GL_FRAGMENT_SHADER)
)


# Câmera simples 
camera_pos = glm.vec3(0.0, 1.0, 3.0)
camera_front = glm.vec3(0.0, 0.0, -1.0)
camera_up = glm.vec3(0.0, 1.0, 0.0)

def get_view():
    return glm.lookAt(camera_pos, camera_pos + camera_front, camera_up)

def get_projection():
    return glm.perspective(glm.radians(45.0), 800/600, 0.1, 100.0)


#  Carrega o modelo 
ceramica = Mesh(
    obj_path="trab2/assets/models/ceramicvase.obj",
    textura_path="trab2/assets/textures/ceramivaseTexture.jpg",
    shader_program=program
)

# Ajusta escala/posição (varia por modelo, deve ajustar olhando o resultado)
ceramica.set_transform(
    glm.scale(glm.mat4(1.0), glm.vec3(0.5))
)


# Key events
def key_event(window, key, scancode, action, mods):
    global mostrar_malha
    if action == glfw.PRESS or action == glfw.REPEAT:
        if key == glfw.KEY_P:
            mostrar_malha = not mostrar_malha
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)

mostrar_malha = False
glfw.set_key_callback(window, key_event)


# Depth test 
glEnable(GL_DEPTH_TEST)


# Loop principal
glClearColor(0.2, 0.2, 0.3, 1.0)

while not glfw.window_should_close(window):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    if mostrar_malha:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # Câmera orbital simples para poer ver o modelo de vários ângulos
    t = glfw.get_time()
    camera_pos.x = 3.0 * math.sin(t * 0.5)
    camera_pos.z = 3.0 * math.cos(t * 0.5)
    camera_front = glm.normalize(glm.vec3(0.0) - camera_pos)

    ceramica.desenhar(get_view(), get_projection())

    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()