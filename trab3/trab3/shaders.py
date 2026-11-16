"""Shaders GLSL: objetos com o modelo de iluminação de Phong (Projeto 3),
skybox e modo malha.

Separação interno / externo: cada objeto envia o uniform 'interno'. Objetos
externos só somam a luz externa (a lua) e objetos internos só somam as duas
luzes da cabine (lustre e abajur). A luz ambiente vale para os dois.
"""
from OpenGL.GL import glGetUniformLocation

vertex_code = """
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoord;
layout(location = 2) in vec3 normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec2 TexCoord;
out vec3 FragPos;   // posição do fragmento no mundo (out_fragPos na aula)
out vec3 Normal;    // normal no mundo (out_normal na aula)

void main(){
    vec4 mundo = model * vec4(position, 1.0);
    FragPos = mundo.xyz;
    Normal = mat3(model) * normal;
    TexCoord = texCoord;
    gl_Position = projection * view * mundo;
}
"""

fragment_code = """
#version 330 core
in vec2 TexCoord;
in vec3 FragPos;
in vec3 Normal;
out vec4 color;

// ---------------------------------------------------------------- fontes de luz
struct Luz {
    vec3  posicao;      // lightPos na aula
    vec3  cor;          // lightColor na aula (Ii)
    float constante;    // fatt = 1 / (constante + linear*d + quadratica*d^2)
    float linear;
    float quadratica;
    bool  ligada;       // "interruptor" de cada luz
};
uniform Luz luz_externa;           // lua (ambiente externo)
uniform Luz luzes_internas[2];     // lustre do teto e abajur (ambiente interno)

// luz ambiente (global)
uniform bool  ambiente_ligada;
uniform float intensidade_ambiente;
uniform vec3  cor_ambiente;

// fatores globais controlados pelo teclado (multiplicam kd e ks)
uniform float fator_difuso;
uniform float fator_especular;

// ---------------------------------------------------------------- material do objeto
uniform float ka;          // coeficiente de reflexão ambiente
uniform float kd;          // coeficiente de reflexão difusa
uniform float ks;          // coeficiente de reflexão especular
uniform float ns;          // expoente de reflexão especular
uniform vec3  cor_base;    // multiplica a textura (peças geradas por código)
uniform vec3  emissao;     // lâmpada acesa (ver comentário no main)
uniform bool  interno;     // true = objeto da cabine

uniform vec3 viewPos;      // posição da câmera/observador (mesmo nome da aula)
uniform sampler2D texture1;
uniform bool modo_malha;   // true quando a malha está visível com a tecla 'p'

// reflexão difusa + especular de UMA fonte pontual 
vec3 phong(Luz luz, vec3 N, vec3 V){
    if (!luz.ligada) return vec3(0.0);

    vec3  L = luz.posicao - FragPos;            // direção da luz
    float d = length(L);
    L = L / d;
    float fatt = 1.0 / (luz.constante + luz.linear * d + luz.quadratica * d * d);

    // difusa: kd * cos(teta), com cos(teta) = N . L  (lei de Lambert)
    float diff = max(dot(N, L), 0.0);
    vec3 difusa = kd * fator_difuso * diff * luz.cor;

    // especular: ks * cos(alfa)^ns, com cos(alfa) = R . V
    // (se a luz está atrás da superfície, diff = 0, não há brilho)
    vec3 R = reflect(-L, N);                    // direção da reflexão
    float spec = (diff > 0.0) ? pow(max(dot(V, R), 0.0), ns) : 0.0;
    vec3 especular = ks * fator_especular * spec * luz.cor;

    return fatt * (difusa + especular);
}

void main(){
    if (modo_malha) {
        color = vec4(0.1, 1.0, 0.6, 1.0);   // arestas em verde
        return;
    }

    vec3 N = normalize(Normal);
    vec3 V = normalize(viewPos - FragPos);      // direção do observador
    // Iluminação dos dois lados: paredes, pisos e alguns .obj são vistos pelos
    // dois lados (e nem todo .obj tem as faces orientadas igual), então a
    // normal é virada para o lado de quem está olhando.
    if (dot(N, V) < 0.0) N = -N;

    // ambiente: Ia * ka
    vec3 ambiente = vec3(0.0);
    if (ambiente_ligada)
        ambiente = intensidade_ambiente * ka * cor_ambiente;

    // soma das fontes pontuais: cada ambiente só recebe as SUAS luzes
    vec3 luzes = vec3(0.0);
    if (interno) {
        for (int i = 0; i < 2; i++)
            luzes += phong(luzes_internas[i], N, V);
    } else {
        luzes += phong(luz_externa, N, V);
    }

    // Lâmpadas acesas (globo do lustre, lâmpada do abajur, lua): na aula o
    // luz.obj é desenhado com ka = 1 para aparecer aceso; aqui somamos a cor
    // da luz ('emissao'), que vira 0 quando a luz é desligada.
    vec4 textura = texture(texture1, TexCoord) * vec4(cor_base, 1.0);
    color = vec4(ambiente + luzes + emissao, 1.0) * textura;   // aplica iluminação
}
"""

skybox_vertex_code = """
#version 330 core
layout (location = 0) in vec3 aPos;

out vec3 texCoords;

uniform mat4 projection;
uniform mat4 view;

void main() {
    texCoords = aPos;
    vec4 pos = projection * view * vec4(aPos, 1.0);
    gl_Position = pos.xyww;  //tivemos que forçar o skybox a ter z = w para arrumar a profundidade
}
"""

skybox_fragment_code = """
#version 330 core
in vec3 texCoords;
out vec4 FragColor;

uniform samplerCube skybox;

void main() {
    FragColor = texture(skybox, texCoords);
}
"""


# ------------------------------------------------------------------ utilidade
_cache_locais = {}


def uniform(programa, nome):
    """glGetUniformLocation com cache (evita consultar o driver a cada objeto)."""
    chave = (int(programa), nome)
    if chave not in _cache_locais:
        _cache_locais[chave] = glGetUniformLocation(programa, nome)
    return _cache_locais[chave]
