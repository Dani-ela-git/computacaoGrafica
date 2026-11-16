""" Nesse trabalho optamos por fazer o nosso parser para ficar mais fácil de corrigir algum 
problema com os arquivos .obj, caso seja necessário, facilitando a modularização do código. """

import numpy as np
import os

# layout de cada vértice: posição (3) + textura (2) + normal (3)
FLOATS_POR_VERTICE = 8

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
    """Lê o .obj e devolve (posicoes, textcoord, normais, faces, materiais).
    Cada face = (lista de (idx_v, idx_vt, idx_vn), nome_do_material)."""
    
    posicoes = []   # v x y z
    textcoord = []  # vt u v
    normais = []    # vn x y z   (Projeto 3: necessárias para a iluminação)
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

            # normais (nem todo .obj tem; quando falta, calculamos em montar())
            elif tipo == 'vn':
                normais.append([float(partes[1]), float(partes[2]), float(partes[3])])

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
                    idx_vn = (indice(indices[2], len(normais))
                              if len(indices) > 2 and indices[2] else None)
                    face.append((idx_v, idx_vt, idx_vn))
                faces.append((face, material))

            # materiais (para modelos com mais de uma textura)
            elif tipo in ('usemtl', 'usemat'):
                material = ' '.join(partes[1:])
            elif tipo == 'mtllib':
                materiais.update(ler_mtl(os.path.join(pasta, ' '.join(partes[1:]))))

    return posicoes, textcoord, normais, faces, materiais


def montar(posicoes, textcoord, normais, faces, normais_planas=False):
    """Triangula (leque) e monta o array intercalado [x, y, z, u, v, nx, ny, nz].

    Normais (Projeto 3):
      - se o .obj traz 'vn', usamos a normal do arquivo;
      - senão, calculamos uma normal SUAVE por vértice (média das normais das
        faces que usam aquele vértice, ponderada pela área). Em quinas vivas
        (ex.: tampa do piano) a média fica muito diferente da normal da face;
        nesses casos usamos a normal da própria face, para a quina não borrar;
      - normais_planas=True força a normal da face.
    """
    idx_pos, uvs, idx_nor = [], [], []
    for face in faces:
        if len(face) < 3:
            continue  # ignora faces inválidas
        v0 = face[0]
        for i in range(1, len(face) - 1):
            for (idx_v, idx_vt, idx_vn) in (v0, face[i], face[i + 1]):
                idx_pos.append(idx_v)
                if idx_vt is not None and 0 <= idx_vt < len(textcoord):
                    uvs.append(textcoord[idx_vt])
                else:
                    uvs.append((0.0, 0.0))  # caso não haja coordenadas de textura
                ok = idx_vn is not None and 0 <= idx_vn < len(normais)
                idx_nor.append(idx_vn if ok else -1)

    P_todas = np.asarray(posicoes, dtype=np.float64)
    idx_pos = np.asarray(idx_pos, dtype=np.int64)
    P = P_todas[idx_pos]                                  # (3*t, 3)

    # normal de cada triângulo (o tamanho do produto vetorial = 2 * área)
    tri = P.reshape(-1, 3, 3)
    n_face = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n_face_unit = n_face / np.maximum(np.linalg.norm(n_face, axis=1, keepdims=True), 1e-12)
    n_face_unit = np.repeat(n_face_unit, 3, axis=0)       # uma por vértice do triângulo

    if normais_planas:
        N = n_face_unit
    else:
        # média por posição (vértices que compartilham a mesma 'v' do .obj)
        acumulado = np.zeros_like(P_todas)
        np.add.at(acumulado, idx_pos, np.repeat(n_face, 3, axis=0))
        suave = acumulado[idx_pos]
        suave /= np.maximum(np.linalg.norm(suave, axis=1, keepdims=True), 1e-12)
        quina = np.einsum('ij,ij->i', suave, n_face_unit) < np.cos(np.radians(35.0))
        N = np.where(quina[:, None], n_face_unit, suave)

        # onde o arquivo tem 'vn', ela tem prioridade
        idx_nor = np.asarray(idx_nor, dtype=np.int64)
        tem_vn = idx_nor >= 0
        if tem_vn.any():
            N[tem_vn] = np.asarray(normais, dtype=np.float64)[idx_nor[tem_vn]]
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    dados = np.hstack([P, np.asarray(uvs, dtype=np.float64).reshape(-1, 2), N])
    vertices = np.ascontiguousarray(dados, dtype=np.float32).ravel()
    # Como o array já está "achatado", os índices são 0, 1, 2, ...
    indices = np.arange(len(vertices) // FLOATS_POR_VERTICE, dtype=np.uint32)
    return vertices, indices

def carregar_obj(caminho_arquivo, normais_planas=False):
    """
    Carrega um arquivo .obj (Wavefront) e retorna:
        vertices: np.array float32 com layout [x, y, z, u, v, nx, ny, nz] (intercalado)
        indices:  np.array uint32 com os índices dos triângulos
    Trata automaticamente:
        - Faces triangulares (f v/vt/vn)
        - Faces quads/polígonos (triangulação em leque)
        - .obj sem coordenadas de textura (usa u=v=0)
    """
    posicoes, textcoord, normais, faces, _ = ler_arquivo(caminho_arquivo)
    return montar(posicoes, textcoord, normais, [f for f, _ in faces], normais_planas)

def carregar_obj_por_material(caminho_arquivo, normais_planas=False):
    """Igual ao carregar_obj, mas separa por material do .mtl.
    Retorna lista de (vertices, indices, caminho_textura_ou_None)."""
    
    posicoes, textcoord, normais, faces, materiais = ler_arquivo(caminho_arquivo)
    grupos = {}
    for face, material in faces:
        grupos.setdefault(material, []).append(face)
    resultado = []
    for mat, lista in grupos.items():
        vertices, indices = montar(posicoes, textcoord, normais, lista, normais_planas)
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
    Altera os arrays no lugar. lista_vertices = arrays [x,y,z,u,v,nx,ny,nz] achatados.
    As normais só giram (a escala é uniforme, então não mudam de direção)."""
    
    giro = _rotacao(*giro_base)
    blocos = [v.reshape(-1, FLOATS_POR_VERTICE) for v in lista_vertices]
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
        b[:, 5:8] = b[:, 5:8] @ giro.T