"""
Gera o modelo da lua usado no Projeto 3 

assets/models/lua.obj   esfera UV de raio 1 com v, vt, vn e faces v/vt/vn

O .obj segue o mesmo formato dos modelos da aula (ex.: objetos/luz/luz.obj)
e é lido pelo nosso parser (obj_loader.py) como qualquer outro modelo.
"""
import os
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))


def gerar_obj(caminho, fatias=48, aneis=24):
    linhas = ["# lua: esfera UV de raio 1 (gerada por gerar_lua.py)", "o lua"]
    # vértices, coordenadas de textura e normais (na esfera de raio 1, normal = posição)
    for j in range(aneis + 1):
        teta = np.pi * j / aneis                    # 0 = polo norte, pi = polo sul
        for i in range(fatias + 1):
            u = i / fatias
            fi = 2 * np.pi * u                      # longitude
            x = -np.sin(teta) * np.sin(fi)          # u = 0.5 -> (0, 0, +1)
            y = np.cos(teta)
            z = -np.sin(teta) * np.cos(fi)
            linhas.append(f"v {x:.6f} {y:.6f} {z:.6f}")
            linhas.append(f"vt {u:.6f} {1 - j / aneis:.6f}")
            linhas.append(f"vn {x:.6f} {y:.6f} {z:.6f}")
    # faces (cada quadrilátero vira 2 triângulos)
    idx = lambda i, j: j * (fatias + 1) + i + 1     # .obj começa em 1
    for j in range(aneis):
        for i in range(fatias):
            a, b, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
            for tri in ((a, d, c), (a, c, b)):
                linhas.append("f " + " ".join(f"{k}/{k}/{k}" for k in tri))
    with open(caminho, "w") as f:
        f.write("\n".join(linhas) + "\n")


if __name__ == "__main__":
    gerar_obj(os.path.join(BASE, "assets", "models", "lua.obj"))
    print("lua.obj gerado.")
