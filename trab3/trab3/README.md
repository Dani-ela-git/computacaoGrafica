# Titanic, 14 de abril de 1912 — Projeto 3 (SCC0250)

Continuação do Projeto 2: a mesma cena 3D em OpenGL moderno (Python + GLFW +
PyOpenGL + PyGLM), agora com **iluminação de Phong** (ambiente, difusa e
especular). O usuário começa na cabine e consegue andar pela cena.

## Como rodar

```bash
pip install glfw PyOpenGL PyGLM numpy Pillow
python main.py
```

Ou pelo Jupyter (Anaconda): abra `executar.ipynb` (nesta pasta) e rode as células.

Os modelos, texturas e o céu ficam em `assets/`.

## Controles

| Tecla | Ação |
|---|---|
| Mouse / setas | olhar |
| Roda do mouse | zoom |
| W A S D | andar |
| Espaço / Ctrl | subir / descer |
| Shift | correr |
| **1** | liga/desliga a luz **ambiente** |
| **2** | liga/desliga a **lua** (luz externa) |
| **3** | liga/desliga o **lustre do teto** (luz interna, branco-azulada) |
| **4** | liga/desliga o **abajur** (luz interna, âmbar) |
| **Z / X** | diminui / aumenta a luz ambiente |
| **C / V** | diminui / aumenta a reflexão difusa |
| **B / N** | diminui / aumenta a reflexão especular |
| M | pausa / continua o movimento da lua |
| P | mostrar/ocultar malha |
| Esc | sair |

Segurar Z/X, C/V ou B/N continua ajustando. O estado de todas as luzes
aparece no **título da janela** (e no console) a cada mudança.

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `main.py` | janela, shaders, teclado/mouse e laço principal |
| `config.py` | medidas (metros), modelos, **materiais**, **luzes** e teclas |
| `iluminacao.py` | **(novo)** classes `Luz` e `Iluminacao`: interruptores, intensidades e envio dos uniforms |
| `cena.py` | monta a cena, a **lua** (animação) e as **luminárias** da cabine |
| `mesh.py` | classe `Mesh` (VAO/VBO/EBO com posição + textura + **normal**) |
| `obj_loader.py` | parser .obj/.mtl próprio; agora lê `vn` ou **calcula as normais** |
| `texture_loader.py` | texturas 2D, cubemap da skybox e textura branca (peças sem imagem) |
| `shaders.py` | GLSL com o **modelo de Phong** e a skybox |
| `camera.py` | câmera em 1ª pessoa com glm e limites do cenário |
| `geometria.py` | pisos, oceano, paredes, casco e (novo) esfera, cilindro, cone e caixa com normais |
| `gerar_lua.py` | **(novo)** gera `lua.obj` (já gerado; não precisa rodar) |

## Iluminação

Segue a Aula 18 (Iluminação e Tonalização) e os códigos `Tema11.Ex01/Ex02`.
Modelo de iluminação de **Phong** com M fontes de luz coloridas (slide 48):

```
I = Ia·ka + Σ Ii · fatt · ( kd·cos θi + ks·cosⁿ αi )      e o resultado × textura
    ambiente              difusa        especular
```

### Correspondência aula → código

| Na aula | Aqui |
|---|---|
| `ka`, `kd`, `ks`, `ns` definidos em `desenha_caixa()` / `desenha_chaleira()` | `config.MATERIAIS`: cada objeto tem os seus (enviados em `Objeto.desenhar`) |
| `Ia` (intensidade da luz ambiente, slide 10) | `intensidade_ambiente` (teclas Z/X; liga/desliga na tecla 1) |
| `lightPos1`, `lightPos2`, `lightColor1`, `lightColor2` | struct `Luz` no shader: `luz_externa` (lua) e `luzes_internas[2]` (lustre, abajur) |
| `diff = max(dot(norm, lightDir), 0)` (Lambert) | igual, na função `phong()` do fragment shader |
| `reflectDir = reflect(-lightDir, norm)`, `pow(max(dot(viewDir, reflectDir), 0), ns)` | igual |
| `viewPos` (posição da câmera) | `viewPos` |
| `result = vec4(ambient + diffuse + specular, 1) * texture` | `color = vec4(ambiente + luzes + emissao, 1) * textura` |
| `fatt = 1/d²` (slide 29) | `fatt = 1 / (constante + linear·d + quadratica·d²)` (a lua usa `fatt = 1`) |
| `luz.obj` desenhado com `ka = 1` para aparecer aceso | a lua é um `.obj` (`lua.obj`); lâmpadas acesas recebem `emissao` = cor da luz |
| `desenha_luz(..., t_x, t_y, t_z)` usa a mesma translação como `lightPos` | `Lua.atualizar()` usa a posição da lua como posição da luz |
| Tonalização de Phong: normal interpolada, cálculo no fragment shader (slides 64-69) | igual |
| Teclas U/I/O ligam/desligam ka/kd/ks | 1–4 interruptores; Z/X, C/V, B/N aumentam/diminuem |

