"""Sculptor topshirig'i: Blender'da aylanayotgan kub, 5 sekund, 1080p, MP4.

Bu haqiqiy 3D sahna: kub, material, yorug'lik, kamera va 120 kadrlik
kalit-ramka animatsiyasi. Test-pattern emas — GPU/CPU EEVEE render.
"""
import bpy
import math
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES = 120          # 5 s * 24 fps
FPS = 24
RES = (1920, 1080)

# 1) Sahnani tozalash
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2) Kub
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "SpinningCube"

# 3) Silliq bevel — haqiqiy 3D ko'rinish
mod = cube.modifiers.new(name="Bevel", type="BEVEL")
mod.width = 0.06
mod.segments = 4

# 4) Material — aks ettiruvchi metall
mat = bpy.data.materials.new("CubeMetal")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.15, 0.45, 0.95, 1.0)
bsdf.inputs["Metallic"].default_value = 0.9
bsdf.inputs["Roughness"].default_value = 0.18
cube.data.materials.append(mat)

# 5) Yorug'lik
bpy.ops.object.light_add(type="AREA", location=(4, -4, 6))
key = bpy.context.active_object
key.data.energy = 1200
key.data.size = 6

bpy.ops.object.light_add(type="AREA", location=(-5, 3, 3))
fill = bpy.context.active_object
fill.data.energy = 400
fill.data.size = 8

# 6) Kamera
bpy.ops.object.camera_add(location=(6.5, -6.5, 4.2))
cam = bpy.context.active_object
bpy.context.scene.camera = cam
# Kamerani markazga qaratish
constraint = cam.constraints.new(type="TRACK_TO")
constraint.track_axis = "TRACK_NEGATIVE_Z"
constraint.up_axis = "UP_Y"
empty = bpy.data.objects.new("Target", None)
bpy.context.collection.objects.link(empty)
constraint.target = empty

# 7) Render sozlamalari — 1080p, 5 sekund
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FRAMES
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [
    e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
] else "BLENDER_EEVEE"
scene.render.film_transparent = False

# 8) Aylanish animatsiyasi — 360 daraja, butun 5 sekund davomida
cube.rotation_euler = (math.radians(20), 0, 0)
cube.keyframe_insert(data_path="rotation_euler", frame=1)
cube.rotation_euler = (math.radians(20), 0, math.radians(360))
cube.keyframe_insert(data_path="rotation_euler", frame=FRAMES)

# 9) PNG kadrlar (Blender 5.2 build'ida FFMPEG backend yo'q — FFmpeg keyin yig'adi)
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
frames_dir = os.path.join(OUT_DIR, "frames")
os.makedirs(frames_dir, exist_ok=True)
scene.render.filepath = os.path.join(frames_dir, "frame_")

print(f"[SCULPTOR] Render boshlanmoqda: {RES[0]}x{RES[1]}, {FRAMES} kadr, {FPS} fps")
bpy.ops.render.render(animation=True)
print(f"[SCULPTOR] KADRLAR TAYYOR: {frames_dir}")
