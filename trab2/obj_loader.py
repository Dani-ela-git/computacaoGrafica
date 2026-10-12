""" Nesse trabalho optamos por fazer o nosso parser para ficar mais fácil de corrigir algum 
problema com os arquivos .obj, caso seja necessário, facilitando a modularização do código. """

import numpy as np
import os

def achar_arquivo(pasta, nome):
    """Acha a imagem citada no .mtl mesmo com caminho quebrado"""

    nome = nome.strip().strip('"').replace("\\", "/")
    for c in (os.path.join(pasta, nome), os.path.join(pasta, os.path.basename(nome))):
        if os.path.isfile(c):
            return c
    alvo = os.path.basename(nome).lower()
    for raiz, _, arquivos in os.walk(pasta):
        for a in arquivos:
            if a.lower() == alvo:
                return os.path.join(raiz, a)
    return None

def ler_mtl(caminho_mtl):
    """Retorna {nome_material: caminho_da_textura ou None} lendo as linhas map_Kd."""

    materiais, atual = {}, None

    if not os.path.isfile(caminho_mtl):
        print(f"  [aviso] .mtl não encontrado: {caminho_mtl}")
        return materiais
    pasta = os.path.dirname(caminho_mtl)
    with open(caminho_mtl, 'r', encoding='utf-8', errors='ignore') as f:
        for linha in f:
            partes = linha.split()
            if not partes:
                continue
            if partes[0] == 'newmtl':
                atual = ' '.join(partes[1:])
                materiais[atual] = None
            elif partes[0].lower() == 'map_kd' and atual is not None:
                # o nome do arquivo é sempre o último item (pode haver opções antes)
                materiais[atual] = achar_arquivo(pasta, partes[-1])
    return materiais


def indice(texto, total):
    """.obj é 1-indexed; índices negativos contam a partir do fim da lista."""
    i = int(texto)
    return i - 1 if i > 0 else total + i


def ler_arquivo(caminho_arquivo):
    """Lê o .obj e devolve (posicoes, textcoord, faces, materiais).
    Cada face = (lista de (idx_v, idx_vt), nome_do_material)."""
    
    posicoes = []   # v x y z
    textcoord = []  # vt u v
    faces = []
    materiais = {}
    material = None
    pasta = os.path.dirname(caminho_arquivo)

    with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue

            partes = linha.split()
            tipo = partes[0]

            # vertices de posicao
            if tipo == 'v':
                posicoes.append([float(partes[1]), float(partes[2]), float(partes[3])])

            # vertices de textura
            elif tipo == 'vt':
                # O "v" do .obj ja segue a convencao do OpenGL (v = 0 embaixo).
                # Quem acerta a orientacao é o texture_loader, que inverte a IMAGEM.
                # (Inverter aqui tambem deixava a textura de cabeca para baixo.)
                u = float(partes[1])
                v = float(partes[2]) if len(partes) > 2 else 0.0
                textcoord.append([u, v])

            # faces
            elif tipo == 'f':
                face = []
                for vertice in partes[1:]:
                    # cada vertice da face pode ter a forma: v, v/vt, v//vn, v/vt/vn
                    indices = vertice.split('/')
                    idx_v = indice(indices[0], len(posicoes))
                    idx_vt = (indice(indices[1], len(textcoord))
                              if len(indices) > 1 and indices[1] else None)
                    face.append((idx_v, idx_vt))
                faces.append((face, material))

            # materiais (para modelos com mais de uma textura)
            elif tipo in ('usemtl', 'usemat'):
                material = ' '.join(partes[1:])
            elif tipo == 'mtllib':
                materiais.update(ler_mtl(os.path.join(pasta, ' '.join(partes[1:]))))

    return posicoes, textcoord, faces, materiais


