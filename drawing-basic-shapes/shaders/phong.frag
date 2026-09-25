#version 330 core

precision mediump float;

// =============================================================================
// PHONG SHADING  (fragment shader)
// =============================================================================
// Evaluate the Phong illumination model AT EACH FRAGMENT.
// `normal_interp` and `vertPos` were interpolated from the three vertices,
// so N must be re-normalized (interpolation breaks unit length).
// Specular highlights stay round — more accurate than Gouraud on coarse meshes.
// =============================================================================

in vec3 normal_interp;   // interpolated normal (not necessarily unit length)
in vec3 vertPos;         // interpolated view-space position
in vec3 colorInterp;     // interpolated albedo

uniform mat3 K_materials;   // rows: diffuse, specular, ambient
uniform mat3 I_light;       // matching light intensities
uniform float shininess;    // specular exponent (n)
uniform vec3 light_pos;     // light position (view space)

out vec4 fragColor;

void main() {
    vec3 N = normalize(normal_interp);                // required after interpolation
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
    vec3 rgb = (matrixCompMult(K_materials, I_light) * g) * colorInterp;

    fragColor = vec4(rgb, 1.0);
}
