"""Classe que representa um modelo 3D (de um .obj ou gerado por código), com
textura e shader. No Projeto 3 cada vértice passou a ter também a NORMAL,
usada no cálculo da iluminação."""

from OpenGL.GL import *
import numpy as np
import glm
import ctypes

from obj_loader import carregar_obj, carregar_obj_por_material, normalizar, FLOATS_POR_VERTICE
from texture_loader import carregar_textura, textura_branca
from geometria import com_normais
from shaders import uniform


class Mesh:
    def __init__(self, obj_path, textura_path, shader_program,
                 altura=None, comprimento=None, giro_base=(0, 0, 0), normais_planas=False):
        """
        obj_path        arquivo .obj
        textura_path    imagem da textura. Se for None, usa as texturas do .mtl
                        (útil para modelos com mais de uma imagem).
        altura /        ajusta o modelo para essa altura 
        comprimento     comprimento em metros, com a base em y = 0.
        giro_base       corrige modelos "deitados", ex.: (-90, 0, 0).
        normais_planas  uma normal por face (visual low-poly).
        """
        self.program = shader_program
        self.model = glm.mat4(1.0)

        # Cada "parte" = um material com sua textura. Um modelo comum tem só uma.
        if textura_path is not None:
            self.vertices, self.indices = carregar_obj(obj_path, normais_planas)
            grupos = [(self.vertices, self.indices, textura_path)]
        else:
            grupos = carregar_obj_por_material(obj_path, normais_planas)
            self.vertices, self.indices = grupos[0][0], grupos[0][1]

        if altura is not None or comprimento is not None or any(giro_base):
            normalizar([g[0] for g in grupos], altura, comprimento, giro_base)

        self.montar(grupos)

    @classmethod
    def de_vertices(cls, vertices, textura_path, shader_program):
        """Cria uma Mesh a partir de vértices gerados no código.
        Aceita [x,y,z,u,v] (a normal de cada triângulo é calculada aqui) ou
        [x,y,z,u,v,nx,ny,nz]. textura_path=None usa uma textura branca
        (a cor vem do uniform cor_base)."""
        malha = cls.__new__(cls)
        malha.program = shader_program
        malha.model = glm.mat4(1.0)

        dados = np.asarray(vertices, dtype=np.float32)
        if dados.ndim == 1:
            dados = dados.reshape(-1, 5)
        malha.vertices = np.ascontiguousarray(com_normais(dados)).ravel()
        malha.indices = np.arange(len(malha.vertices) // FLOATS_POR_VERTICE, dtype=np.uint32)

        malha.montar([(malha.vertices, malha.indices, textura_path)], branca_se_vazio=True)
        return malha

    def montar(self, grupos, branca_se_vazio=False):
        self.partes = []   # lista de (VAO, quantidade de índices, id da textura)
        for vertices, indices, textura in grupos:
            vao = self.criar_buffers(vertices, indices)
            tex = textura_branca() if (textura is None and branca_se_vazio) else carregar_textura(textura)
            self.partes.append((vao, len(indices), tex))
        self.VAO = self.partes[0][0]
        self.textura_id = self.partes[0][2]

    def criar_buffers(self, vertices, indices):
        # cria VAO
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        # VBO: posições + uv + normal intercalados
        VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # EBO: índices
        EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # layout do shader: [x, y, z, u, v, nx, ny, nz] → 8 floats por vértice = 32 bytes
        stride = FLOATS_POR_VERTICE * 4

        # atributo 0: position (3 floats, offset 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        # atributo 1: texcoord (2 floats, offset 12 bytes)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))

        # atributo 2: normal (3 floats, offset 20 bytes)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(20))

        glBindVertexArray(0)
        return vao

    def set_transform(self, matriz):
        """Define a matriz model do objeto (glm.mat4)."""
        self.model = matriz

    def desenhar(self, model=None):
        """Desenha o modelo. view, projection, luzes e material já foram
        enviados pela Cena/Objeto; aqui só vai a matriz model.
        'model' é opcional: permite desenhar a MESMA malha em várias posições."""
        glUniformMatrix4fv(uniform(self.program, "model"), 1, GL_FALSE,
                           glm.value_ptr(model if model is not None else self.model))

        # desenha cada parte com sua textura
        for vao, quantidade, textura in self.partes:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, textura)
            glBindVertexArray(vao)
            glDrawElements(GL_TRIANGLES, quantidade, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
