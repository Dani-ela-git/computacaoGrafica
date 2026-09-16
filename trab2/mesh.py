"""Classe que representa um modelo 3D carregado de um arquivo .obj, com textura e shader."""

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import glm
import ctypes

from obj_loader import carregar_obj
from texture_loader import carregar_textura

class Mesh:
    def __init__(self, obj_path, textura_path, shader_program):
        self.vertices, self.indices = carregar_obj(obj_path)
        self.textura_id = carregar_textura(textura_path)
        self.program = shader_program

        #transformacao local do objeto (posição, rotação e escala)
        self.model = glm.mat4(1.0)  # matriz identidade

        #buffers do OpenGL
        self.VAO = None
        self.__criar_buffers()

    def __criar_buffers(self):
        #cria VAO 
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # VBO: posições + uv intercalados 
        VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        # EBO: índices
        EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        #layout do shader: [x, y, z, u, v] → 5 floats por vértice = 20 bytes
        stride = 5*4 # 5 floats * 4 bytes/float

        # atributo 0: position (3 floats, offset 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride,
                              ctypes.c_void_p(0))

        # atributo 1: texcoord (2 floats, offset 12 bytes)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride,
                              ctypes.c_void_p(12))

        glBindVertexArray(0)

    def set_transform(self, matriz):
        """Define a matriz model do objeto (glm.mat4)."""
        self.model = matriz

    def desenhar(self, view, projection):
        """Desenha o modelo com a view e projection atuais."""
        glUseProgram(self.program)

        #passa as matrizes para o shader
        loc_model = glGetUniformLocation(self.program, "model")
        loc_view = glGetUniformLocation(self.program, "view")
        loc_projection = glGetUniformLocation(self.program, "projection")

        glUniformMatrix4fv(loc_model, 1, GL_FALSE, glm.value_ptr(self.model))
        glUniformMatrix4fv(loc_view, 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(loc_projection, 1, GL_FALSE, glm.value_ptr(projection))

        #ativa a textura
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.textura_id)   
        glUniform1i(glGetUniformLocation(self.program, "texture1"), 0)  # textura no slot 0

        #desenha
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)