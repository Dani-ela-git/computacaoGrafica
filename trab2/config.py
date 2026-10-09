""" Medidas da cena, em metros, para os modelos ficarem coerentes com o mundo
real """

import os

BASE = os.path.dirname(os.path.abspath(__file__))


def caminho(*partes):
    return os.path.join(BASE, *partes)


# ---------------------------------------------------------------- janela
LARGURA_JANELA = 1280
ALTURA_JANELA = 720
TITULO = "Titanic - Computacao Grafica (SCC0250) - Projeto 2"

# ---------------------------------------------------------------- navio
CONVES = dict(x_min=-25.0, x_max=25.0, z_min=-12.0, z_max=12.0)   # piso EXTERNO (y = 0)
ALTURA_AMURADA = 1.0
NIVEL_OCEANO = -8.0
TAMANHO_OCEANO = 300.0

# Cabine de primeira classe (ambiente INTERNO), com porta na parede x = x_max
CABINE = dict(x_min=-19.0, x_max=-9.0, z_min=-5.0, z_max=5.0, altura=3.2,
              porta_largura=1.6, porta_altura=2.3)

# ---------------------------------------------------------------- câmera
POSICAO_INICIAL = (4.0, 1.7, 8.0)
ALTURA_OLHOS_MIN = 0.4        # a câmera nunca atravessa o piso
ALTURA_MAX = 60.0             # nem sobe além do céu
VELOCIDADE = 6.0              # m/s (Shift corre x3)
SENSIBILIDADE_MOUSE = 0.1
FOV = 60.0
PLANO_PERTO, PLANO_LONGE = 0.1, 1000.0

# ---------------------------------------------------------------- texturas
# Pisos diferentes: madeira no convés (externo) e carpete na cabine (interno)
TEXTURAS = dict(
    conves=caminho("assets", "textures", "conves.png"),
    carpete=caminho("assets", "textures", "carpete.png"),
    oceano=caminho("assets", "textures", "oceano.png"),
    parede=caminho("assets", "textures", "parede.png"),
    teto=caminho("assets", "textures", "teto.png"),
    casco=caminho("assets", "textures", "casco.png"),
)
SKYBOX = [caminho("assets", "skybox", f"{n}.png")
          for n in ("right", "left", "top", "bottom", "front", "back")]

# ---------------------------------------------------------------- modelos
#   obj / textura -> arquivos (textura=None usa as imagens do .mtl)
#   altura ou comprimento -> tamanho real em metros
#   giro_base     -> corrige modelos deitados, ex.: (-90, 0, 0)
#   instancias    -> lista de (x, y, z, rotação_y). Repetições do mesmo modelo.
def models(nome):
    return caminho("assets", "models", f"{nome}.obj")


def textures(nome):
    return caminho("assets", "textures", f"{nome}.png")


MODELOS = {
    # ---------- ambiente INTERNO (cabine) ----------
    "vaso": dict(obj=models("ceramicvase"), textura=caminho("assets", "textures", "ceramivaseTexture.jpg"),
                 altura=0.6, instancias=[(-9.6, 0.0, 4.4, 0.0)]),        # modelo do grupo

    "cama": dict(obj=models("cama"), textura=textures("cama"), comprimento=2.2,
                 instancias=[(-17.85, 0.0, -2.8, 90.0)]),
   
    # Teclas no +z do modelo -> giro de 90° as vira para dentro da cabine
    "piano": dict(obj=models("piano"), textura=textures("piano"), altura=1.3,
                  instancias=[(-18.3, 0.0, 2.8, 90.0)]),
    
    "mala": dict(obj=models("mala"), textura=textures("mala"), comprimento=0.6,
                 instancias=[(-13.0, 0.0, -4.2, 15.0)]),
    
    "poltrona": dict(obj=caminho("assets", "models", "poltrona", "DB_IndoorFurniture_105.obj"),
                     textura=None, altura=1.0,
                     instancias=[(-12.0, 0.0, 2.6, -90.0)]),             # virada para o piano

    # ---------- ambiente EXTERNO (convés / oceano) ----------
    "bote": dict(obj=models("bote"), textura=textures("bote"), comprimento=8.5,
                 instancias=[(8.0, 0.0, -5.5, 0.0)]),
    
    "espreguicadeira": dict(obj=models("espreguicadeira"), textura=textures("espreguicadeira"), altura=1.0,
                            instancias=[(0.0, 0.0, 9.5, 0.0), (2.2, 0.0, 9.5, 0.0),
                                        (4.4, 0.0, 9.5, 0.0), (6.6, 0.0, 9.5, 0.0)]),
   
    "boia": dict(obj=models("boia"), textura=None, comprimento=0.76,
                 instancias=[(-4.0, 0.0, 11.0, 0.0)]),
    
    "iceberg": dict(obj=models("iceberg"), textura=textures("iceberg"), altura=20.0,
                    instancias=[(20.0, NIVEL_OCEANO, -90.0, 0.0)]),
}

# ---------------------------------------------------------------- teclado
#   Translação -> iceberg (I/K/J/L) | Rotação -> bote (R/T) | Escala -> boia (Z/X)
MODELO_TRANSLACAO = "iceberg"
MODELO_ROTACAO = "bote"
MODELO_ESCALA = "boia"
VEL_TRANSLACAO = 12.0         # m/s
VEL_ROTACAO = 60.0            # graus/s
VEL_ESCALA = 0.8              # fator/s
LIMITES_ICEBERG = dict(x_min=-120.0, x_max=120.0, z_min=-140.0, z_max=-45.0)
LIMITES_ESCALA = (0.5, 2.5)