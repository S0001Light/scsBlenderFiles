bl_info = {
    "name": "Writers Jumbler 150 Default Cubes Rows",
    "author": "Shawn + Microsoft 365 Copilot",
    "version": (1, 10, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > WJ150",
    "description": "150x50 grid made from Blender-style cubes; Auto150 advances upward by Y row",
    "category": "3D View",
}
import bpy, random

ROWS, COLS = 50, 150
CUBE_SIZE, GAP = 1.0, 0.08
STEP = CUBE_SIZE + GAP
COLLECTION = "WJ150_DefaultCubeGrid"
MATERIAL = "WJ150_ObjectColorMaterial"
CAMERA = "WJ150_TopCamera"
DARK = (0.025, 0.025, 0.025)

def index(row, col): return row + col * ROWS

def cubes():
    collection = bpy.data.collections.get(COLLECTION)
    if not collection: return []
    result = [o for o in collection.objects if "wj150_index" in o]
    result.sort(key=lambda o: int(o["wj150_index"]))
    return result

def set_color(obj, rgb): obj.color = (float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)
def selected_color(scene): return tuple(scene.wj150_color[:3])
def shade(rgb, amount): return tuple(max(0.0, min(1.0, v + amount)) for v in rgb)

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

def material():
    mat = bpy.data.materials.get(MATERIAL) or bpy.data.materials.new(MATERIAL)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    info = nodes.new("ShaderNodeObjectInfo")
    links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        links.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 0.12
    bsdf.inputs["Roughness"].default_value = 0.72
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat

def default_cube_mesh():
    # Same proportions as Blender's startup cube: 2 x 2 x 2 before object scale.
    verts = [(-1,-1,-1),(-1,1,-1),(1,1,-1),(1,-1,-1),
             (-1,-1,1),(-1,1,1),(1,1,1),(1,-1,1)]
    faces = [(4,5,1,0),(5,6,2,1),(6,7,3,2),(7,4,0,3),(0,1,2,3),(7,6,5,4)]
    mesh = bpy.data.meshes.new("WJ150_DefaultCubeMesh")
    mesh.from_pydata(verts, [], faces); mesh.validate(); mesh.update()
    mesh.materials.append(material())
    return mesh

def remove_grid():
    collection = bpy.data.collections.get(COLLECTION)
    if collection:
        for obj in list(collection.objects): bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)

