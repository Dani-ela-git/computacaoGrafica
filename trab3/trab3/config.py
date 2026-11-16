""" Medidas da cena, em metros """

import os

BASE = os.path.dirname(os.path.abspath(__file__))

def caminho(*partes):
    return os.path.join(BASE, *partes)

# janela
LARGURA_JANELA = 1280
ALTURA_JANELA = 720
TITULO = "Titanic - Computacao Grafica (SCC0250) - Projeto 3"

# navio
CONVES = dict(x_min=-25.0, x_max=25.0, z_min=-12.0, z_max=12.0)
ALTURA_AMURADA = 1.2
NIVEL_OCEANO = -8.0
TAMANHO_OCEANO = 2000.0    

# cabine INTERNA
CABINE = dict(x_min=-19.0, x_max=-9.0, z_min=-5.0, z_max=5.0, altura=3.2,
              porta_largura=1.6, porta_altura=2.3)

# superestrutura EXTERNA (bloco em volta da cabine, com chaminés em cima)
SUPERESTRUTURA = dict(x_min=-22.0, x_max=-6.0, z_min=-7.0, z_max=7.0,
                      y_base=3.2, altura=4.0)

# chaminés (4, em fileira sobre a superestrutura)
CHAMINES = dict(
    y_base=3.2 + 4.0,          # em cima da superestrutura
    altura=6.0,
    raio=1.1,
    posicoes_x=[-19.0, -15.0, -11.0, -7.0],
    z=0.0,
)

# câmera
POSICAO_INICIAL = (-14.0, 1.7, 0.0)   # dentro da cabine, olhando pro centro
ALTURA_OLHOS_MIN = 0.4
ALTURA_MAX = 60.0
VELOCIDADE = 6.0
SENSIBILIDADE_MOUSE = 0.1
FOV = 60.0
PLANO_PERTO, PLANO_LONGE = 0.1, 2000.0

# texturas
TEXTURAS = dict(
    conves=caminho("assets", "textures", "conves.png"),
    carpete=caminho("assets", "textures", "carpete.png"),
    oceano=caminho("assets", "textures", "oceano.png"),
    parede=caminho("assets", "textures", "parede.png"),
    teto=caminho("assets", "textures", "teto.png"),
    casco=caminho("assets", "textures", "casco.png"),
    superestrutura=caminho("assets", "textures", "parede.png"),  # reaproveitei
    chamines=caminho("assets", "textures", "casco.png"),         # reaproveitei
)
SKYBOX = [caminho("assets", "skybox", f"{n}.png")
          for n in ("right", "left", "top", "bottom", "front", "back")]

def models(nome):
    return caminho("assets", "models", f"{nome}.obj")

def textures(nome):
    return caminho("assets", "textures", f"{nome}.png")

