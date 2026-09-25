#version 330 core

// =============================================================================
// PHONG SHADING  (vertex shader)
// =============================================================================
// No lighting here.
// Transform position and normal to view space and pass them on.
// The GPU smoothly interpolates `vertPos`, `normal_interp`, `colorInterp`
// across the triangle. Lighting is evaluated per fragment in phong.frag.
//
// vs Gouraud: Gouraud lights at vertices then interpolates color
//             → specular highlights smear / vanish on large faces.
// =============================================================================

layout(location = 0) in vec3 position;  // vertex position (object space)
layout(location = 1) in vec3 color;     // vertex color (used as albedo)
layout(location = 2) in vec3 normal;    // vertex normal (object space)

uniform mat4 projection, modelview;

out vec3 normal_interp;   // view-space normal → will be interpolated
out vec3 vertPos;         // view-space position → will be interpolated
out vec3 colorInterp;     // albedo → will be interpolated

void main() {
    // Transform position to view space
    vec4 vertPos4 = modelview * vec4(position, 1.0);
    vertPos = vertPos4.xyz / vertPos4.w;

    // Normal matrix = (M_3x3)^{-T}
    // Use only the 3x3 linear part (rotation + scale), drop translation:
    //   mat3(modelview)  → extract 3x3
    //   inverse          → invert that 3x3
    //   transpose        → transpose
    // Do not normalize here: normalize after interpolation in the fragment
    // shader (interpolating unit vectors does not keep unit length).
    mat3 normal_matrix = transpose(inverse(mat3(modelview)));
    normal_interp = normal_matrix * normal;
    colorInterp = color;

    gl_Position = projection * vertPos4;
}
