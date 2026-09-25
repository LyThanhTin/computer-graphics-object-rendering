#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;
layout(location = 2) in vec3 normal;

out vec3 vertexColor;
out vec3 vertexNormal;
out vec3 fragPos;

uniform mat4 projection;
uniform mat4 modelview;

void main()
{
    vec4 worldPos = modelview * vec4(position, 1.0);

    gl_Position = projection * worldPos;

    fragPos = worldPos.xyz;
    vertexColor = color;
    vertexNormal = normal;
}