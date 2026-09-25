#version 330 core

// =============================================================================
// INTERPOLATED VERTEX COLOR  (vertex shader)
// =============================================================================
// No lighting. Pass each vertex color through; the GPU smoothly interpolates
// it across the triangle (the classic RGB triangle).
//
// vs Gouraud: Gouraud also interpolates color, but that color was *lit* at
//             the vertex. Here the color is the vertex attribute itself.
// vs Flat:    Flat uses `flat` so the whole face is one color.
// vs Phong:   Phong interpolates normals and lights per fragment.
// =============================================================================

layout(location = 0) in vec3 position;  // vertex position (object space)
layout(location = 1) in vec3 color;     // vertex color (no lighting)

uniform mat4 projection, modelview;

out vec3 fragment_color;    // vertex color → interpolated to the fragment

void main() {
    fragment_color = color;
    gl_Position = projection * modelview * vec4(position, 1.0);
}
