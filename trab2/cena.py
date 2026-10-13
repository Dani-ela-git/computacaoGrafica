"""
Monta a cena com a classe Mesh: pisos, cabine, casco, oceano, skybox e os
modelos .obj. Também aplica as transformações do teclado e desenha tudo.
"""
import os
import glm
import numpy as np
from OpenGL.GL import *

import config as cfg
import geometria as geo
from mesh import Mesh
from texture_loader import carregar_cubemap


class Objeto:
    """Uma instância de uma Mesh na cena, com posição, rotação e escala próprias."""

    def __init__(self, mesh, posicao=(0, 0, 0), rotacao_y=0.0, escala=1.0):
        self.mesh = mesh
        self.posicao = glm.vec3(*posicao)
        self.rotacao_y = float(rotacao_y)
        self.escala = float(escala)

    def matriz_model(self):
        # Model = Translação * Rotação * Escala (a escala é aplicada primeiro),
        m = glm.translate(glm.mat4(1.0), self.posicao)
        m = glm.rotate(m, glm.radians(self.rotacao_y), glm.vec3(0, 1, 0))
        return glm.scale(m, glm.vec3(self.escala))

    def desenhar(self, view, projection):
        self.mesh.desenhar(view, projection, self.matriz_model())


class Cena:
    def __init__(self, programa, programa_ceu):
        self.programa = programa
        self.programa_ceu = programa_ceu
        self.mostrar_malha = False
        self._criar_estrutura()
        self.carregar_modelos()
        self.criar_ceu()

    # ------------------------------------------------------------ montagem
    def estatico(self, vertices, chave_textura):
        """Objeto gerado por código (não conta entre os modelos .obj)."""
        return Objeto(Mesh.de_vertices(vertices, cfg.TEXTURAS[chave_textura], self.programa))

        def _criar_estrutura(self):
        """Navio e oceano, gerados por código (delimitam os ambientes;
        não contam entre os modelos .obj). O último número de cada plano
        é a cada quantos metros a textura se repete (escala real)."""
        c, cab = cfg.CONVES, cfg.CABINE
        meio = cfg.TAMANHO_OCEANO / 2
        self.estrutura = [
            # piso EXTERNO: convés de madeira (~1,8 m por repetição)
            self.estatico(geo.plano(c["x_min"], c["x_max"], c["z_min"], c["z_max"], 0.0, 1.8), "conves"),
            # oceano em volta do navio
            self.estatico(geo.plano(-meio, meio, -meio, meio, cfg.NIVEL_OCEANO, 6.0), "oceano"),
            # laterais do navio, do nível do mar até a amurada
            self.estatico(geo.casco(c, cfg.NIVEL_OCEANO, cfg.ALTURA_AMURADA), "casco"),
            # piso INTERNO: carpete (~40 cm por repetição), 2 cm acima do convés
            self.estatico(geo.plano(cab["x_min"], cab["x_max"], cab["z_min"], cab["z_max"], 0.02, 0.4), "carpete"),
            # paredes da cabine (com vão de porta) e teto
            self.estatico(geo.paredes_cabine(cab), "parede"),
            self.estatico(geo.plano(cab["x_min"], cab["x_max"], cab["z_min"], cab["z_max"], cab["altura"], 2.0), "teto"),
        ]

    def carregar_modelos(self):
        """Carrega cada .obj em tamanho real e cria as instâncias."""
        self.modelos = {}      # nome -> lista de Objeto
        for nome, info in cfg.MODELOS.items():
            if not os.path.isfile(info["obj"]):
                print(f"  [aviso] {nome}: arquivo não encontrado ({info['obj']}), pulando")
                self.modelos[nome] = []
                continue
            print(f"Carregando {nome}...")
            mesh = Mesh(info["obj"], info.get("textura"), self.programa,
                        altura=info.get("altura"), comprimento=info.get("comprimento"),
                        giro_base=info.get("giro_base", (0, 0, 0)))
            self.modelos[nome] = [Objeto(mesh, (x, y, z), ry) for (x, y, z, ry) in info["instancias"]]

    def criar_ceu(self):
        self.tex_ceu = carregar_cubemap(cfg.SKYBOX)
        vertices = geo.cubo_ceu()
        self.vao_ceu = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(self.vao_ceu)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, None)
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

    # ------------------------------------------------------ transformações
    def transladar(self, dx, dz):
        """TRANSLAÇÃO: move o iceberg pelo oceano."""
        lim = cfg.LIMITES_ICEBERG
        for obj in self.modelos[cfg.MODELO_TRANSLACAO]:
            obj.posicao.x = float(np.clip(obj.posicao.x + dx, lim["x_min"], lim["x_max"]))
            obj.posicao.z = float(np.clip(obj.posicao.z + dz, lim["z_min"], lim["z_max"]))

    def rotacionar(self, graus):
        """ROTAÇÃO: gira o bote salva-vidas em torno do eixo vertical."""
        for obj in self.modelos[cfg.MODELO_ROTACAO]:
            obj.rotacao_y = (obj.rotacao_y + graus) % 360.0

    def escalar(self, fator):
        """ESCALA: aumenta/diminui a boia. Como a origem do modelo está na base,
        ela continua apoiada no chão enquanto muda de tamanho."""
        lo, hi = cfg.LIMITES_ESCALA
        for obj in self.modelos[cfg.MODELO_ESCALA]:
            obj.escala = float(np.clip(obj.escala * fator, lo, hi))

    def alternar_malha(self):
        self.mostrar_malha = not self.mostrar_malha

    # --------------------------------------------------------------- desenho
    def desenhar(self, view, projection):
        # objetos: preenchidos ou só as arestas (tecla 'p')
        glUseProgram(self.programa)
        glUniform1i(glGetUniformLocation(self.programa, "modo_malha"), int(self.mostrar_malha))
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if self.mostrar_malha else GL_FILL)
        #glClearColor(1.0, 0.0, 0.0, 1.0)   # vermelho vivo
        #glClear(GL_COLOR_BUFFER_BIT)       # limpa só a cor

        # ---- DEBUG ----
        #if not hasattr(self, "_printou"):
            # self._printou = True
            # print("=== ESTRUTURA ===")
            # for i, obj in enumerate(self.estrutura):
            #     m = obj.mesh
            #     print(f"  [{i}] VAO={m.VAO} partes={len(m.partes)} "
            #           f"qtd_idx={m.partes[0][1] if m.partes else 0} "
            #           f"pos={tuple(obj.posicao)}")
            # print("=== MODELOS ===")
            # for nome, lista in self.modelos.items():
            #     for obj in lista:
            #         m = obj.mesh
            #         print(f"  {nome}: VAO={m.VAO} partes={len(m.partes)} "
            #               f"qtd_idx={m.partes[0][1] if m.partes else 0}")
            # # matrizes da câmera
            # print("=== CÂMERA ===")
            # print(f"  view[3] (pos): {glm.vec3(view[3])}")
            # # escolhe um objeto da estrutura (o convés = índice 0) e mostra
            # # o resultado da multiplicação view*model*posição de um vértice
            # conv = self.estrutura[0]
            # proj = projection
            # mvp = proj * view * conv.matriz_model()
            # print(f"  MVP do convés:\n{mvp}")
        # ---- FIM DEBUG ----
        
        for obj in self.estrutura:
            obj.desenhar(view, projection)
        for lista in self.modelos.values():
            for obj in lista:
                obj.desenhar(view, projection)
                
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)   # ← não escreve no depth buffer
        
        glUseProgram(self.programa_ceu)
        view_sem_translacao = glm.mat4(glm.mat3(view))
        glUniformMatrix4fv(glGetUniformLocation(self.programa_ceu, "view"), 1, GL_FALSE,
                           glm.value_ptr(view_sem_translacao))
        glUniformMatrix4fv(glGetUniformLocation(self.programa_ceu, "projection"), 1, GL_FALSE,
                           glm.value_ptr(projection))
        glUniform1i(glGetUniformLocation(self.programa_ceu, "skybox"), 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.tex_ceu)
        glBindVertexArray(self.vao_ceu)
        glDrawArrays(GL_TRIANGLES, 0, 36)
        glBindVertexArray(0)
        
        glDepthMask(GL_TRUE)   # ← restaura
        glDepthFunc(GL_LESS)