def montar(posicoes, textcoord, faces):
    """Triangula (leque) e monta o array intercalado [x, y, z, u, v]."""
    
    dados = []
    for face in faces:
        if len(face) < 3:
            continue  # ignora faces inválidas
        v0 = face[0]
        for i in range(1, len(face) - 1):
            for (idx_v, idx_vt) in (v0, face[i], face[i + 1]):
                x, y, z = posicoes[idx_v]
                if idx_vt is not None and 0 <= idx_vt < len(textcoord):
                    u, v = textcoord[idx_vt]
                else:
                    u, v = 0.0, 0.0  # caso não haja coordenadas de textura
                dados.extend([x, y, z, u, v])

    vertices = np.array(dados, dtype=np.float32)
    # Cada vértice ocupa 5 floats, então há len(vertices) // 5 vértices.
    # Como o array já está "achatado", os índices são 0, 1, 2, ...
    indices = np.arange(len(vertices) // 5, dtype=np.uint32)
    return vertices, indices

def carregar_obj(caminho_arquivo):
    """
    Carrega um arquivo .obj (Wavefront) e retorna:
        vertices: np.array float32 com layout [x, y, z, u, v] (intercalado)
        indices:  np.array uint32 com os índices dos triângulos
    Trata automaticamente:
        - Faces triangulares (f v/vt/vn)
        - Faces quads/polígonos (triangulação em leque)
        - .obj sem coordenadas de textura (usa u=v=0)
    """
    posicoes, textcoord, faces, _ = ler_arquivo(caminho_arquivo)
    return montar(posicoes, textcoord, [f for f, _ in faces])

def carregar_obj_por_material(caminho_arquivo):
    """Igual ao carregar_obj, mas separa por material do .mtl.
    Retorna lista de (vertices, indices, caminho_textura_ou_None)."""
    
    posicoes, textcoord, faces, materiais = ler_arquivo(caminho_arquivo)
    grupos = {}
    for face, material in faces:
        grupos.setdefault(material, []).append(face)
    resultado = []
    for mat, lista in grupos.items():
        vertices, indices = montar(posicoes, textcoord, lista)
        resultado.append((vertices, indices, materiais.get(mat)))
    return resultado
    
#### função de rotação 
def _rotacao(graus_x, graus_y, graus_z):
    ax, ay, az = np.radians([graus_x, graus_y, graus_z])
    rx = np.array([[1, 0, 0], [0, np.cos(ax), -np.sin(ax)], [0, np.sin(ax), np.cos(ax)]])
    ry = np.array([[np.cos(ay), 0, np.sin(ay)], [0, 1, 0], [-np.sin(ay), 0, np.cos(ay)]])
    rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    return rz @ ry @ rx

###função que normaliza o modelo para o tamanho real
def normalizar(lista_vertices, altura=None, comprimento=None, giro_base=(0, 0, 0)):
    """ Essa função faz três coisas:
      1) corrige a orientação (giro_base, ex.: (-90, 0, 0) para modelos Z-up);
      2) coloca a origem no centro da BASE do modelo (não flutua nem afunda,
         mesmo quando é escalado pelo teclado);
      3) redimensiona para a altura OU o comprimento horizontal desejado.
    Altera os arrays no lugar. lista_vertices = arrays [x,y,z,u,v] achatados."""
    
    giro = _rotacao(*giro_base)
    blocos = [v.reshape(-1, 5) for v in lista_vertices]
    todos = np.vstack([b[:, :3] for b in blocos]) @ giro.T
    minimo, maximo = todos.min(axis=0), todos.max(axis=0)
    tamanho = maximo - minimo

    if altura is not None:
        fator = altura / max(tamanho[1], 1e-6)
    elif comprimento is not None:
        fator = comprimento / max(tamanho[0], tamanho[2], 1e-6)
    else:
        fator = 1.0

    base = np.array([(minimo[0] + maximo[0]) / 2, minimo[1], (minimo[2] + maximo[2]) / 2])
    for b in blocos:
        b[:, :3] = ((b[:, :3] @ giro.T) - base) * fator