""" Nesse trabalho optamos por fazer o nosso parser para ficar mais fácil de corrigir algum 
problema com os arquivos .obj, caso seja necessário, facilitando a modularização do código. """

import numpy as np

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
    posicoes = [] # v x y z
    textcoord = [] # vt u v
    faces = []  # cada face = lista de (idx_v, idx_vt)

    with open(caminho_arquivo, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue

            partes = linha.split()
            tipo = partes[0]


            #vertices de posicao
            if tipo == 'v':
                posicoes.append(
                    [float(partes[1]),
                     float(partes[2]),
                     float(partes[3])]
                )

            #vertices de textura
            elif tipo == 'vt':
                #.obj guarda as coordenadas de textura como u,v, mas o OpenGL espera v invertido por convençao
                u = float(partes[1])
                v = float(partes[2]) if len(partes) > 2 else 0.0
                textcoord.append([u, 1.0 - v])

            #faces
            elif tipo == 'f':
                face = []
                for vertice in partes[1:]:
                    # cada vertice da face pode ter a forma:
                    # v, v/vt, v//vn, v/vt/vn
                    indices = vertice.split('/')
                    idx_v = int(indices[0]) - 1  # .obj é 1-indexed
                    idx_vt = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else None
                    face.append((idx_v, idx_vt))
                faces.append(face)

        #trinagulação (leque) de faces com mais de 3 vértices
        indice = []
        for face in faces:
            if len(face) < 3:
                continue  # ignora faces inválidas
            v0 = face[0]
            for i in range(1, len(face) - 1):
                v1 = face[i]
                v2 = face[i + 1]
                for (idx_v, idx_vt) in (v0, v1, v2):
                    # Cada vértice vira uma entrada intercalada [pos, uv]
                    # Índice final = posição na lista intercalada
                    indice.append((idx_v, idx_vt))

        # Cria o array intercalado de vertices
        # Layout: [x, y, z, u, v]  →  5 floats por vértice
        dados = []
        for(idx_v, idx_vt) in indice:
            x, y,z = posicoes[idx_v]
            if idx_vt >= 0 and idx_vt < len(textcoord):
                u, v = textcoord[idx_vt]
            else:
                u, v = 0.0, 0.0  # caso não haja coordenadas de textura
            dados.extend([x, y, z, u, v])

        vertices = np.array(dados, dtype=np.float32)

        # Como montamos o array já "achatado" (cada entrada = 1 vértice),
        # os índices do glDrawElements são simplesmente 0, 1, 2, 3, ...
        indices_simples = np.arange(len(vertices), dtype=np.uint32)
    
        return vertices, indices_simples