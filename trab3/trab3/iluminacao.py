"""
Estado da iluminação (Projeto 3) e envio dos uniforms para o shader.

  - Luz:         uma fonte pontual (posição, cor, atenuação, interruptor).
  - Iluminacao:  junta a luz ambiente, as fontes pontuais e os fatores
                 globais de reflexão difusa/especular controlados pelo teclado.
"""
import glm
from OpenGL.GL import *

import config as cfg
from shaders import uniform


def _limitar(valor, limites):
    return max(limites[0], min(limites[1], valor))


class Luz:
    """Fonte de luz pontual."""

    def __init__(self, nome, cor, atenuacao, interna, posicao=(0.0, 0.0, 0.0)):
        self.nome = nome
        self.cor = glm.vec3(*cor)
        self.constante, self.linear, self.quadratica = atenuacao
        self.interna = interna          # True = só ilumina o ambiente interno
        self.posicao = glm.vec3(*posicao)
        self.ligada = True

    def alternar(self):
        self.ligada = not self.ligada

    def enviar(self, programa, nome_uniform):
        """Preenche a struct Luz do shader (ex.: 'luzes_internas[0]')."""
        u = lambda campo: uniform(programa, f"{nome_uniform}.{campo}")
        glUniform3f(u("posicao"), *self.posicao)
        glUniform3f(u("cor"), *self.cor)
        glUniform1f(u("constante"), self.constante)
        glUniform1f(u("linear"), self.linear)
        glUniform1f(u("quadratica"), self.quadratica)
        glUniform1i(u("ligada"), int(self.ligada))


class Iluminacao:
    def __init__(self):
        # luz ambiente
        self.ambiente_ligada = True
        self.intensidade_ambiente = cfg.AMBIENTE_INICIAL
        # fatores globais (multiplicam o kd / ks de cada material)
        self.fator_difuso = 1.0
        self.fator_especular = 1.0
        # fontes pontuais
        self.luzes = {nome: Luz(nome, info["cor"], info["atenuacao"], info["interna"],
                                info.get("posicao", (0.0, 0.0, 0.0)))
                      for nome, info in cfg.LUZES.items()}
        self.externa = self.luzes["lua"]
        self.internas = [self.luzes["lustre"], self.luzes["abajur"]]

    # ------------------------------------------------------------ teclado
    def alternar_ambiente(self):
        self.ambiente_ligada = not self.ambiente_ligada

    def alternar(self, nome):
        self.luzes[nome].alternar()

    def mudar_ambiente(self, delta):
        self.intensidade_ambiente = _limitar(self.intensidade_ambiente + delta, cfg.AMBIENTE_LIMITES)

    def mudar_difusa(self, delta):
        self.fator_difuso = _limitar(self.fator_difuso + delta, cfg.FATOR_LIMITES)

    def mudar_especular(self, delta):
        self.fator_especular = _limitar(self.fator_especular + delta, cfg.FATOR_LIMITES)

    # ------------------------------------------------------------ shader
    def enviar(self, programa):
        """Uniforms que valem para o quadro inteiro (iguais para todos os objetos)."""
        glUniform1i(uniform(programa, "ambiente_ligada"), int(self.ambiente_ligada))
        glUniform1f(uniform(programa, "intensidade_ambiente"), self.intensidade_ambiente)
        glUniform3f(uniform(programa, "cor_ambiente"), *cfg.COR_AMBIENTE)
        glUniform1f(uniform(programa, "fator_difuso"), self.fator_difuso)
        glUniform1f(uniform(programa, "fator_especular"), self.fator_especular)
        self.externa.enviar(programa, "luz_externa")
        for i, luz in enumerate(self.internas):
            luz.enviar(programa, f"luzes_internas[{i}]")

    # ------------------------------------------------------------ texto
    def resumo(self):
        """Linha curta para o título da janela e o console."""
        on = lambda b: "ON" if b else "off"
        return (f"Ambiente {on(self.ambiente_ligada)} {self.intensidade_ambiente:.2f} | "
                f"Difusa x{self.fator_difuso:.1f} | Especular x{self.fator_especular:.1f} | "
                f"Lua {on(self.externa.ligada)} | Lustre {on(self.luzes['lustre'].ligada)} | "
                f"Abajur {on(self.luzes['abajur'].ligada)}")
