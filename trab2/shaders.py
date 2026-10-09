"""Desenha shaders com texturas, skybox e o modo malha"""

vertex_code = """
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec2 TexCoord;

void main(){
    gl_Position = projection * view * model * vec4(position, 1.0);
    TexCoord = texCoord;
}
"""

fragment_code = """
#version 330 core
in vec2 TexCoord;
out vec4 color;

uniform sampler2D texture1;
uniform bool modo_malha; //true quando a malha está visível com a tecla 'p'

void main(){
    if (modo_malha) {
        color = vec4(0.1, 1.0, 0.6, 1.0);   // arestas em verde
    } else {
        color = texture(texture1, TexCoord);
    }
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
    gl_Position = projection * view * vec4(aPos, 1.0);
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