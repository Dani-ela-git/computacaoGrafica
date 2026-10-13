# Titanic, 14 de abril de 1912 — Projeto 2 (SCC0250)

Cena 3D em OpenGL moderno (Python + GLFW + PyOpenGL + PyGLM). O usuário começa
na cabine e consegue andar pela cena.

## Como rodar

```bash
pip install glfw PyOpenGL PyGLM numpy Pillow
python main.py
```

Os modelos, texturas e o céu ficam em `assets/` (pacote `modelos_titanic_parte1.zip` +
`modelos_titanic_parte2.zip`). Os autores e licenças estão em `CREDITOS.txt`.

`gerar_provisorios.py` cria arquivos de teste só para o que estiver faltando em `assets/`
(ele nunca sobrescreve um arquivo que já existe).

## Controles

| Tecla | Ação |
|---|---|
| Mouse / setas | olhar |
| Roda do mouse | zoom |
| W A S D | andar |
| Espaço / Ctrl | subir / descer |
| Shift | correr |
| I K J L | **translação** do iceberg |
| R T | **rotação** do bote salva-vidas |
| Z X | **escala** da boia |
| P | mostrar/ocultar malha |
| Esc | sair |

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `main.py` | janela, shaders, teclado/mouse e laço principal |
| `config.py` | medidas (metros), caminhos, modelos e teclas |
| `cena.py` | monta a cena com `Mesh`, transformações do teclado e desenho |
| `mesh.py` | classe `Mesh` (VAO/VBO/EBO, textura, matriz model) |
| `obj_loader.py` | parser .obj/.mtl próprio + ajuste para tamanho real |
| `texture_loader.py` | texturas 2D e cubemap da skybox |
| `shaders.py` | GLSL dos objetos e da skybox (sem iluminação) |
| `camera.py` | câmera em 1ª pessoa com glm e limites do cenário |
| `geometria.py` | pisos, oceano, paredes da cabine e casco |
| `teste_mesh.py` | teste de um modelo isolado (vaso de cerâmica) |
| `gerar_provisorios.py` | gera arquivos de teste |
| `assets/models`, `assets/textures`, `assets/skybox` | arquivos da cena |

## Adicionando um modelo

Em `config.py`, dentro de `MODELOS`:

```python
"piano": dict(obj=_m("piano"), textura=_t("piano"), altura=1.3,
              instancias=[(-18.3, 0.0, 2.8, 90.0)]),
```

- `altura` **ou** `comprimento`: tamanho real em metros. O modelo é
  redimensionado sozinho e fica com a base no chão.
- `instancias`: `(x, y, z, rotação_y)`. Várias entradas = várias cópias.
- `textura=None`: usa as imagens listadas no `.mtl` (modelos com várias texturas).
- Modelo deitado? `giro_base=(-90, 0, 0)`.
- Textura xadrez magenta = imagem não encontrada (o console mostra o caminho).

## Como cada requisito é atendido

1. **Interno e externo:** cabine (interno) e convés + oceano (externo).
2. **Seis ou mais modelos com textura:** 9 modelos (vaso, cama, piano, mala, poltrona, bote, espreguiçadeira, boia, iceberg).
3. **3 internos e 3 externos:** 5 na cabine e 4 fora. A cabine e o casco são gerados por código e não contam.
4. **Um objeto por .obj.**
5. **Coerência com o mundo real:** `obj_loader.normalizar` usa medidas reais em metros.
6. **Pisos diferentes:** carpete (interno) e madeira (externo).
7. **Transformações independentes:** translação no iceberg, rotação no bote, escala na boia.
8. **Céu:** skybox em cubemap com `GL_CLAMP_TO_EDGE` + `GL_TEXTURE_CUBE_MAP_SEAMLESS`.
9. **Limites:** a câmera fica dentro do oceano, abaixo do céu, e não atravessa o piso.
10. **Tecla P:** `glPolygonMode` entre `GL_FILL` e `GL_LINE`.
11. **Arquivos .obj:** parser próprio em `obj_loader.py`.
12. **Sem iluminação:** o fragment shader só usa a textura.
- **Pipeline moderno:** contexto OpenGL 3.3 core, sem funções obsoletas.

