""" Medidas da cena, em metros """

import os

BASE = os.path.dirname(os.path.abspath(__file__))

def caminho(*partes):
    return os.path.join(BASE, *partes)

# janela
LARGURA_JANELA = 1280
ALTURA_JANELA = 720
TITULO = "Titanic - Computacao Grafica (SCC0250) - Projeto 2"

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
                 altura=0.6, instancias=[(-9.6, 0.0, 4.4, 0.0)]),
    "cama": dict(obj=models("cama"), textura=textures("cama"), comprimento=2.2,
                 instancias=[(-17.85, 0.0, -2.8, 90.0)]),
    "piano": dict(obj=models("piano"), textura=textures("piano"), altura=1.3,
                  instancias=[(-18.3, 0.0, 2.8, 90.0)]),
    "mala": dict(obj=models("mala"), textura=textures("mala"), comprimento=0.6,
                 instancias=[(-13.0, 0.0, -4.2, 15.0)]),
    "poltrona": dict(obj=caminho("assets", "models", "poltrona", "DB_IndoorFurniture_105.obj"),
                     textura=None, altura=1.0,
                     instancias=[(-12.0, 0.0, 2.6, -90.0)]),

    # ---------- ambiente externo (convés / oceano) ----------
    "bote": dict(obj=models("bote"), textura=textures("bote"), comprimento=8.5, #4 botes na hora do naufrágio
             instancias=[
                 (35.0, NIVEL_OCEANO + 0.2, -15.0, 20.0),
                 (35.0, NIVEL_OCEANO + 0.2,  -5.0, 15.0),
                 (35.0, NIVEL_OCEANO + 0.2,   5.0, 10.0),
                 (35.0, NIVEL_OCEANO + 0.2,  15.0,  5.0),
             ]),
    "espreguicadeira": dict(obj=models("espreguicadeira"), textura=textures("espreguicadeira"), altura=1.0,
                            instancias=[(0.0, 0.0, 9.5, 0.0), (2.5, 0.0, 9.5, 0.0),
                                        (5.0, 0.0, 9.5, 0.0), (7.5, 0.0, 9.5, 0.0)]),
    "boia": dict(obj=models("boia"), textura=textures("boia_lifebuoyshader"), comprimento=0.76,
             instancias=[(30.0, NIVEL_OCEANO + 0.1, -8.0, 0.0)]),
    "iceberg": dict(obj=models("iceberg"), textura=textures("iceberg"), altura=80.0, 
                    instancias=[(20.0, NIVEL_OCEANO, -60.0, 0.0)]),  
}

# teclado
MODELO_TRANSLACAO = "iceberg"
MODELO_ROTACAO = "bote"
MODELO_ESCALA = "boia"
VEL_TRANSLACAO = 12.0
VEL_ROTACAO = 60.0
VEL_ESCALA = 0.8
LIMITES_ICEBERG = dict(x_min=-120.0, x_max=120.0, z_min=-140.0, z_max=-45.0)
LIMITES_ESCALA = (0.5, 2.5)