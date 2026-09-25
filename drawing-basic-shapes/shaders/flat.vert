#version 330 core

// =============================================================================
// FLAT SHADING  (vertex shader)
// =============================================================================
// Same Phong formula as Gouraud, evaluated AT THE VERTEX.
// Unlike Gouraud, the `flat` qualifier disables interpolation:
// the whole triangle uses the *provoking vertex* color (last vertex of
// the primitive by default in OpenGL). One face = one color, hard edges.
// =============================================================================

layout(location = 0) in vec3 position;  // vertex position (object space)
layout(location = 1) in vec3 color;     // vertex color (used as albedo)
layout(location = 2) in vec3 normal;    // vertex normal (object space)

uniform mat4 projection, modelview;
uniform mat3 K_materials;   // rows: diffuse, specular, ambient
uniform mat3 I_light;       // matching light intensities
uniform float shininess;    // specular exponent (n)
uniform vec3 light_pos;     // light position (view space)

flat out vec3 fragment_color;   // `flat`: no interpolation between vertices

void main() {
    // Transform position to view space
    vec4 vertPos4 = modelview * vec4(position, 1.0);
    vec3 vertPos = vertPos4.xyz / vertPos4.w;

    // Normal matrix = (M_3x3)^{-T}
    // Use only the 3x3 linear part (rotation + scale), drop translation:
    //   mat3(modelview)  → extract 3x3
    //   inverse          → invert that 3x3
    //   transpose        → transpose
    mat3 normal_matrix = transpose(inverse(mat3(modelview)));
    vec3 N = normalize(normal_matrix * normal);       // normal (view space)
    vec3 L = normalize(light_pos - vertPos);          // toward the light
    vec3 V = normalize(-vertPos);                     // toward the camera (view origin = 0)
    vec3 R = reflect(-L, N);                          // reflection of -L about N

    // Diffuse: max(N·L, 0). Specular only if the face sees the light (N·L > 0).
    float diff = max(dot(N, L), 0.0);
    float spec = 0.0;
    if (diff > 0.0) {
        spec = pow(max(dot(R, V), 0.0), shininess);
    }

    // g = (diffuse, specular, ambient=1)
    // (K ⊙ I) * g  =  K_d⊙I_d * diff  +  K_s⊙I_s * spec  +  K_a⊙I_a
    vec3 g = vec3(diff, spec, 1.0);
    fragment_color = (matrixCompMult(K_materials, I_light) * g) * color;

    gl_Position = projection * vertPos4;
}
