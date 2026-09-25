#version 330 core

in vec3 vertexColor;
in vec3 vertexNormal;
in vec3 fragPos;

out vec4 fragColor;

uniform vec3 lightPos;
uniform vec3 viewPos;
uniform float shininess;

void main()
{
    vec3 normal = normalize(vertexNormal);

    // Light direction at this fragment
    vec3 lightDir = normalize(lightPos - fragPos);

    // View direction at this fragment
    vec3 viewDir = normalize(viewPos - fragPos);

    // Ambient
    vec3 ambient = 0.2 * vertexColor;

    // Diffuse
    float diffuse = max(dot(normal, lightDir), 0.0);
    vec3 diffuseColor = diffuse * vertexColor;

    // Specular
    vec3 reflectDir = reflect(-lightDir, normal);

    float specular = pow(
        max(dot(viewDir, reflectDir), 0.0),
        shininess
    );

    vec3 specularColor = vec3(1.0) * specular;

    vec3 finalColor =
        ambient +
        diffuseColor +
        specularColor;

    fragColor = vec4(finalColor, 1.0);
}