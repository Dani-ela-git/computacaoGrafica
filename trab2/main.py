"""
Computação Gráfica (SCC0250) - Projeto 2
Cena: "Titanic, 14 de abril de 1912"

Controles
  Mouse / setas ........ olhar ao redor
  Roda do mouse ........ zoom
  W A S D .............. andar
  Espaço / Ctrl ........ subir / descer
  Shift ................ correr
  I K J L .............. TRANSLAÇÃO do iceberg
  R T .................. ROTAÇÃO do bote salva-vidas
  Z X .................. ESCALA da boia
  P .................... mostrar/ocultar malha poligonal
  Esc .................. sair
"""
import glfw
import glm
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

import config as cfg
from camera import Camera
from cena import Cena
from shaders import vertex_code, fragment_code, skybox_vertex_code, skybox_fragment_code


# ------------------------------------------------------------- janela
glfw.init()
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)   # necessário no macOS
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
window = glfw.create_window(cfg.LARGURA_JANELA, cfg.ALTURA_JANELA, cfg.TITULO, None, None)
if not window:
    glfw.terminate()
    raise RuntimeError("Falha ao criar janela")
glfw.make_context_current(window)
glfw.swap_interval(1)


# -------------------------------------------------- shaders
vao_validacao = glGenVertexArrays(1)
glBindVertexArray(vao_validacao)
program = compileProgram(
    compileShader(vertex_code, GL_VERTEX_SHADER),
    compileShader(fragment_code, GL_FRAGMENT_SHADER)
)
program_ceu = compileProgram(
    compileShader(skybox_vertex_code, GL_VERTEX_SHADER),
    compileShader(skybox_fragment_code, GL_FRAGMENT_SHADER)
)
glBindVertexArray(0)


# ------------------------------------------------------- cena e câmera
camera = Camera()
cena = Cena(program, program_ceu)


# ------------------------------------------------------------- eventos
def key_event(window, key, scancode, action, mods):
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_ESCAPE:
        # se o cursor está travado, libera; se está livre, fecha a janela
        modo = glfw.get_input_mode(window, glfw.CURSOR)
        if modo == glfw.CURSOR_DISABLED:
            glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
        else:
            glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_P:
        cena.alternar_malha()


ultimo_mouse = None


def mouse_callback(window, xpos, ypos):
    global ultimo_mouse
    if ultimo_mouse is None:
        ultimo_mouse = (xpos, ypos)
    dx, dy = xpos - ultimo_mouse[0], ultimo_mouse[1] - ypos   # y invertido
    ultimo_mouse = (xpos, ypos)
    camera.girar(dx * cfg.SENSIBILIDADE_MOUSE, dy * cfg.SENSIBILIDADE_MOUSE)


def scroll_callback(window, xoffset, yoffset):
    """Roda do mouse: zoom alterando o fov, como nas aulas."""
    camera.fov = max(20.0, min(cfg.FOV, camera.fov - yoffset))


def teclas_continuas(dt):
    """Teclas que agem enquanto estão pressionadas (movimento suave)."""
    apertada = lambda k: glfw.get_key(window, k) == glfw.PRESS

    # --- câmera
    vel = cfg.VELOCIDADE * (3.0 if apertada(glfw.KEY_LEFT_SHIFT) else 1.0) * dt
    d = glm.vec3(0.0)
    if apertada(glfw.KEY_W): d += camera.frente_horizontal()
    if apertada(glfw.KEY_S): d -= camera.frente_horizontal()
    if apertada(glfw.KEY_D): d += camera.direita()
    if apertada(glfw.KEY_A): d -= camera.direita()
    if apertada(glfw.KEY_SPACE): d.y += 1.0
    if apertada(glfw.KEY_LEFT_CONTROL): d.y -= 1.0
    if glm.length(d) > 0:
        camera.mover(glm.normalize(d) * vel)
    giro = 90.0 * dt
    if apertada(glfw.KEY_LEFT):  camera.girar(-giro, 0)
    if apertada(glfw.KEY_RIGHT): camera.girar(giro, 0)
    if apertada(glfw.KEY_UP):    camera.girar(0, giro)
    if apertada(glfw.KEY_DOWN):  camera.girar(0, -giro)

    # --- translação (iceberg)
    t = cfg.VEL_TRANSLACAO * dt
    if apertada(glfw.KEY_I): cena.transladar(0, t)     # aproxima do navio
    if apertada(glfw.KEY_K): cena.transladar(0, -t)
    if apertada(glfw.KEY_J): cena.transladar(-t, 0)
    if apertada(glfw.KEY_L): cena.transladar(t, 0)

    # --- rotação (bote)
    if apertada(glfw.KEY_R): cena.rotacionar(cfg.VEL_ROTACAO * dt)
    if apertada(glfw.KEY_T): cena.rotacionar(-cfg.VEL_ROTACAO * dt)

    # --- escala (boia)
    f = 1.0 + cfg.VEL_ESCALA * dt
    if apertada(glfw.KEY_X): cena.escalar(f)
    if apertada(glfw.KEY_Z): cena.escalar(1.0 / f)


glfw.set_key_callback(window, key_event)
glfw.set_cursor_pos_callback(window, mouse_callback)
glfw.set_scroll_callback(window, scroll_callback)
glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)


# ------------------------------------------------------------- loop
glfw.show_window(window)
glEnable(GL_DEPTH_TEST)
glDisable(GL_CULL_FACE)
glClearColor(0.02, 0.03, 0.08, 1.0)

ultimo_frame = glfw.get_time()     # deltaTime, co mo nas aulas
while not glfw.window_should_close(window):
    agora = glfw.get_time()
    dt = min(agora - ultimo_frame, 0.1)
    ultimo_frame = agora

    glfw.poll_events()
    teclas_continuas(dt)

    largura, altura = glfw.get_framebuffer_size(window)
    if altura == 0:        # janela minimizada
        continue
    glViewport(0, 0, largura, altura)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    cena.desenhar(camera.get_view(), camera.get_projection(largura, altura))
    glfw.swap_buffers(window)

glfw.terminate()