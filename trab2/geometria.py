"""Geometria simples gerada por codigo: pisos, oceano, paredes da cabine e
casco do navio. Esses sao os objetos que delimitam os ambientes."""

import numpy as np


def quad(p0, p1, p2, p3, rep_u=1.0, rep_v=1.0):
    """Quadrilatero p0-p1-p2-p3 (sentido anti-horario) em 2 triangulos."""
    uv = [(0, 0), (rep_u, 0), (rep_u, rep_v), (0, rep_v)]
    p = [p0, p1, p2, p3]
    ordem = [0, 1, 2, 0, 2, 3]
    return np.array([[*p[i], *uv[i]] for i in ordem], dtype=np.float32)


def plano(x_min, x_max, z_min, z_max, y, metros_por_textura):
    ru = (x_max - x_min) / metros_por_textura
    rv = (z_max - z_min) / metros_por_textura
    return quad((x_min, y, z_max), (x_max, y, z_max), (x_max, y, z_min), (x_min, y, z_min), ru, rv)


def parede(a, b, y0, y1, metros_por_textura=2.0, esticar_v=False):
    """Parede vertical entre os pontos (x, z) a e b, da altura y0 ate y1.
    esticar_v=True: a imagem ocupa a altura inteira uma unica vez (usado no casco)."""
    comprimento = np.hypot(b[0] - a[0], b[1] - a[1])
    rep_v = 1.0 if esticar_v else (y1 - y0) / metros_por_textura
    return quad((a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1]),
                comprimento / metros_por_textura, rep_v)


def paredes_cabine(c):
    """Quatro paredes; a parede x = x_max tem um vao de porta no meio."""
    x0, x1, z0, z1, h = c["x_min"], c["x_max"], c["z_min"], c["z_max"], c["altura"]
    meia = c["porta_largura"] / 2
    ph = c["porta_altura"]
    partes = [
        parede((x0, z0), (x1, z0), 0, h),              # fundo
        parede((x1, z1), (x0, z1), 0, h),              # frente
        parede((x0, z1), (x0, z0), 0, h),              # lateral cega
        parede((x1, z0), (x1, -meia), 0, h),           # lateral da porta: parte 1
        parede((x1, meia), (x1, z1), 0, h),            # parte 2
        parede((x1, -meia), (x1, meia), ph, h),        # acima da porta
    ]
    return np.vstack(partes)


def casco(conves, nivel_oceano, altura_amurada):
    """Laterais do navio: do nivel do mar ate a amurada."""
    x0, x1, z0, z1 = conves["x_min"], conves["x_max"], conves["z_min"], conves["z_max"]
    y0, y1 = nivel_oceano, altura_amurada
    return np.vstack([
        parede((x0, z0), (x1, z0), y0, y1, 4.0, True),
        parede((x1, z0), (x1, z1), y0, y1, 4.0, True),
        parede((x1, z1), (x0, z1), y0, y1, 4.0, True),
        parede((x0, z1), (x0, z0), y0, y1, 4.0, True),
    ])


def cubo_ceu():
    """36 vertices de um cubo unitario (so posicao) para a skybox."""
    f = [
        (-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (-1, -1, -1), (-1, 1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1),
        (1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, 1), (1, 1, -1), (1, -1, -1),
        (-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1),
        (-1, 1, -1), (1, 1, -1), (1, 1, 1), (1, 1, 1), (-1, 1, 1), (-1, 1, -1),
        (-1, -1, -1), (-1, -1, 1), (1, -1, -1), (1, -1, -1), (-1, -1, 1), (1, -1, 1),
    ]
    return np.array(f, dtype=np.float32)