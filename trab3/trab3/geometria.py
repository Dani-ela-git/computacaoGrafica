"""Geometria simples gerada por codigo: pisos, oceano, paredes da cabine,
casco do navio com proa/popa, chaminés e, no Projeto 3, as peças das
fontes de luz (lustre, abajur, criado-mudo e lua).

Formatos de saída:
  - funções "antigas" (quad, plano, parede, casco...) devolvem [x, y, z, u, v];
    a normal de cada triângulo é calculada depois por com_normais();
  - funções de superfícies curvas (cilindro, esfera, cone) já devolvem
    [x, y, z, u, v, nx, ny, nz] com normais suaves, para a luz não "facetar".
"""

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
    r"""Casco do navio com proa e popa afilada (+X) a (-X).

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

def com_normais(vertices):
    """Recebe triângulos [x, y, z, u, v] (n, 5) e devolve (n, 8) com a normal
    de cada triângulo (normal "plana", ideal para paredes, pisos e caixas).
    Se já vier com 8 colunas, devolve igual."""
    v = np.asarray(vertices, dtype=np.float32)
    if v.ndim == 1:
        v = v.reshape(-1, 5)
    if v.shape[1] == 8:
        return v
    tri = v[:, :3].reshape(-1, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    return np.hstack([v, np.repeat(n, 3, axis=0)]).astype(np.float32)


def cilindro(centro_x, centro_z, y_base, altura, raio, lados=16, tampa_baixo=False):
    """Cilindro vertical (chaminé, haste de luminária...). Centro em (x,z),
    de y_base até y_base+altura. Lateral com normais suaves (apontam para fora
    a partir do eixo); tampas com normal +Y / -Y."""
    cx, cz = centro_x, centro_z
    y0, y1 = y_base, y_base + altura
    dados = []
    for i in range(lados):
        a0 = 2 * np.pi * i / lados
        a1 = 2 * np.pi * (i + 1) / lados
        c0, s0, c1, s1 = np.cos(a0), np.sin(a0), np.cos(a1), np.sin(a1)
        x0, z0 = cx + raio * c0, cz + raio * s0
        x1, z1 = cx + raio * c1, cz + raio * s1
        u0, u1 = i / lados, (i + 1) / lados
        # dois triângulos da lateral
        dados.extend([
            x0, y0, z0, u0, 0, c0, 0, s0,
            x1, y0, z1, u1, 0, c1, 0, s1,
            x1, y1, z1, u1, 1, c1, 0, s1,
            x0, y0, z0, u0, 0, c0, 0, s0,
            x1, y1, z1, u1, 1, c1, 0, s1,
            x0, y1, z0, u0, 1, c0, 0, s0,
        ])
        # topo (tampa)
        dados.extend([
            cx, y1, cz, 0.5, 0.5, 0, 1, 0,
            x0, y1, z0, 0, 0, 0, 1, 0,
            x1, y1, z1, 1, 0, 0, 1, 0,
        ])
        if tampa_baixo:
            dados.extend([
                cx, y0, cz, 0.5, 0.5, 0, -1, 0,
                x1, y0, z1, 1, 0, 0, -1, 0,
                x0, y0, z0, 0, 0, 0, -1, 0,
            ])
    return np.array(dados, dtype=np.float32).reshape(-1, 8)


def tronco_cone(cx, cz, y_base, altura, raio_baixo, raio_cima, lados=24):
    """Tronco de cone aberto (cúpula do abajur). Normais suaves inclinadas
    conforme a abertura do cone."""
    dados = []
    y0, y1 = y_base, y_base + altura
    inclinacao = (raio_baixo - raio_cima) / altura   # componente y da normal
    for i in range(lados):
        a0 = 2 * np.pi * i / lados
        a1 = 2 * np.pi * (i + 1) / lados
        pts = []
        for a, u in ((a0, i / lados), (a1, (i + 1) / lados)):
            c, s = np.cos(a), np.sin(a)
            n = np.array([c, inclinacao, s]); n /= np.linalg.norm(n)
            pts.append(((cx + raio_baixo * c, y0, cz + raio_baixo * s, u, 0, *n),
                        (cx + raio_cima * c, y1, cz + raio_cima * s, u, 1, *n)))
        (b0, t0), (b1, t1) = pts
        dados.extend([*b0, *b1, *t1, *b0, *t1, *t0])
    return np.array(dados, dtype=np.float32).reshape(-1, 8)


def esfera(cx, cy, cz, raio, fatias=20, aneis=12):
    """Esfera UV (lâmpadas, globo do lustre, lua). Normal = direção do
    centro até o ponto."""
    dados = []

    def ponto(i, j):
        teta = np.pi * j / aneis            # 0 (polo norte) .. pi (polo sul)
        fi = 2 * np.pi * i / fatias
        n = np.array([np.sin(teta) * np.cos(fi), np.cos(teta), np.sin(teta) * np.sin(fi)])
        return (cx + raio * n[0], cy + raio * n[1], cz + raio * n[2],
                i / fatias, 1 - j / aneis, *n)

    for j in range(aneis):
        for i in range(fatias):
            p00, p10 = ponto(i, j), ponto(i + 1, j)
            p01, p11 = ponto(i, j + 1), ponto(i + 1, j + 1)
            dados.extend([*p00, *p01, *p11, *p00, *p11, *p10])
    return np.array(dados, dtype=np.float32).reshape(-1, 8)


def caixa(x_min, x_max, y_min, y_max, z_min, z_max, metros_por_textura=0.5):
    """Paralelepípedo fechado (criado-mudo, tampo...). Seis quads."""
    m = metros_por_textura
    dx, dy, dz = (x_max - x_min) / m, (y_max - y_min) / m, (z_max - z_min) / m
    a, b = (x_min, z_min), (x_max, z_max)
    partes = [
        parede((x_min, z_max), (x_max, z_max), y_min, y_max, m),        # frente (+z)
        parede((x_max, z_min), (x_min, z_min), y_min, y_max, m),        # trás  (-z)
        parede((x_max, z_max), (x_max, z_min), y_min, y_max, m),        # +x
        parede((x_min, z_min), (x_min, z_max), y_min, y_max, m),        # -x
        plano(x_min, x_max, z_min, z_max, y_max, m),                    # tampo
        quad((x_min, y_min, z_min), (x_max, y_min, z_min),
             (x_max, y_min, z_max), (x_min, y_min, z_max), dx, dz),     # fundo
    ]
    return np.vstack(partes)


def superestrutura(x_min, x_max, z_min, z_max, y_base, altura, portas=True):
    """Bloco retangular sólido com janelas nas laterais (visão externa).
    Projeto 3: ganhou a face de baixo (1 cm acima do teto da cabine), para o
    "beiral" sobre o convés não ficar vazado quando visto de baixo."""
    partes = [plano(x_min, x_max, z_min, z_max, y_base + 0.01, 2.0)]
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