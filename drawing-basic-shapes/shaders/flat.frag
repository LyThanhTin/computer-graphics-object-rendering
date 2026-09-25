#version 330 core

// =============================================================================
// FLAT SHADING  (fragment shader)
// =============================================================================
// `flat in` must match `flat out` in the vertex shader.
// Every fragment of the triangle gets the same color (provoking vertex).
// No lighting here.
// =============================================================================

flat in vec3 fragment_color;    // constant over the face, not interpolated
out vec4 out_color;

void main() {
    out_color = vec4(fragment_color, 1.0);
}
