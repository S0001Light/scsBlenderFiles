bl_info = {
    "name": "Writers Jumbler 150 Default Cubes",
    "author": "Shawn + Microsoft 365 Copilot",
    "version": (1, 13, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > WJ150",
    "description": (
        "150x50 default cube grid with Version 7 Auto150 "
        "row spread, Z height controls, and symmetry"
    ),
    "category": "3D View",
}

import bpy
import random


# ============================================================
# GRID SETTINGS
# ============================================================

ROWS = 50
COLS = 150

CUBE_SIZE = 1.0
GAP = 0.08
STEP = CUBE_SIZE + GAP

COLLECTION = "WJ150_DefaultCubeGrid"
MATERIAL = "WJ150_ObjectColorMaterial"
MESH_NAME = "WJ150_DefaultCubeMesh"
CAMERA = "WJ150_TopCamera"

DARK = (0.025, 0.025, 0.025)


# ============================================================
# GRID HELPERS
# ============================================================

def index(row, col):
    return row + col * ROWS


def cubes():
    collection = bpy.data.collections.get(COLLECTION)

    if not collection:
        return []

    result = [
        obj for obj in collection.objects
        if "wj150_index" in obj
    ]

    result.sort(
        key=lambda obj: int(obj["wj150_index"])
    )

    return result


def set_color(obj, rgb):
    obj.color = (
        float(rgb[0]),
        float(rgb[1]),
        float(rgb[2]),
        1.0,
    )


def selected_color(scene):
    return tuple(scene.wj150_color[:3])


def tint(rgb, amount):
    return tuple(
        max(0.0, min(1.0, value + amount))
        for value in rgb
    )


# ============================================================
# VIEWPORT
# ============================================================

def force_object_color(context):
    screen = getattr(context, "screen", None)

    if screen:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.type = 'SOLID'
                space.shading.color_type = 'OBJECT'
                area.tag_redraw()

    context.view_layer.update()


# ============================================================
# MATERIAL
# ============================================================

def material():
    mat = bpy.data.materials.get(MATERIAL)

    if not mat:
        mat = bpy.data.materials.new(MATERIAL)

    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    info = nodes.new("ShaderNodeObjectInfo")

    links.new(
        info.outputs["Color"],
        bsdf.inputs["Base Color"],
    )

    if "Emission Color" in bsdf.inputs:
        links.new(
            info.outputs["Color"],
            bsdf.inputs["Emission Color"],
        )

        bsdf.inputs["Emission Strength"].default_value = 0.12

    bsdf.inputs["Roughness"].default_value = 0.72

    links.new(
        bsdf.outputs["BSDF"],
        output.inputs["Surface"],
    )

    return mat


# ============================================================
# DEFAULT BLENDER-STYLE CUBE MESH
# ============================================================

def default_cube_mesh():
    old_mesh = bpy.data.meshes.get(MESH_NAME)

    if old_mesh and old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

    verts = [
        (-1, -1, -1),
        (-1,  1, -1),
        ( 1,  1, -1),
        ( 1, -1, -1),

        (-1, -1,  1),
        (-1,  1,  1),
        ( 1,  1,  1),
        ( 1, -1,  1),
    ]

    faces = [
        (4, 5, 1, 0),
        (5, 6, 2, 1),
        (6, 7, 3, 2),
        (7, 4, 0, 3),
        (0, 1, 2, 3),
        (7, 6, 5, 4),
    ]

    mesh = bpy.data.meshes.new(MESH_NAME)

    mesh.from_pydata(
        verts,
        [],
        faces,
    )

    mesh.validate()
    mesh.update()
    mesh.materials.append(material())

    return mesh


# ============================================================
# REMOVE GRID
# ============================================================

def remove_grid():
    collection = bpy.data.collections.get(COLLECTION)

    if not collection:
        return

    old_meshes = set()

    for obj in list(collection.objects):
        if obj.type == 'MESH' and obj.data:
            old_meshes.add(obj.data)

        bpy.data.objects.remove(
            obj,
            do_unlink=True,
        )

    bpy.data.collections.remove(collection)

    for mesh in old_meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


# ============================================================
# CAMERA
# ============================================================

def setup_camera(scene):
    cam = bpy.data.objects.get(CAMERA)

    if not cam:
        camera_data = bpy.data.cameras.new(
            CAMERA + "Data"
        )

        cam = bpy.data.objects.new(
            CAMERA,
            camera_data,
        )

        scene.collection.objects.link(cam)

    cam.location = (
        0.0,
        0.0,
        190.0,
    )

    cam.rotation_euler = (
        0.0,
        0.0,
        0.0,
    )

    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ROWS * STEP + 3.0

    scene.camera = cam

    scene.render.resolution_x = 1800
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 50


# ============================================================
# BUILD GRID
# ============================================================

def build_grid(context):
    remove_grid()

    scene = context.scene

    collection = bpy.data.collections.new(
        COLLECTION
    )

    scene.collection.children.link(
        collection
    )

    mesh = default_cube_mesh()
    half = CUBE_SIZE * 0.5

    x_start = -((COLS - 1) * STEP) * 0.5
    y_start = -((ROWS - 1) * STEP) * 0.5

    for col in range(COLS):
        for row in range(ROWS):
            obj = bpy.data.objects.new(
                f"WJ150_R{row:02d}_C{col:03d}",
                mesh,
            )

            obj.scale = (
                half,
                half,
                half,
            )

            obj.location = (
                x_start + col * STEP,
                y_start + row * STEP,
                0.0,
            )

            obj.color = (
                *DARK,
                1.0,
            )

            obj["wj150_index"] = index(row, col)
            obj["wj150_row"] = row
            obj["wj150_col"] = col

            collection.objects.link(obj)

    setup_camera(scene)
    force_object_color(context)


# ============================================================
# CLEAR COLORS
# ============================================================

def clear_grid_colors(context):
    for obj in cubes():
        set_color(obj, DARK)

    force_object_color(context)


# ============================================================
# VERSION 7 AUTO A/B/C ROW SPREAD
# ============================================================

def auto150_row_spread(context, mode):
    """
    Choose one random seed row for each X column.

    Auto A:
        Paint only the seed cube.

    Auto B:
        Paint the seed and vertically spread darker shades.

    Auto C:
        Paint the seed and vertically spread randomized shades.

    Existing colors are preserved between button presses.
    """

    scene = context.scene
    items = cubes()

    if not items:
        return False

    base = selected_color(scene)
    radius = scene.wj150_spread

    for col in range(COLS):
        seed_row = random.randrange(ROWS)

        for row_offset in range(
            -radius,
            radius + 1,
        ):
            row = seed_row + row_offset

            if not 0 <= row < ROWS:
                continue

            distance = abs(row_offset)

            if mode == 'A':
                if row_offset != 0:
                    continue

                result_color = base

            elif mode == 'B':
                result_color = tint(
                    base,
                    -0.055 * distance,
                )

            else:
                result_color = tint(
                    base,
                    random.uniform(-0.10, 0.10)
                    - 0.025 * distance,
                )

            set_color(
                items[index(row, col)],
                result_color,
            )

    force_object_color(context)
    return True


# ============================================================
# Z HEIGHT COLOR
# ============================================================

def height_color(scene, z_value):
    max_z = max(
        scene.wj150_z_step_height,
        scene.wj150_z_steps
        * scene.wj150_z_step_height,
    )

    amount = min(
        1.0,
        abs(z_value) / max_z,
    )

    base = tuple(
        scene.wj150_color[:3]
    )

    if z_value >= 0.0:
        target = tuple(
            scene.wj150_z_plus_color[:3]
        )
    else:
        target = tuple(
            scene.wj150_z_minus_color[:3]
        )

    return tuple(
        base[i] * (1.0 - amount)
        + target[i] * amount
        for i in range(3)
    )


def repaint_from_z(context):
    scene = context.scene

    for obj in cubes():
        set_color(
            obj,
            height_color(
                scene,
                obj.location.z,
            ),
        )

    force_object_color(context)


# ============================================================
# RESET Z
# ============================================================

def reset_z(context):
    for obj in cubes():
        obj.location.z = 0.0

    repaint_from_z(context)


# ============================================================
# RANDOM Z PER CUBE
# ============================================================

def random_signed_z(context):
    scene = context.scene
    items = cubes()

    if not items:
        return False

    levels = list(
        range(
            -scene.wj150_z_steps,
            scene.wj150_z_steps + 1,
        )
    )

    for col in range(COLS):
        for row in range(ROWS):
            obj = items[index(row, col)]

            obj.location.z = (
                random.choice(levels)
                * scene.wj150_z_step_height
            )

    repaint_from_z(context)
    return True


# ============================================================
# RANDOM Z PER COLUMN
# ============================================================

def random_signed_z_by_column(context):
    scene = context.scene
    items = cubes()

    if not items:
        return False

    levels = list(
        range(
            -scene.wj150_z_steps,
            scene.wj150_z_steps + 1,
        )
    )

    for col in range(COLS):
        z_value = (
            random.choice(levels)
            * scene.wj150_z_step_height
        )

        for row in range(ROWS):
            items[
                index(row, col)
            ].location.z = z_value

    repaint_from_z(context)
    return True


# ============================================================
# MOVE ENTIRE GRID ON Z
# ============================================================

def nudge_all_z(context, direction):
    amount = (
        context.scene.wj150_z_step_height
        * direction
    )

    for obj in cubes():
        obj.location.z += amount

    repaint_from_z(context)


# ============================================================
# COLOR SYMMETRY
# ============================================================

def mirror_left_right(left_source=True):
    items = cubes()

    for row in range(ROWS):
        for col in range(COLS // 2):
            left = col
            right = COLS - 1 - col

            if left_source:
                source = left
                destination = right
            else:
                source = right
                destination = left

            set_color(
                items[index(row, destination)],
                items[index(row, source)].color[:3],
            )


def mirror_top_bottom(top_source=True):
    items = cubes()

    for col in range(COLS):
        for row in range(ROWS // 2):
            bottom = row
            top = ROWS - 1 - row

            if top_source:
                source = top
                destination = bottom
            else:
                source = bottom
                destination = top

            set_color(
                items[index(destination, col)],
                items[index(source, col)].color[:3],
            )


def mirror_both():
    items = cubes()

    for row in range(ROWS // 2, ROWS):
        mirrored_row = ROWS - 1 - row

        for col in range(COLS // 2):
            mirrored_col = COLS - 1 - col

            value = items[
                index(row, col)
            ].color[:3]

            set_color(
                items[index(row, mirrored_col)],
                value,
            )

            set_color(
                items[index(mirrored_row, col)],
                value,
            )

            set_color(
                items[index(mirrored_row, mirrored_col)],
                value,
            )


# ============================================================
# BUILD OPERATOR
# ============================================================

class WJ150_OT_Build(bpy.types.Operator):
    bl_idname = "wj150.build_default_cubes"
    bl_label = "Build 150 x 50 Cube Grid"
    bl_description = "Build the complete 7,500-cube grid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        build_grid(context)
        return {'FINISHED'}


# ============================================================
# CLEAR OPERATOR
# ============================================================

class WJ150_OT_Clear(bpy.types.Operator):
    bl_idname = "wj150.clear_default_cubes"
    bl_label = "Clear Grid Colors"
    bl_description = "Reset every cube to the dark background color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not cubes():
            self.report(
                {'WARNING'},
                "Build the cube grid first",
            )
            return {'CANCELLED'}

        clear_grid_colors(context)
        return {'FINISHED'}


# ============================================================
# AUTO A/B/C OPERATOR
# ============================================================

class WJ150_OT_Auto150(bpy.types.Operator):
    bl_idname = "wj150.auto150"
    bl_label = "Auto150 Row Spread"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[
            (
                'A',
                "Auto A150",
                "Place one randomly positioned colored cube per column",
            ),
            (
                'B',
                "Auto B150",
                "Place random seeds with vertically fading colors",
            ),
            (
                'C',
                "Auto C150",
                "Place random seeds with randomized vertical color spreading",
            ),
        ]
    )

    def execute(self, context):
        if not auto150_row_spread(
            context,
            self.mode,
        ):
            self.report(
                {'WARNING'},
                "Build the cube grid first",
            )
            return {'CANCELLED'}

        return {'FINISHED'}


# ============================================================
# RANDOM Z OPERATOR
# ============================================================

class WJ150_OT_RandomZ(bpy.types.Operator):
    bl_idname = "wj150.random_z"
    bl_label = "Random Signed Z"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[
            (
                'CUBE',
                "Each Cube +/- Z",
                "Give every cube an independent random Z value",
            ),
            (
                'COLUMN',
                "Each Column +/- Z",
                "Give every column one shared random Z value",
            ),
        ]
    )

    def execute(self, context):
        if self.mode == 'CUBE':
            success = random_signed_z(context)
        else:
            success = random_signed_z_by_column(
                context
            )

        if not success:
            self.report(
                {'WARNING'},
                "Build the cube grid first",
            )
            return {'CANCELLED'}

        return {'FINISHED'}


# ============================================================
# RESET Z OPERATOR
# ============================================================

class WJ150_OT_ResetZ(bpy.types.Operator):
    bl_idname = "wj150.reset_z"
    bl_label = "Flatten Z"
    bl_description = "Return every cube to Z equals zero"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not cubes():
            self.report(
                {'WARNING'},
                "Build the cube grid first",
            )
            return {'CANCELLED'}

        reset_z(context)
        return {'FINISHED'}


# ============================================================
# NUDGE Z OPERATOR
# ============================================================

class WJ150_OT_NudgeZ(bpy.types.Operator):
    bl_idname = "wj150.nudge_z"
    bl_label = "Move Entire Grid Z"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.IntProperty(
        default=1
    )

    def execute(self, context):
        if not cubes():
            self.report(
                {'WARNING'},
                "Build the cube grid first",
            )
            return {'CANCELLED'}

        nudge_all_z(
            context,
            self.direction,
        )

        return {'FINISHED'}


# ============================================================
# REPAINT Z OPERATOR
# ============================================================

class WJ150_OT_RepaintZ(bpy.types.Operator):
    bl_idname = "wj150.repaint_z"
    bl_label = "Repaint from Z Heights"
    bl_description = "Replace existing colors with Z height colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not cubes():
            self.report(
                {'WARNING'},
                "Build the cube grid first",
            )
            return {'CANCELLED'}

        repaint_from_z(context)
        return {'FINISHED'}


# ============================================================
# SYMMETRY OPERATOR
# ============================================================

class WJ150_OT_Symmetry(bpy.types.Operator):
    bl_idname = "wj150.symmetry_default_cubes"
    bl_label = "Cube Grid Symmetry"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[
            ('LR', "Left to Right", ""),
            ('RL', "Right to Left", ""),
            ('TB', "Top to Bottom", ""),
            ('BT', "Bottom to Top", ""),
            ('BOTH', "Both Directions", ""),
        ]
    )

    def execute(self, context):
        if not cubes():
            self.report(
                {'WARNING'},
                "Build the cube grid first",
            )
            return {'CANCELLED'}

        actions = {
            'LR': lambda: mirror_left_right(True),
            'RL': lambda: mirror_left_right(False),
            'TB': lambda: mirror_top_bottom(True),
            'BT': lambda: mirror_top_bottom(False),
            'BOTH': mirror_both,
        }

        actions[self.mode]()
        force_object_color(context)

        return {'FINISHED'}


# ============================================================
# SIDEBAR PANEL
# ============================================================

class WJ150_PT_Panel(bpy.types.Panel):
    bl_label = "WJ150 Painted Z Cubes"
    bl_idname = "WJ150_PT_DEFAULT_CUBES"

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'WJ150'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ----------------------------------------------------
        # BUILD
        # ----------------------------------------------------

        box = layout.box()

        box.label(
            text="Blender-Style Cube Grid",
            icon='CUBE',
        )

        box.operator(
            "wj150.build_default_cubes",
            text="Build 150 x 50 Cube Grid",
            icon='MESH_CUBE',
        )

        box.operator(
            "wj150.clear_default_cubes",
            text="Clear Grid Colors",
            icon='TRASH',
        )

        # ----------------------------------------------------
        # VERSION 7 AUTO A/B/C
        # ----------------------------------------------------

        box = layout.box()

        box.label(
            text="Auto150 Row Spread",
            icon='COLOR',
        )

        box.prop(
            scene,
            "wj150_color",
            text="Color",
        )

        box.prop(
            scene,
            "wj150_spread",
            text="Spread Rows",
        )

        row = box.row(align=True)

        operator = row.operator(
            "wj150.auto150",
            text="Auto A150",
        )
        operator.mode = 'A'

        operator = row.operator(
            "wj150.auto150",
            text="Auto B150",
        )
        operator.mode = 'B'

        operator = row.operator(
            "wj150.auto150",
            text="Auto C150",
        )
        operator.mode = 'C'

        box.label(
            text="A: one random seed per column",
            icon='INFO',
        )

        box.label(
            text="B: faded spread   C: random spread",
        )

        # ----------------------------------------------------
        # Z CONTROLS
        # ----------------------------------------------------

        box = layout.box()

        box.label(
            text="Painted Z- / Z+ Solid View",
            icon='CUBE',
        )

        box.prop(
            scene,
            "wj150_z_steps",
            text="Max +/- Z Steps",
        )

        box.prop(
            scene,
            "wj150_z_step_height",
            text="Z Step Size",
        )

        box.prop(
            scene,
            "wj150_z_minus_color",
            text="Z- Color",
        )

        box.prop(
            scene,
            "wj150_z_plus_color",
            text="Z+ Color",
        )

        row = box.row(align=True)

        operator = row.operator(
            "wj150.nudge_z",
            text="Z -",
        )
        operator.direction = -1

        operator = row.operator(
            "wj150.nudge_z",
            text="Z +",
        )
        operator.direction = 1

        row = box.row(align=True)

        operator = row.operator(
            "wj150.random_z",
            text="Random Z Cubes",
        )
        operator.mode = 'CUBE'

        operator = row.operator(
            "wj150.random_z",
            text="Random Z Columns",
        )
        operator.mode = 'COLUMN'

        box.operator(
            "wj150.repaint_z",
            text="Repaint from Z Heights",
        )

        box.operator(
            "wj150.reset_z",
            text="Flatten Back to Z = 0",
        )

        box.label(
            text="Only Z changes. X/Y stays locked.",
            icon='INFO',
        )

        # ----------------------------------------------------
        # SYMMETRY
        # ----------------------------------------------------

        box = layout.box()

        box.label(
            text="Color Symmetry",
            icon='MOD_MIRROR',
        )

        row = box.row(align=True)

        operator = row.operator(
            "wj150.symmetry_default_cubes",
            text="Left -> Right",
        )
        operator.mode = 'LR'

        operator = row.operator(
            "wj150.symmetry_default_cubes",
            text="Right -> Left",
        )
        operator.mode = 'RL'

        row = box.row(align=True)

        operator = row.operator(
            "wj150.symmetry_default_cubes",
            text="Top -> Bottom",
        )
        operator.mode = 'TB'

        operator = row.operator(
            "wj150.symmetry_default_cubes",
            text="Bottom -> Top",
        )
        operator.mode = 'BT'

        operator = box.operator(
            "wj150.symmetry_default_cubes",
            text="Mirror Both Directions",
        )
        operator.mode = 'BOTH'


# ============================================================
# REGISTRATION
# ============================================================

CLASSES = (
    WJ150_OT_Build,
    WJ150_OT_Clear,
    WJ150_OT_Auto150,
    WJ150_OT_RandomZ,
    WJ150_OT_ResetZ,
    WJ150_OT_NudgeZ,
    WJ150_OT_RepaintZ,
    WJ150_OT_Symmetry,
    WJ150_PT_Panel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.wj150_color = (
        bpy.props.FloatVectorProperty(
            name="Color",
            subtype='COLOR',
            size=3,
            default=(0.05, 0.35, 1.0),
            min=0.0,
            max=1.0,
        )
    )

    bpy.types.Scene.wj150_spread = (
        bpy.props.IntProperty(
            name="Spread Rows",
            description=(
                "Rows above and below each random seed "
                "used by Auto B and Auto C"
            ),
            default=3,
            min=0,
            max=24,
        )
    )

    bpy.types.Scene.wj150_z_steps = (
        bpy.props.IntProperty(
            name="Max Z Steps",
            default=10,
            min=0,
            max=100,
        )
    )

    bpy.types.Scene.wj150_z_step_height = (
        bpy.props.FloatProperty(
            name="Z Step Height",
            default=5.0,
            min=0.01,
            max=100.0,
        )
    )

    bpy.types.Scene.wj150_z_minus_color = (
        bpy.props.FloatVectorProperty(
            name="Z- Color",
            subtype='COLOR',
            size=3,
            default=(0.08, 0.15, 1.0),
            min=0.0,
            max=1.0,
        )
    )

    bpy.types.Scene.wj150_z_plus_color = (
        bpy.props.FloatVectorProperty(
            name="Z+ Color",
            subtype='COLOR',
            size=3,
            default=(1.0, 0.12, 0.03),
            min=0.0,
            max=1.0,
        )
    )


def unregister():
    properties = (
        "wj150_color",
        "wj150_spread",
        "wj150_z_steps",
        "wj150_z_step_height",
        "wj150_z_minus_color",
        "wj150_z_plus_color",
    )

    for property_name in properties:
        if hasattr(
            bpy.types.Scene,
            property_name,
        ):
            delattr(
                bpy.types.Scene,
                property_name,
            )

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


# ============================================================
# DIRECT SCRIPT EXECUTION
# ============================================================

if __name__ == "__main__":
    register()
    build_grid(bpy.context)
