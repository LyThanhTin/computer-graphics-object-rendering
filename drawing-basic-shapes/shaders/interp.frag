#version 330 core

// =============================================================================
// INTERPOLATED VERTEX COLOR  (fragment shader)
// =============================================================================
// No lighting. Use the smoothly interpolated vertex colors.
// =============================================================================

in vec3 fragment_color;
out vec4 out_color;

void main() {
    out_color = vec4(fragment_color, 1.0);
}
