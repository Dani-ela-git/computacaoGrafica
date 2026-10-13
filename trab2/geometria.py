"""Geometria simples gerada por codigo: pisos, oceano, paredes da cabine,
casco do navio com proa/popa, chaminés e iceberg."""

import numpy as np


def quad(p0, p1, p2, p3, rep_u=1.0, rep_v=1.0):
    """Quadrilatero p0-p1-p2-p3 (anti-horario) em 2 triangulos."""
    uv = [(0, 0), (rep_u, 0), (rep_u, rep_v), (0, rep_v)]
    p = [p0, p1, p2, p3]
    ordem = [0, 1, 2, 0, 2, 3]
    return np.array([[*p[i], *uv[i]] for i in ordem], dtype=np.float32)


def triangulo(p0, p1, p2, uv0=(0, 0), uv1=(1, 0), uv2=(0.5, 1)):
    """Um triangulo simples com UVs."""
    return np.array([
        [*p0, *uv0],
        [*p1, *uv1],
        [*p2, *uv2],
    ], dtype=np.float32)


def plano(x_min, x_max, z_min, z_max, y, metros_por_textura):
    ru = (x_max - x_min) / metros_por_textura
    rv = (z_max - z_min) / metros_por_textura
    return quad((x_min, y, z_max), (x_max, y, z_max), (x_max, y, z_min), (x_min, y, z_min), ru, rv)


def parede(a, b, y0, y1, metros_por_textura=2.0, esticar_v=False):
    """Parede vertical entre (x,z) a e b, de y0 ate y1."""
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
        parede((x0, z0), (x1, z0), 0, h),
        parede((x1, z1), (x0, z1), 0, h),
        parede((x0, z1), (x0, z0), 0, h),
        parede((x1, z0), (x1, -meia), 0, h),
        parede((x1, meia), (x1, z1), 0, h),
        parede((x1, -meia), (x1, meia), ph, h),
    ]
    return np.vstack(partes)


def casco(conves, nivel_oceano, altura_amurada):
    """Casco do navio com proa e popa afilada (+X) a (-X).

    Topologia (vista de cima, +X direita):
        z=+z1   D---C-------B
              /              \
         z=-z1 popa                A (proa) -- ponta em x_proa, z=0
             \               /
              \             /
                D---C------B
                ^
    """
    x0, x1, z0, z1 = conves["x_min"], conves["x_max"], conves["z_min"], conves["z_max"]
    y0, y1 = nivel_oceano, altura_amurada

    fator_proa = 0.25
    fator_popa = 0.25
    extensao_proa = 8.0
    extensao_popa = 6.0

    ponta_proa_x = x1 + extensao_proa
    ponta_popa_x = x0 - extensao_popa

    # z onde o afilamento começa
    z_p1 = z1 - (z1 - z0) * fator_proa
    z_p0 = z0 + (z1 - z0) * fator_proa
    z_q1 = z1 - (z1 - z0) * fator_popa
    z_q0 = z0 + (z1 - z0) * fator_popa

    partes = []

    # lateral de cima (z = z1): reta, do x0 ao x1
    partes.append(parede((x0, z1), (x1, z1), y0, y1, 4.0, True))

    #lateral de baixo (z = z0): reta, do x1 ao x0
    partes.append(parede((x1, z0), (x0, z0), y0, y1, 4.0, True))

    # PROA (+X): do z1 até ponta, e da ponta até z0
    partes.append(quad(
        (x1, y0, z1), (ponta_proa_x, y0, 0.0),
        (ponta_proa_x, y1, 0.0), (x1, y1, z1), 2.0, 1.0
    ))
    partes.append(quad(
        (ponta_proa_x, y0, 0.0), (x1, y0, z0),
        (x1, y1, z0), (ponta_proa_x, y1, 0.0), 2.0, 1.0
    ))

    # POPA (-X): do z0 até ponta, e da ponta até z1
    partes.append(quad(
        (x0, y0, z0), (ponta_popa_x, y0, 0.0),
        (ponta_popa_x, y1, 0.0), (x0, y1, z0), 2.0, 1.0
    ))
    partes.append(quad(
        (ponta_popa_x, y0, 0.0), (x0, y0, z1),
        (x0, y1, z1), (ponta_popa_x, y1, 0.0), 2.0, 1.0
    ))

    return np.vstack(partes)