MODELOS = {
    # ---------- ambiente interno (cabine) ----------
    "vaso": dict(obj=models("ceramicvase"), textura=caminho("assets", "textures", "ceramivaseTexture.jpg"),
                 altura=0.6, interno=True, instancias=[(-9.6, 0.0, 4.4, 0.0)]),
    "cama": dict(obj=models("cama"), textura=textures("cama"), comprimento=2.2, interno=True,
                 instancias=[(-17.85, 0.0, -2.8, 90.0)]),
    "piano": dict(obj=models("piano"), textura=textures("piano"), altura=1.3, interno=True,
                  instancias=[(-18.3, 0.0, 2.8, 90.0)]),
    "mala": dict(obj=models("mala"), textura=textures("mala"), comprimento=0.6, interno=True,
                 instancias=[(-13.0, 0.0, -4.2, 15.0)]),
    "poltrona": dict(obj=caminho("assets", "models", "poltrona", "DB_IndoorFurniture_105.obj"),
                     textura=None, altura=1.0, interno=True,
                     instancias=[(-12.0, 0.0, 2.6, -90.0)]),

    # ---------- ambiente externo (convés / oceano) ----------
    "bote": dict(obj=models("bote"), textura=textures("bote"), comprimento=8.5, interno=False, #4 botes na hora do naufrágio
             instancias=[
                 (35.0, NIVEL_OCEANO + 0.2, -15.0, 20.0),
                 (35.0, NIVEL_OCEANO + 0.2,  -5.0, 15.0),
                 (35.0, NIVEL_OCEANO + 0.2,   5.0, 10.0),
                 (35.0, NIVEL_OCEANO + 0.2,  15.0,  5.0),
             ]),
    "espreguicadeira": dict(obj=models("espreguicadeira"), textura=textures("espreguicadeira"), altura=1.0,
                            interno=False,
                            instancias=[(0.0, 0.0, 9.5, 0.0), (2.5, 0.0, 9.5, 0.0),
                                        (5.0, 0.0, 9.5, 0.0), (7.5, 0.0, 9.5, 0.0)]),
    "boia": dict(obj=models("boia"), textura=textures("boia_lifebuoyshader"), comprimento=0.76,
             interno=False, instancias=[(30.0, NIVEL_OCEANO + 0.1, -8.0, 0.0)]),
    "iceberg": dict(obj=models("iceberg"), textura=textures("iceberg"), altura=80.0, interno=False,
                    normais_planas=True,     # gelo facetado (visual low-poly)
                    instancias=[(20.0, NIVEL_OCEANO, -60.0, 0.0)]),
}


# =====================================================================
#  PROJETO 3 - ILUMINAÇÃO
# =====================================================================

# ---------------------------------------------------------- materiais
# Cada objeto tem os SEUS parâmetros de iluminação (como ka, kd, ks e ns
# definidos dentro de desenha_caixa() / desenha_chaleira() nos códigos da aula):
#   ka = reflexão ambiente, kd = reflexão difusa, ks = reflexão especular,
#   ns = expoente especular (maior = brilho menor e mais concentrado)
#   cor = cor base (multiplica a textura; usada nas peças sem textura)
def material(ka, kd, ks, ns, cor=(1.0, 1.0, 1.0)):
    return dict(ka=ka, kd=kd, ks=ks, ns=ns, cor=cor)

MATERIAIS = {
    # ---- ambiente externo
    "oceano":          material(0.6, 0.70, 0.90, 96.0),    # água: brilho forte e concentrado
    "conves":          material(0.9, 0.85, 0.25, 16.0),    # madeira envernizada
    "casco":           material(0.8, 0.75, 0.50, 32.0),    # aço pintado
    "superestrutura":  material(0.9, 0.80, 0.15, 8.0),
    "parede_externa":  material(0.9, 0.80, 0.15, 8.0),     # lado de fora da cabine
    "chamines":        material(0.8, 0.75, 0.60, 48.0),
    "bote":            material(0.9, 0.85, 0.20, 12.0),    # madeira
    "espreguicadeira": material(0.9, 0.85, 0.15, 8.0),
    "boia":            material(0.9, 0.80, 0.35, 24.0),    # lona/borracha
    "iceberg":         material(1.0, 0.90, 0.70, 40.0),    # gelo
    "lua":             material(1.0, 0.10, 0.00, 1.0),   # brilha por emissão (textura lua.jpg)
    # ---- ambiente interno (cabine)
    "carpete":         material(1.0, 0.90, 0.03, 2.0),     # tecido: quase sem brilho
    "parede":          material(1.0, 0.85, 0.12, 8.0),
    "teto":            material(1.0, 0.90, 0.05, 4.0),
    "vaso":            material(0.8, 0.80, 0.80, 96.0),    # cerâmica vitrificada
    "cama":            material(1.0, 0.90, 0.05, 4.0),     # tecido
    "piano":           material(0.7, 0.75, 0.90, 80.0),    # laca polida
    "mala":            material(0.9, 0.85, 0.35, 16.0),    # couro
    "poltrona":        material(1.0, 0.90, 0.12, 8.0),
    "criado_mudo":     material(0.8, 0.85, 0.45, 32.0, (0.45, 0.26, 0.14)),   # madeira escura
    "latao":           material(0.6, 0.60, 0.90, 64.0, (0.85, 0.65, 0.30)),   # metal dourado
    "cupula":          material(1.0, 0.90, 0.05, 2.0, (0.95, 0.85, 0.65)),    # tecido da cúpula
    "globo_lustre":    material(0.8, 0.40, 1.00, 128.0, (0.95, 0.95, 1.0)),   # vidro
    "lampada_abajur":  material(0.8, 0.40, 1.00, 128.0, (1.0, 0.9, 0.7)),
}

