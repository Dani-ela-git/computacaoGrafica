"""Classe que representa um modelo 3D carregado de um arquivo .obj, com textura e shader."""

from OpenGL.GL import *
import numpy as np
import glm
import ctypes
import os

from obj_loader import carregar_obj, carregar_obj_por_material, normalizar
from texture_loader import carregar_textura


class Mesh:
    def __init__(self, obj_path, textura_path, shader_program,
                 altura=None, comprimento=None, giro_base=(0, 0, 0)):
        """
        obj_path        arquivo .obj
        textura_path    imagem da textura. Se for None, usa as texturas do .mtl
                        (útil para modelos com mais de uma imagem).
        altura /        opcional: ajusta o modelo para essa altura OU esse
        comprimento     comprimento em metros, com a base em y = 0.
        giro_base       opcional: corrige modelos "deitados", ex.: (-90, 0, 0).
        """
        self.program = shader_program
        self.model = glm.mat4(1.0)

        # Cada "parte" = um material com sua textura. Um modelo comum tem só uma.
        if textura_path is not None:
            self.vertices, self.indices = carregar_obj(obj_path)
            grupos = [(self.vertices, self.indices, textura_path)]
        else:
            grupos = carregar_obj_por_material(obj_path)
            self.vertices, self.indices = grupos[0][0], grupos[0][1]

        if altura is not None or comprimento is not None or any(giro_base):
            normalizar([g[0] for g in grupos], altura, comprimento, giro_base)

        self.montar(grupos)

    @classmethod
    def de_vertices(cls, vertices, textura_path, shader_program):
        """Cria uma Mesh a partir de vértices gerados no código (pisos, paredes...)."""
        malha = cls.__new__(cls)
        malha.program = shader_program
        malha.model = glm.mat4(1.0)
        malha.vertices = np.ascontiguousarray(vertices, dtype=np.float32).ravel()
        malha.indices = np.arange(len(vertices) // 5, dtype=np.uint32)
        malha.montar([(malha.vertices, malha.indices, textura_path)])
        return malha

    def montar(self, grupos):
        self.partes = []   # lista de (VAO, quantidade de índices, id da textura)
        for vertices, indices, textura in grupos:
            vao = self.criar_buffers(vertices, indices)
            self.partes.append((vao, len(indices), carregar_textura(textura)))
        self.VAO = self.partes[0][0]
        self.textura_id = self.partes[0][2]

    def criar_buffers(self, vertices, indices):
        # cria VAO
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        # VBO: posições + uv intercalados
        VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # EBO: índices
        EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # layout do shader: [x, y, z, u, v] → 5 floats por vértice = 20 bytes
        stride = 5 * 4

        # atributo 0: position (3 floats, offset 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        # atributo 1: texcoord (2 floats, offset 12 bytes)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))

        glBindVertexArray(0)
        return vao

    def set_transform(self, matriz):
        """Define a matriz model do objeto (glm.mat4)."""
        self.model = matriz

    def desenhar(self, view, projection, model=None):
        """Desenha o modelo com a view e projection atuais.
        'model' é opcional: permite desenhar a MESMA malha em várias posições."""
        glUseProgram(self.program)

        # passa as matrizes para o shader
        loc_model = glGetUniformLocation(self.program, "model")
        loc_view = glGetUniformLocation(self.program, "view")
        loc_projection = glGetUniformLocation(self.program, "projection")

        glUniformMatrix4fv(loc_model, 1, GL_FALSE,
                           glm.value_ptr(model if model is not None else self.model))
        glUniformMatrix4fv(loc_view, 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(loc_projection, 1, GL_FALSE, glm.value_ptr(projection))

        glUniform1i(glGetUniformLocation(self.program, "texture1"), 0)

        # desenha cada parte com sua textura
        for vao, quantidade, textura in self.partes:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, textura)
            glBindVertexArray(vao)
            glDrawElements(GL_TRIANGLES, quantidade, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)