def conves_afilado(x_min, x_max, z_min, z_max, y, metros_textura,
                    fator_proa=0.25, extensao_proa=8.0,
                    fator_popa=0.35, extensao_popa=3.0):
    """Convés cuja ponta (+X) acompanha o casco afilado para
    não ficar um buraco entre o chão do convés e o casco"""
    dados = []
    
    #  cantos na base da proa (onde o afilamento começa)
    xp_min = x_max   # onde o corpo reto termina e a proa começa
    xp_max = x_max + extensao_proa


    # cantos na base da popa
    xq_min = x_min - extensao_popa
    xq_max = x_min

    # CORPO CENTRAL: retângulo de (x_min, z_min) a (x_max, z_max)
    p0 = (x_min, y, z_max)
    p1 = (x_max, y, z_max)
    p2 = (x_max, y, z_min)
    p3 = (x_min, y, z_min)

    for tri in [(p0, p1, p2), (p0, p2, p3)]:
        for v in tri:
            u = (v[0] - xq_min) / metros_textura
            w = (v[2] - z_min) / metros_textura
            dados.extend([*v, u, w])

    # PROA: triângulo de (x_max, z_max) a (x_max, z_min) até a ponta
    ponta_proa = (xp_max, y, 0.0)
    for v in [(x_max, y, z_max), ponta_proa, (x_max, y, z_min)]:
        u = (v[0] - xq_min) / metros_textura
        w = (v[2] - z_min) / metros_textura
        dados.extend([*v, u, w])

    # POPA: triângulo de (x_min, z_min) a (x_min, z_max) até a ponta
    ponta_popa = (xq_min, y, 0.0)
    for v in [(x_min, y, z_min), ponta_popa, (x_min, y, z_max)]:
        u = (v[0] - xq_min) / metros_textura
        w = (v[2] - z_min) / metros_textura
        dados.extend([*v, u, w])

    return np.array(dados, dtype=np.float32)

def cilindro(centro_x, centro_z, y_base, altura, raio, lados=16):
    """Cilindro vertical (chaminé). centro em (x,z), de y_base até y_base+altura."""
    cx, cz = centro_x, centro_z
    dados = []
    for i in range(lados):
        a0 = 2 * np.pi * i / lados
        a1 = 2 * np.pi * (i + 1) / lados
        x0, z0 = cx + raio * np.cos(a0), cz + raio * np.sin(a0)
        x1, z1 = cx + raio * np.cos(a1), cz + raio * np.sin(a1)
        # dois triângulos da lateral
        dados.extend([
            x0, y_base, z0, 0, 0,
            x1, y_base, z1, 1, 0,
            x1, y_base + altura, z1, 1, 1,
            x0, y_base, z0, 0, 0,
            x1, y_base + altura, z1, 1, 1,
            x0, y_base + altura, z0, 0, 1,
        ])
        # topo (tampa)
        dados.extend([
            cx, y_base + altura, cz, 0.5, 0.5,
            x0, y_base + altura, z0, 0, 0,
            x1, y_base + altura, z1, 1, 0,
        ])
    return np.array(dados, dtype=np.float32)


def superestrutura(x_min, x_max, z_min, z_max, y_base, altura, portas=True):
    """Bloco retangular sólido com janelas nas laterais (visão externa)."""
    partes = []
    # paredes do bloco
    partes.append(parede((x_min, z_min), (x_max, z_min), y_base, y_base + altura, 2.0))
    partes.append(parede((x_max, z_max), (x_min, z_max), y_base, y_base + altura, 2.0))
    partes.append(parede((x_min, z_max), (x_min, z_min), y_base, y_base + altura, 2.0))
    partes.append(parede((x_max, z_min), (x_max, z_max), y_base, y_base + altura, 2.0))
    # teto
    partes.append(plano(x_min, x_max, z_min, z_max, y_base + altura, 2.0))
    return np.vstack(partes)


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