def setup_camera(scene):
    cam = bpy.data.objects.get(CAMERA)
    if not cam:
        data = bpy.data.cameras.new(CAMERA + "Data")
        cam = bpy.data.objects.new(CAMERA, data)
        scene.collection.objects.link(cam)
    cam.location = (0.0, 0.0, 190.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    cam.data.type = 'ORTHO'
    # 3:1 render ratio covers 150 columns by 50 rows from directly above.
    cam.data.ortho_scale = ROWS * STEP + 3.0
    scene.camera = cam
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 50

def build_grid(context):
    remove_grid()
    scene = context.scene
    collection = bpy.data.collections.new(COLLECTION)
    scene.collection.children.link(collection)
    mesh = default_cube_mesh()
    half = CUBE_SIZE * 0.5
    x0 = -((COLS - 1) * STEP) * 0.5
    y0 = -((ROWS - 1) * STEP) * 0.5
    for row in range(ROWS):
        for col in range(COLS):
            obj = bpy.data.objects.new(f"WJ150_R{row:02d}_C{col:03d}", mesh)
            obj.scale = (half, half, half)
            obj.location = (x0 + col * STEP, y0 + row * STEP, 0.0)
            obj.color = (*DARK, 1.0)
            obj["wj150_index"], obj["wj150_row"], obj["wj150_col"] = index(row,col), row,col
            collection.objects.link(obj)
    scene.wj150_next_row = 0
    setup_camera(scene)
    force_object_color(context)

def clear_grid_colors(context):
    for obj in cubes(): set_color(obj, DARK)
    context.scene.wj150_next_row = 0
    force_object_color(context)

def auto150_row(context, mode):
    scene, items = context.scene, cubes()
    if not items: return False
    row = scene.wj150_next_row % ROWS
    base = selected_color(scene)
    for col in range(COLS):
        if mode == 'A': value = base
        elif mode == 'B': value = shade(base, random.uniform(-0.12, 0.08))
        else:
            wave = ((col % 12) / 11.0 - 0.5) * 0.22
            value = shade(base, wave + random.uniform(-0.05, 0.05))
        set_color(items[index(row, col)], value)
    scene.wj150_next_row = (row + 1) % ROWS
    force_object_color(context)
    return True

def height_color(scene, z_value):
    """Paint by signed Z: positive blends toward plus color, negative toward minus color."""
    max_z = max(scene.wj150_z_step_height, scene.wj150_z_steps * scene.wj150_z_step_height)
    t = min(1.0, abs(z_value) / max_z)
    base = tuple(scene.wj150_color[:3])
    target = tuple(scene.wj150_z_plus_color[:3]) if z_value >= 0.0 else tuple(scene.wj150_z_minus_color[:3])
    return tuple(base[i] * (1.0 - t) + target[i] * t for i in range(3))


def repaint_from_z(context):
    scene = context.scene
    for obj in cubes():
        set_color(obj, height_color(scene, obj.location.z))
    force_object_color(context)


def reset_z(context):
    for obj in cubes():
        obj.location.z = 0.0
    repaint_from_z(context)


def random_signed_z(context):
    """X and Y never move. Each cube only receives a random negative or positive Z step."""
    scene, items = context.scene, cubes()
    if not items:
        return False
    levels = list(range(-scene.wj150_z_steps, scene.wj150_z_steps + 1))
    for col in range(COLS):
        for row in range(ROWS):
            obj = items[index(row, col)]
            obj.location.z = random.choice(levels) * scene.wj150_z_step_height
    repaint_from_z(context)
    return True


def random_signed_z_by_column(context):
    """One signed Z value per X column; all 50 Y cubes in that column share it."""
    scene, items = context.scene, cubes()
    if not items:
        return False
    levels = list(range(-scene.wj150_z_steps, scene.wj150_z_steps + 1))
    for col in range(COLS):
        z = random.choice(levels) * scene.wj150_z_step_height
        for row in range(ROWS):
            items[index(row, col)].location.z = z
    repaint_from_z(context)
    return True


def nudge_all_z(context, direction):
    """Move the complete solid grid only on Z- or Z+."""
    amount = context.scene.wj150_z_step_height * direction
    for obj in cubes():
        obj.location.z += amount
    repaint_from_z(context)


def mirror_lr(left_source=True):
    a = cubes()
    for r in range(ROWS):
        for c in range(COLS//2):
            left, right = c, COLS-1-c
            src,dst = (left,right) if left_source else (right,left)
            set_color(a[index(r,dst)], a[index(r,src)].color[:3])

def mirror_tb(top_source=True):
    a = cubes()
    for c in range(COLS):
        for r in range(ROWS//2):
            bottom,top = r,ROWS-1-r
            src,dst = (top,bottom) if top_source else (bottom,top)
            set_color(a[index(dst,c)], a[index(src,c)].color[:3])

def mirror_both():
    a=cubes()
    for r in range(ROWS//2,ROWS):
        rr=ROWS-1-r
        for c in range(COLS//2):
            cc=COLS-1-c; v=a[index(r,c)].color[:3]
            set_color(a[index(r,cc)],v); set_color(a[index(rr,c)],v); set_color(a[index(rr,cc)],v)

class Build(bpy.types.Operator):
    bl_idname="wj150.build_default_cubes"; bl_label="Build 150 x 50 Cube Grid"
    def execute(self,context): build_grid(context); return {'FINISHED'}
class Clear(bpy.types.Operator):
    bl_idname="wj150.clear_default_cubes"; bl_label="Clear and Reset Row"
    def execute(self,context): clear_grid_colors(context); return {'FINISHED'}
class Auto(bpy.types.Operator):
    bl_idname="wj150.auto150_row"; bl_label="Auto150 Next Y Row"
    mode:bpy.props.EnumProperty(items=[('A','A',''),('B','B',''),('C','C','')])
    def execute(self,context): return {'FINISHED'} if auto150_row(context,self.mode) else {'CANCELLED'}
class RandomZ(bpy.types.Operator):
    bl_idname="wj150.random_z_columns"; bl_label="Paint Random Signed Z"
    mode:bpy.props.EnumProperty(items=[('CUBE','Each Cube +/- Z',''),('COLUMN','Each Column +/- Z','')])
    def execute(self,context):
        ok = random_signed_z(context) if self.mode == 'CUBE' else random_signed_z_by_column(context)
        return {'FINISHED'} if ok else {'CANCELLED'}

class ResetZ(bpy.types.Operator):
    bl_idname="wj150.reset_z"; bl_label="Flatten Z"
    def execute(self,context): reset_z(context); return {'FINISHED'}

class NudgeZ(bpy.types.Operator):
    bl_idname="wj150.nudge_z"; bl_label="Move Entire Grid Z"
    direction:bpy.props.IntProperty(default=1)
    def execute(self,context):
        if not cubes(): return {'CANCELLED'}
        nudge_all_z(context, self.direction)
        return {'FINISHED'}

class RepaintZ(bpy.types.Operator):
    bl_idname="wj150.repaint_z"; bl_label="Repaint from Z Heights"
    def execute(self,context): repaint_from_z(context); return {'FINISHED'}

class Symmetry(bpy.types.Operator):
    bl_idname="wj150.symmetry_default_cubes"; bl_label="Cube Grid Symmetry"
    mode:bpy.props.EnumProperty(items=[('LR','LR',''),('RL','RL',''),('TB','TB',''),('BT','BT',''),('BOTH','BOTH','')])
    def execute(self,context):
        if not cubes(): return {'CANCELLED'}
        {'LR':lambda:mirror_lr(True),'RL':lambda:mirror_lr(False),'TB':lambda:mirror_tb(True),'BT':lambda:mirror_tb(False),'BOTH':mirror_both}[self.mode]()
        force_object_color(context); return {'FINISHED'}

class Panel(bpy.types.Panel):
    bl_label="WJ150 Painted Z Cubes"; bl_idname="WJ150_PT_DEFAULT_CUBES"
    bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category='WJ150'
    def draw(self,context):
        l,s=self.layout,context.scene
        b=l.box(); b.label(text="Blender-Style Cube Grid",icon='CUBE'); b.operator("wj150.build_default_cubes"); b.operator("wj150.clear_default_cubes")
        b=l.box(); b.label(text="Auto150: Next Row Up Y"); b.prop(s,"wj150_color",text="Row Color"); b.label(text=f"Next Y row: {s.wj150_next_row + 1} / {ROWS}")
        row=b.row(align=True)
        for mode in 'ABC':
            op=row.operator("wj150.auto150_row",text=f"Auto {mode}150"); op.mode=mode
        b.label(text="Each press colors one full 150-cube row.",icon='INFO')
        b=l.box(); b.label(text="Painted Z- / Z+ Solid View",icon='CUBE')
        b.prop(s,"wj150_z_steps",text="Max +/- Z Steps")
        b.prop(s,"wj150_z_step_height",text="Z Step Size")
        b.prop(s,"wj150_z_minus_color",text="Z- Color")
        b.prop(s,"wj150_z_plus_color",text="Z+ Color")
        row=b.row(align=True)
        op=row.operator("wj150.nudge_z",text="Z -"); op.direction=-1
        op=row.operator("wj150.nudge_z",text="Z +"); op.direction=1
        row=b.row(align=True)
        op=row.operator("wj150.random_z_columns",text="Random +/- Z Cubes"); op.mode='CUBE'
        op=row.operator("wj150.random_z_columns",text="Random +/- Z Columns"); op.mode='COLUMN'
        b.operator("wj150.repaint_z",text="Repaint from Z Heights")
        b.operator("wj150.reset_z",text="Flatten Back to Z = 0")
        b.label(text="Only Z changes. X/Y grid stays locked.",icon='INFO')
        b=l.box(); b.label(text="Symmetry",icon='MOD_MIRROR')
        for pair in [[('LR','Left -> Right'),('RL','Right -> Left')],[('TB','Top -> Bottom'),('BT','Bottom -> Top')]]:
            row=b.row(align=True)
            for mode,text in pair: op=row.operator("wj150.symmetry_default_cubes",text=text); op.mode=mode
        op=b.operator("wj150.symmetry_default_cubes",text="Mirror Both Directions"); op.mode='BOTH'

CLASSES=(Build,Clear,Auto,RandomZ,ResetZ,NudgeZ,RepaintZ,Symmetry,Panel)
def register():
    for cls in CLASSES: bpy.utils.register_class(cls)
    bpy.types.Scene.wj150_color=bpy.props.FloatVectorProperty(name="Row Color",subtype='COLOR',size=3,default=(0.05,0.35,1.0),min=0,max=1)
    bpy.types.Scene.wj150_next_row=bpy.props.IntProperty(name="Next Y Row",default=0,min=0,max=ROWS-1)
    bpy.types.Scene.wj150_z_steps=bpy.props.IntProperty(name="Max Z Steps",default=10,min=0,max=100)
    bpy.types.Scene.wj150_z_step_height=bpy.props.FloatProperty(name="Z Step Height",default=5.0,min=0.01,max=100.0)
    bpy.types.Scene.wj150_z_minus_color=bpy.props.FloatVectorProperty(name="Z- Color",subtype='COLOR',size=3,default=(0.08,0.15,1.0),min=0,max=1)
    bpy.types.Scene.wj150_z_plus_color=bpy.props.FloatVectorProperty(name="Z+ Color",subtype='COLOR',size=3,default=(1.0,0.12,0.03),min=0,max=1)
def unregister():
    del bpy.types.Scene.wj150_color; del bpy.types.Scene.wj150_next_row; del bpy.types.Scene.wj150_z_steps; del bpy.types.Scene.wj150_z_step_height; del bpy.types.Scene.wj150_z_minus_color; del bpy.types.Scene.wj150_z_plus_color
    for cls in reversed(CLASSES): bpy.utils.unregister_class(cls)
if __name__=='__main__':
    register(); build_grid(bpy.context)