# ---------------------------------------------------------- luz ambiente
# Uma só, vale para os dois ambientes. Noite de lua: levemente azulada.
COR_AMBIENTE = (0.75, 0.80, 1.00)
AMBIENTE_INICIAL = 0.20     # Ia
AMBIENTE_LIMITES = (0.0, 1.0)
AMBIENTE_PASSO = 0.05

# fatores globais de reflexão difusa e especular (multiplicam kd e ks)
FATOR_LIMITES = (0.0, 3.0)
FATOR_PASSO = 0.1

# ---------------------------------------------------------- fontes pontuais
# atenuação = 1 / (constante + linear*d + quadratica*d^2)
LUZES = {
    # EXTERNA: a lua (muito longe, então praticamente sem atenuação)
    "lua":      dict(cor=(0.70, 0.78, 0.95), atenuacao=(1.0, 0.0, 0.0), interna=False),
    # INTERNAS, de cores diferentes
    "lustre":   dict(cor=(0.85, 0.92, 1.05), atenuacao=(1.0, 0.07, 0.017), interna=True,
                     posicao=(-14.0, 2.62, 0.0)),            # luz elétrica, branco-azulada
    "abajur":   dict(cor=(1.00, 0.55, 0.20), atenuacao=(1.0, 0.22, 0.20), interna=True,
                     posicao=(-18.70, 0.97, -1.35)),         # lâmpada sob cúpula, âmbar
}

# peças das luminárias da cabine (geradas por código, em metros)
CRIADO_MUDO = dict(x=-18.70, z=-1.35, largura=0.50, profundidade=0.50, altura=0.60)
LUSTRE = dict(x=-14.0, z=0.0, raio_globo=0.16)

# ---------------------------------------------------------- lua
# Objeto EXTERNO com TRANSLAÇÃO: a lua anda num arco pelo céu, indo de um
# lado ao outro e voltando (nunca desce abaixo do horizonte).
#   ângulo(t) = 90° + amplitude * sen(velocidade * t)
#   posição   = (raio*cos(ângulo), y_centro + raio*sen(ângulo), z)
LUA = dict(
    obj=models("lua"),      # esfera UV (assets/models/lua.obj, gerada por gerar_lua.py)
    textura=caminho("assets", "textures", "lua.jpg"),   # mapa da NASA (CGI Moon Kit)
    raio_orbita=350.0,      # metros
    y_centro=-50.0,         # centro do arco (abaixo do mar, para o arco ficar "achatado")
    z=-200.0,               # a lua fica do lado do iceberg
    amplitude=60.0,         # graus para cada lado do ponto mais alto
    velocidade=0.10,        # rad/s (ida e volta em ~1 min)
    raio=14.0,              # o .obj tem raio 1; a escala da model deixa com 14 m
    brilho=(1.00, 0.90, 0.74),   # emissão = cor da luz * brilho (por canal: lua sem tom azul)
)

# ---------------------------------------------------------- teclado
# (as teclas de transformação do Projeto 2 foram retiradas, como permite o enunciado)
TECLA_INFO = """
  1 ............ liga/desliga luz AMBIENTE
  2 ............ liga/desliga LUA (externa)
  3 ............ liga/desliga LUSTRE do teto (interna, branco-azulada)
  4 ............ liga/desliga ABAJUR (interna, âmbar)
  Z / X ........ diminui / aumenta luz ambiente
  C / V ........ diminui / aumenta reflexão difusa
  B / N ........ diminui / aumenta reflexão especular
  M ............ pausa / continua o movimento da lua
  P ............ mostrar/ocultar malha poligonal
"""