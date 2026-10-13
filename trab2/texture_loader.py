""" Vamos usar a biblioteca PIL para carregar imagens e gerar texturas OpenGL. """

from PIL import Image
from OpenGL.GL import *
import numpy as np
import os

cache = {} #apenas para evitar subir a mesma imagem para a GPU duas vezes


def carregar_textura(caminho_arquivo):
    """
    Carrega uma imagem (.png/.jpg) com PIL e sobe pra GPU.
    Retorna o ID da textura do OpenGL.
    """

    if caminho_arquivo in cache:
        return cache[caminho_arquivo]
    if not caminho_arquivo or not os.path.isfile(caminho_arquivo):
        print(f"  [aviso] textura não encontrada: {caminho_arquivo} (usando xadrez)")
        return textura_xadrez()
    
    # PIL carrega como RGB (sem alpha), por isso estamos usando o convert
    img = Image.open(caminho_arquivo).convert("RGBA")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)   # OpenGL inverte o eixo Y

    largura, altura = img.size
    dados = np.array(img, dtype=np.uint8)

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    # Filtros (evita textura borrada/pixelada estranha)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Sobe os pixels
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, largura, altura, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, dados)

    # Gera mipmaps (melhora a qualidade quando o objeto está longe)
    glGenerateMipmap(GL_TEXTURE_2D)

    glBindTexture(GL_TEXTURE_2D, 0)
    return tex_id

def textura_xadrez():
    """Textura de erro. Apenas para facilitar vizualizar se as texturas foram carregadas"""

    if "xadrez" in cache:
        return cache["xadrez"]
    dados = np.zeros((8,8,4), dtype=np.uint8)
    for x in range(8):
        for y in range(8):
            dados[y, x] = (255, 0, 255, 255) if (x + y) % 2 else (20, 20, 20, 255)
    tex_id = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 8, 8, 0, GL_RGBA, GL_UNSIGNED_BYTE, dados)
    glBindTexture(GL_TEXTURE_2D, 0)
    cache["__xadrez__"] = tex_id

    return tex_id

def carregar_cubemap(caminhos):
    """Skybox: 6 imagens na ordem +X, -X, +Y, -Y, +Z, -Z
    (right, left, top, bottom, front, back).
    GL_CLAMP_TO_EDGE + GL_TEXTURE_CUBE_MAP_SEAMLESS evitam bordas visíveis."""

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, tex_id)

    for i, caminho in enumerate(caminhos):
        img = Image.open(caminho).convert("RGB")      # cubemap NÃO é invertido
        dados = np.array(img, dtype=np.uint8)
        glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB, img.size[0], img.size[1],
                     0, GL_RGB, GL_UNSIGNED_BYTE, dados)
        
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    for eixo in (GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_WRAP_R):
        glTexParameteri(GL_TEXTURE_CUBE_MAP, eixo, GL_CLAMP_TO_EDGE)

    glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS)
    glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
    return tex_id