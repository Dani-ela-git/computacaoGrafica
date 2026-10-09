"""
Câmera em primeira pessoa (mouse + WASD).
Gera as matrizes view e projection e restringe a exploração aos limites
do céu e do terreno.
"""
import glm

import config as cfg

CIMA = glm.vec3(0.0, 1.0, 0.0)


class Camera:
    def __init__(self):
        self.posicao = glm.vec3(*cfg.POSICAO_INICIAL)
        self.yaw = -90.0      # olhando para -Z
        self.pitch = 0.0
        self.fov = cfg.FOV    # alterado pela roda do mouse (zoom)

    # --------------------------------------------------------- direções
    def frente(self):
        # mesma fórmula do mouse_callback das aulas 
        y, p = glm.radians(self.yaw), glm.radians(self.pitch)
        return glm.normalize(glm.vec3(glm.cos(y) * glm.cos(p), glm.sin(p), glm.sin(y) * glm.cos(p)))

    def frente_horizontal(self):
        y = glm.radians(self.yaw)
        return glm.vec3(glm.cos(y), 0.0, glm.sin(y))

    def direita(self):
        return glm.normalize(glm.cross(self.frente_horizontal(), CIMA))

    # --------------------------------------------------------- controle
    def girar(self, dx, dy):
        self.yaw += dx
        self.pitch = max(-89.0, min(89.0, self.pitch + dy))

    def mover(self, deslocamento):
        anterior = glm.vec3(self.posicao)
        self.posicao += deslocamento
        self.restringir(anterior)

    def restringir(self, anterior):
        """Mantém a câmera dentro do cenário.
        o casco funciona como parede quando a câmera está fora do navio,
        abaixo da altura do convés."""
        p = self.posicao
        lim = cfg.TAMANHO_OCEANO / 2 - 5.0
        p.x = max(-lim, min(lim, p.x))
        p.z = max(-lim, min(lim, p.z))
        p.y = max(cfg.NIVEL_OCEANO + 1.0, min(cfg.ALTURA_MAX, p.y))

        c = cfg.CONVES
        sobre_navio = lambda q: c["x_min"] <= q.x <= c["x_max"] and c["z_min"] <= q.z <= c["z_max"]
        if sobre_navio(p) and p.y < cfg.ALTURA_OLHOS_MIN:
            if sobre_navio(anterior):
                p.y = cfg.ALTURA_OLHOS_MIN         # piso
            else:
                p.x, p.z = anterior.x, anterior.z  # bateu no casco

    # --------------------------------------------------------- matrizes
    def get_view(self):
        return glm.lookAt(self.posicao, self.posicao + self.frente(), CIMA)

    def get_projection(self, largura, altura):
        return glm.perspective(glm.radians(self.fov), largura / altura,
                               cfg.PLANO_PERTO, cfg.PLANO_LONGE)