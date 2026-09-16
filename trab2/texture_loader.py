""" Vamos usar a biblioteca PIL para carregar imagens e gerar texturas OpenGL. """

from PIL import Image
from OpenGL.GL import *
import numpy as np


def carregar_textura(caminho_arquivo):
    """
    Carrega uma imagem (.png/.jpg) com PIL e sobe pra GPU.
    Retorna o ID da textura do OpenGL.
    """
    # PIL carrega como RGB (sem alpha). Se quiser alpha, use .convert("RGBA")
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