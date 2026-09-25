bl_info = {
    "name": "Writers Jumbler 150 Cubes",
    "author": "Shawn + Microsoft 365 Copilot",
    "version": (1, 7, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > WJ150",
    "description": "Centered 150x50 cube grid with row-spread Auto150 color and symmetry",
    "category": "3D View",
}

import bpy
import random

ROWS, COLS = 50, 150
CELL = 0.10
GAP = 0.025
DEPTH = 0.06
STEP = CELL + GAP
COLLECTION = "WJ150_CubeGrid"
MATERIAL = "WJ150_CubeColor"
CAMERA = "WJ150_TopCamera"


def idx(r, c): return r + c * ROWS


def cells():
    col = bpy.data.collections.get(COLLECTION)
    if not col: return []
    out = [o for o in col.objects if "wj150_index" in o]
    out.sort(key=lambda o: o["wj150_index"])
    return out


def set_color(o, rgb): o.color = (*map(float, rgb[:3]), 1.0)


def color(scene): return tuple(scene.wj150_color[:3])


def force_view(context):
    screen = getattr(context, "screen", None)
    if screen:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.shading.type = 'SOLID'
                area.spaces.active.shading.color_type = 'OBJECT'
                area.tag_redraw()
    context.view_layer.update()


def make_material():
    m = bpy.data.materials.get(MATERIAL) or bpy.data.materials.new(MATERIAL)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    info = n.new("ShaderNodeObjectInfo")
    l.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        l.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 0.18
    bsdf.inputs["Roughness"].default_value = 0.68
    l.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def cube_mesh():
    sx, sy, sz = CELL/2, CELL/2, DEPTH/2
    v = [(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),
         (-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)]
    f = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(4,0,3,7)]
    me = bpy.data.meshes.new("WJ150_CubeMesh")
    me.from_pydata(v, [], f); me.update()
    return me


