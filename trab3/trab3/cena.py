"""
Monta a cena com a classe Mesh: pisos, cabine, casco, oceano, skybox, os
modelos .obj e (Projeto 3) as fontes de luz: a lua que anda pelo céu, o
lustre do teto e o abajur da cabine. Também anima a lua e desenha tudo com
iluminação.
"""
import math
import os
import glm
import numpy as np
from OpenGL.GL import *

import config as cfg
import geometria as geo
from mesh import Mesh
from shaders import uniform
from texture_loader import carregar_cubemap
from iluminacao import Iluminacao


class Objeto:
    """Uma instância de uma Mesh na cena, com posição, rotação e escala próprias
    e (Projeto 3) material, ambiente (interno/externo) e, se for uma lâmpada,
    a luz que a faz brilhar."""

    def __init__(self, mesh, material, interno, posicao=(0, 0, 0), rotacao_y=0.0, escala=1.0,
                 luz=None, brilho=1.0):
        self.mesh = mesh
        self.material = cfg.MATERIAIS[material]
        self.interno = interno
        self.posicao = glm.vec3(*posicao)
        self.rotacao_y = float(rotacao_y)
        self.escala = float(escala)
        self.luz = luz          # Luz que este objeto representa (ou None)
        # quanto da cor da luz ele emite quando ligada: um número, ou (r, g, b)
        # para corrigir a cor (ex.: a lua não deve ficar azulada como a sua luz)
        self.brilho = glm.vec3(*brilho) if isinstance(brilho, (tuple, list)) else glm.vec3(brilho)

    def matriz_model(self):
        # Model = Translação * Rotação * Escala (a escala é aplicada primeiro),
        m = glm.translate(glm.mat4(1.0), self.posicao)
        m = glm.rotate(m, glm.radians(self.rotacao_y), glm.vec3(0, 1, 0))
        return glm.scale(m, glm.vec3(self.escala))

    def emissao(self):
        """Lâmpada acesa brilha com a cor da sua luz; apagada não emite nada."""
        if self.luz is not None and self.luz.ligada:
            return self.luz.cor * self.brilho
        return glm.vec3(0.0)

    def desenhar(self, programa):
        m = self.material
        glUniform1f(uniform(programa, "ka"), m["ka"])
        glUniform1f(uniform(programa, "kd"), m["kd"])
        glUniform1f(uniform(programa, "ks"), m["ks"])
        glUniform1f(uniform(programa, "ns"), m["ns"])
        glUniform3f(uniform(programa, "cor_base"), *m["cor"])
        glUniform3f(uniform(programa, "emissao"), *self.emissao())
        glUniform1i(uniform(programa, "interno"), int(self.interno))
        self.mesh.desenhar(self.matriz_model())


class Lua:
    """Objeto externo iluminado com translação."""

    def __init__(self, programa, luz):
        info = cfg.LUA
        self.luz = luz
        self.tempo = 0.0
        self.pausado = False
        # lua.obj é uma esfera de raio 1 centrada na origem (sem normalizar);
        # quem dá o tamanho (escala) e a posição no céu (translação) é a model
        mesh = Mesh(info["obj"], info["textura"], programa)
        self.objeto = Objeto(mesh, "lua", False, escala=info["raio"],
                             luz=luz, brilho=info["brilho"])
        self.atualizar(0.0)

    def atualizar(self, dt):
        info = cfg.LUA
        if not self.pausado:
            self.tempo += dt
        angulo = math.radians(90.0 + info["amplitude"] * math.sin(info["velocidade"] * self.tempo))
        r = info["raio_orbita"]

        # TRANSLAÇÃO: nova posição no arco
        self.objeto.posicao = glm.vec3(r * math.cos(angulo),
                                       info["y_centro"] + r * math.sin(angulo),
                                       info["z"])
        self.luz.posicao = glm.vec3(self.objeto.posicao)   # luz acompanha a lua