### Detalhes

- **Normais:** quando o .obj não tem `vn` (piano, boia, poltrona, iceberg),
  o loader calcula a normal do vértice como a **média das normais das faces**
  que o usam (slide 59). Em quinas vivas usa a normal da própria face.
  O iceberg usa normais planas (flat, slide 55: visual facetado de gelo).
- **Normal no vertex shader:** `mat3(model) * normal`, isto é, só rotação e
  escala. (No `vertex_shader.vs` da aula é `model * vec4(normal, 1.0)`, o que
  também soma a translação; lá os objetos ficam na origem, aqui não.)
- **Dois lados:** a normal é virada para o lado da câmera, então paredes,
  pisos e modelos vistos por dentro também recebem luz.
- **Lâmpadas acesas brilham:** o globo do lustre, a lâmpada/cúpula do abajur e
  a lua somam `emissao` com a cor da sua luz; desligando, apagam.
- **A lua** é `assets/models/lua.obj` (esfera UV de raio 1 com `v`, `vt`, `vn`,
  gerada por `gerar_lua.py` e lida pelo mesmo parser dos outros modelos) com a
  textura `assets/textures/lua.jpg`, o mapa de cores real da Lua (projeção
  equirretangular). A esfera foi montada para que o lado visível da Lua fique
  virado para o navio.

### Separação interno × externo

Cada objeto tem a propriedade `interno` (enviada ao shader como uniform).
Objetos **externos** somam só a luz externa e objetos **internos** somam só as
duas luzes da cabine. A luz ambiente vale para os dois.

As paredes da cabine têm uma "casca" externa 2 cm para fora: vista do convés,
a parede é um objeto externo (recebe a lua); vista de dentro, é interna
(recebe lustre e abajur). Assim a luz não "vaza" pela parede nem pela porta.

## Como cada requisito é atendido

1. **Objeto externo com translação e fonte de luz:** a lua (`lua.obj` com
   textura, classe `Lua` em `cena.py`) anda num arco pelo céu, de um lado ao outro e de
   volta, sem descer abaixo do horizonte. A luz fica no centro da esfera e
   acompanha o movimento, então a direção da luz no navio, no oceano e no
   iceberg muda com o tempo. Só afeta objetos externos.
2. **Duas luzes internas de cores diferentes:** lustre no teto (luz elétrica,
   branco-azulada) e abajur sobre um criado-mudo ao lado da cama (âmbar).
   Lustre, abajur e criado-mudo foram criados por código. Só afetam a cabine.
3. **Interruptores independentes:** teclas 1 (ambiente), 2, 3 e 4. Cada uma
   muda a cena visivelmente (a lâmpada correspondente também apaga).
4. **Luz ambiente:** Z / X.
5. **Reflexão difusa:** C / V (multiplica o `kd` de todos os objetos).
6. **Reflexão especular:** B / N (multiplica o `ks` de todos os objetos).
7. **Parâmetros próprios por objeto:** `config.MATERIAIS` (ka, kd, ks, ns).
8. **Teclas do Projeto 2 retiradas:** translação/rotação/escala pelo teclado
   foram removidas. A tecla P (malha) foi mantida.
- **Pipeline moderno:** contexto OpenGL 3.3 core, sem funções obsoletas
  (nada de glLight, glMaterial etc.: tudo é feito no shader).

## O que mudou em relação ao Projeto 2

- Vértices passaram de 5 para 8 floats (posição, textura, normal).
- Shader com Phong + uniforms de luz e material.
- Lua (`.obj` com textura) se movendo pelo céu (fonte de luz externa).
- Lustre, abajur e criado-mudo na cabine.
- Casca externa da cabine e face de baixo da superestrutura.
- Iceberg, bote e boia não mudam mais pelo teclado.

## Créditos

- Textura da lua (`assets/textures/lua.jpg`): NASA/Goddard Space Flight Center
  Scientific Visualization Studio, *CGI Moon Kit* — https://svs.gsfc.nasa.gov/4720