def clear_grid():
    col = bpy.data.collections.get(COLLECTION)
    if col:
        for o in list(col.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(col)


def camera(scene):
    cam = bpy.data.objects.get(CAMERA)
    if not cam:
        data = bpy.data.cameras.new(CAMERA + "Data")
        cam = bpy.data.objects.new(CAMERA, data)
        scene.collection.objects.link(cam)
    cam.location = (0, 0, 22)
    cam.rotation_euler = (0, 0, 0)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = (ROWS-1)*STEP + CELL + 0.8
    scene.camera = cam


def build(context):
    clear_grid()
    scene = context.scene
    col = bpy.data.collections.new(COLLECTION); scene.collection.children.link(col)
    me, mat = cube_mesh(), make_material(); me.materials.append(mat)
    x0, y0 = -((COLS-1)*STEP)/2, -((ROWS-1)*STEP)/2
    for c in range(COLS):
        for r in range(ROWS):
            o = bpy.data.objects.new(f"WJ150_{r:02d}_{c:03d}", me)
            o.location = (x0+c*STEP, y0+r*STEP, 0)
            o.color = (0.035,0.035,0.035,1)
            o["wj150_index"], o["wj150_row"], o["wj150_col"] = idx(r,c), r,c
            col.objects.link(o)
    camera(scene); force_view(context)


def clear_colors(context):
    for o in cells(): set_color(o, (0.035,0.035,0.035))
    force_view(context)


def tint(rgb, amount):
    return tuple(max(0,min(1,x+amount)) for x in rgb)


def auto150_row_spread(scene, mode):
    """One seed row per column, then color spreads vertically by scene radius."""
    a = cells()
    if not a: return False
    base = color(scene)
    radius = scene.wj150_spread
    for c in range(COLS):
        seed = random.randrange(ROWS)
        for dr in range(-radius, radius+1):
            r = seed + dr
            if not 0 <= r < ROWS: continue
            distance = abs(dr)
            if mode == 'A':
                if dr != 0: continue
                cc = base
            elif mode == 'B':
                cc = tint(base, -0.055 * distance)
            else:
                cc = tint(base, random.uniform(-0.10,0.10) - 0.025*distance)
            set_color(a[idx(r,c)], cc)
    return True


def horizontal(src_left=True):
    a=cells()
    for r in range(ROWS):
        for c in range(COLS//2):
            left,right=c,COLS-1-c
            s,d=(left,right) if src_left else (right,left)
            set_color(a[idx(r,d)], a[idx(r,s)].color[:3])


def vertical(src_top=True):
    a=cells()
    for c in range(COLS):
        for r in range(ROWS//2):
            bottom,top=r,ROWS-1-r
            s,d=(top,bottom) if src_top else (bottom,top)
            set_color(a[idx(d,c)], a[idx(s,c)].color[:3])


def both():
    a=cells()
    for r in range(ROWS//2,ROWS):
        rr=ROWS-1-r
        for c in range(COLS//2):
            cc=COLS-1-c; v=a[idx(r,c)].color[:3]
            set_color(a[idx(r,cc)],v); set_color(a[idx(rr,c)],v); set_color(a[idx(rr,cc)],v)


class Build(bpy.types.Operator):
    bl_idname="wj150.build_cubes"; bl_label="Build Cube Grid"
    def execute(self,context): build(context); return {'FINISHED'}
class Clear(bpy.types.Operator):
    bl_idname="wj150.clear_cubes"; bl_label="Clear"
    def execute(self,context): clear_colors(context); return {'FINISHED'}
class Auto(bpy.types.Operator):
    bl_idname="wj150.auto150_cubes"; bl_label="Auto150"
    mode:bpy.props.EnumProperty(items=[('A','A',''),('B','B',''),('C','C','')])
    def execute(self,context):
        if not auto150_row_spread(context.scene,self.mode): return {'CANCELLED'}
        force_view(context); return {'FINISHED'}
class Sym(bpy.types.Operator):
    bl_idname="wj150.sym_cubes"; bl_label="Symmetry"
    mode:bpy.props.EnumProperty(items=[('LR','LR',''),('RL','RL',''),('TB','TB',''),('BT','BT',''),('BOTH','BOTH','')])
    def execute(self,context):
        if not cells(): return {'CANCELLED'}
        {'LR':lambda:horizontal(True),'RL':lambda:horizontal(False),'TB':lambda:vertical(True),'BT':lambda:vertical(False),'BOTH':both}[self.mode]()
        force_view(context); return {'FINISHED'}


class Panel(bpy.types.Panel):
    bl_label="Writers Jumbler 150 Cubes"; bl_idname="WJ150_PT_CUBES"
    bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category='WJ150'
    def draw(self,context):
        l=self.layout; s=context.scene
        b=l.box(); b.label(text="3D Cube Grid"); b.operator("wj150.build_cubes",icon='CUBE'); b.operator("wj150.clear_cubes")
        b=l.box(); b.label(text="Auto150 Row Spread"); b.prop(s,"wj150_color",text="Color"); b.prop(s,"wj150_spread",text="Spread Rows")
        row=b.row(align=True)
        for mode in 'ABC':
            op=row.operator("wj150.auto150_cubes",text=f"Auto {mode}150"); op.mode=mode
        b=l.box(); b.label(text="Symmetry")
        row=b.row(align=True)
        for mode,text in [('LR','Left -> Right'),('RL','Right -> Left')]: op=row.operator("wj150.sym_cubes",text=text); op.mode=mode
        row=b.row(align=True)
        for mode,text in [('TB','Top -> Bottom'),('BT','Bottom -> Top')]: op=row.operator("wj150.sym_cubes",text=text); op.mode=mode
        op=b.operator("wj150.sym_cubes",text="Mirror Both Directions",icon='MOD_MIRROR'); op.mode='BOTH'
        b=l.box(); b.label(text="Top stays visually flat; cubes show depth when view is tilted.",icon='INFO')


CLASSES=(Build,Clear,Auto,Sym,Panel)
def register():
    for c in CLASSES: bpy.utils.register_class(c)
    bpy.types.Scene.wj150_color=bpy.props.FloatVectorProperty(name="Color",subtype='COLOR',size=3,default=(0.05,0.35,1),min=0,max=1)
    bpy.types.Scene.wj150_spread=bpy.props.IntProperty(name="Spread Rows",default=3,min=0,max=24)
def unregister():
    del bpy.types.Scene.wj150_color; del bpy.types.Scene.wj150_spread
    for c in reversed(CLASSES): bpy.utils.unregister_class(c)
if __name__=='__main__':
    register(); build(bpy.context)