class Cena:
    def __init__(self, programa, programa_ceu):
        self.programa = programa
        self.programa_ceu = programa_ceu
        self.mostrar_malha = False
        self.iluminacao = Iluminacao()
        self._criar_estrutura()
        self.carregar_modelos()
        self._criar_luminarias()
        self.criar_ceu()

    # montagem

    def estatico(self, vertices, chave_textura, interno, material=None):
        """Objeto gerado por código (não conta entre os modelos .obj)."""
        mesh = Mesh.de_vertices(vertices, cfg.TEXTURAS[chave_textura], self.programa)
        return Objeto(mesh, material or chave_textura, interno)

    def _criar_estrutura(self):
        c, cab = cfg.CONVES, cfg.CABINE
        meio = cfg.TAMANHO_OCEANO / 2
        sup = cfg.SUPERESTRUTURA
        cha = cfg.CHAMINES

        # chaminés (um mesh por chaminé e empilhadas)
        chamines = []
        for x in cha["posicoes_x"]:
            verts = geo.cilindro(x, cha["z"], cha["y_base"], cha["altura"], cha["raio"])
            chamines.append(verts)

        # Lado de FORA das paredes da cabine: uma "casca" 2 cm para fora.
        # Assim a parede vista do convés é um objeto EXTERNO (recebe a lua)
        # e a vista de dentro é INTERNA (recebe lustre e abajur).
        fora = dict(cab, x_min=cab["x_min"] - 0.02, x_max=cab["x_max"] + 0.02,
                    z_min=cab["z_min"] - 0.02, z_max=cab["z_max"] + 0.02)

        self.estrutura = [
            # --- EXTERNO ---
            self.estatico(geo.plano(-meio, meio, -meio, meio, cfg.NIVEL_OCEANO, 40.0), "oceano", False),
            self.estatico(geo.conves_afilado( c["x_min"], c["x_max"], c["z_min"], c["z_max"],
            0.0, 1.8, fator_proa=0.25, extensao_proa=8.0, fator_popa=0.25, extensao_popa=6.0), "conves", False),
            self.estatico(geo.casco(c, cfg.NIVEL_OCEANO, cfg.ALTURA_AMURADA), "casco", False),

            # --- superestrutura (bloco externo em cima do convés) ---
            self.estatico(geo.superestrutura(
                sup["x_min"], sup["x_max"], sup["z_min"], sup["z_max"],
                sup["y_base"], sup["altura"]
            ), "superestrutura", False),

            # --- CHAMINÉS (4 cilindros) ---
            self.estatico(np.vstack(chamines), "chamines", False),
            self.estatico(geo.paredes_cabine(fora), "parede", False, material="parede_externa"),

            # --- INTERNO (cabine) ---
            self.estatico(geo.plano(cab["x_min"], cab["x_max"], cab["z_min"], cab["z_max"], 0.02, 0.4), "carpete", True),
            self.estatico(geo.paredes_cabine(cab), "parede", True),
            self.estatico(geo.plano(cab["x_min"], cab["x_max"], cab["z_min"], cab["z_max"], cab["altura"], 2.0), "teto", True),
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
                        giro_base=info.get("giro_base", (0, 0, 0)),
                        normais_planas=info.get("normais_planas", False))
            self.modelos[nome] = [Objeto(mesh, nome, info["interno"], (x, y, z), ry)
                                  for (x, y, z, ry) in info["instancias"]]

    def _criar_luminarias(self):
        """Fontes de luz e as peças que as representam na cena."""
        luzes = self.iluminacao.luzes
        p = self.programa
        cab = cfg.CABINE

        # ---------------- externa: lua (translação pelo céu)
        self.lua = Lua(p, luzes["lua"])

        # ---------------- interna 1: lustre no teto (centro da cabine)
        L = cfg.LUSTRE
        gy = luzes["lustre"].posicao.y
        metal = Mesh.de_vertices(np.vstack([
            geo.cilindro(L["x"], L["z"], cab["altura"] - 0.04, 0.04, 0.12, tampa_baixo=True),  # canopla
            geo.cilindro(L["x"], L["z"], gy + L["raio_globo"] * 0.8,
                         cab["altura"] - gy - L["raio_globo"] * 0.8, 0.015),                  # haste
            geo.cilindro(L["x"], L["z"], gy + L["raio_globo"] * 0.75, 0.05, 0.08),            # bocal
        ]), None, p)
        globo = Mesh.de_vertices(geo.esfera(L["x"], gy, L["z"], L["raio_globo"]), None, p)

        # ---------------- interna 2: abajur sobre um criado-mudo ao lado da cama
        C = cfg.CRIADO_MUDO
        x, z, h = C["x"], C["z"], C["altura"]
        ay = luzes["abajur"].posicao.y
        movel = Mesh.de_vertices(geo.caixa(x - C["largura"] / 2, x + C["largura"] / 2, 0.0, h,
                                           z - C["profundidade"] / 2, z + C["profundidade"] / 2),
                                 None, p)
        pe = Mesh.de_vertices(np.vstack([
            geo.cilindro(x, z, h, 0.03, 0.10, tampa_baixo=True),   # base redonda
            geo.cilindro(x, z, h + 0.03, ay - h - 0.03, 0.015),    # haste
        ]), None, p)
        cupula = Mesh.de_vertices(geo.tronco_cone(x, z, ay - 0.10, 0.24, 0.18, 0.09), None, p)
        lampada = Mesh.de_vertices(geo.esfera(x, ay, z, 0.05), None, p)

        self.luminarias = [
            Objeto(metal, "latao", True),
            Objeto(globo, "globo_lustre", True, luz=luzes["lustre"], brilho=1.0),
            Objeto(movel, "criado_mudo", True),
            Objeto(pe, "latao", True),
            Objeto(cupula, "cupula", True, luz=luzes["abajur"], brilho=0.45),  # cúpula translúcida
            Objeto(lampada, "lampada_abajur", True, luz=luzes["abajur"], brilho=1.0),
        ]

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

    # animação / teclado
    def atualizar(self, dt):
        """Move a lua (e a luz junto)."""
        self.lua.atualizar(dt)

    def pausar_lua(self):
        self.lua.pausado = not self.lua.pausado

    def alternar_malha(self):
        self.mostrar_malha = not self.mostrar_malha

    def todos_objetos(self):
        yield from self.estrutura
        for lista in self.modelos.values():
            yield from lista
        yield self.lua.objeto
        yield from self.luminarias

    # desenho
    def desenhar(self, view, projection, posicao_camera):
        p = self.programa
        glUseProgram(p)

        # uniforms iguais para todos os objetos do quadro
        glUniformMatrix4fv(uniform(p, "view"), 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(uniform(p, "projection"), 1, GL_FALSE, glm.value_ptr(projection))
        glUniform3f(uniform(p, "viewPos"), *posicao_camera)   # para a especular
        glUniform1i(uniform(p, "texture1"), 0)
        self.iluminacao.enviar(p)

        # objetos: preenchidos ou só as arestas (tecla 'p')
        glUniform1i(uniform(p, "modo_malha"), int(self.mostrar_malha))
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if self.mostrar_malha else GL_FILL)

        for obj in self.todos_objetos():
            obj.desenhar(p)

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
