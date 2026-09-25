#version 330 core

// =============================================================================
// GOURAUD SHADING  (fragment shader)
// =============================================================================
// No lighting here.
// `fragment_color` was computed at the three vertices and is smoothly
// interpolated across the triangle → specular highlights smear on large faces.
// =============================================================================

in vec3 fragment_color;     // color interpolated from the three vertices
out vec4 out_color;

void main() {
    out_color = vec4(fragment_color, 1.0);
}
