import bpy
import math
import os
import sys

# Set default keyframe interpolation to LINEAR for seamless constant spin
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 120

scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100

# Optimal EEVEE samples for crisp, fast rendering
scene.eevee.taa_render_samples = 16

# Setup Cube
cube = bpy.data.objects.get('Cube')
if not cube:
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = 'Cube'

# Bevel modifier for highlight edges
bev = cube.modifiers.get('Bevel')
if not bev:
    bev = cube.modifiers.new('Bevel', 'BEVEL')
bev.width = 0.08
bev.segments = 4

# Modern metallic cyan shader
mat = bpy.data.materials.get('CyberCyan')
if not mat:
    mat = bpy.data.materials.new('CyberCyan')
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.05, 0.65, 0.95, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.2
cube.data.materials.clear()
cube.data.materials.append(mat)

# 5-second 360-degree rotation animation (120 frames at 24fps)
cube.animation_data_clear()
cube.rotation_mode = 'XYZ'
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path='rotation_euler', frame=1)

cube.rotation_euler = (math.radians(360), 0, math.radians(360))
cube.keyframe_insert(data_path='rotation_euler', frame=120)

# Camera & Lights
cam = bpy.data.objects.get('Camera')
if cam:
    cam.location = (4.5, -4.5, 3.5)
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))

light = bpy.data.objects.get('Light')
if light:
    light.location = (4.0, -3.0, 6.0)
    light.data.energy = 2500.0

rim_light = bpy.data.objects.get('RimLight')
if not rim_light:
    rim_data = bpy.data.lights.new(name='RimLight', type='POINT')
    rim_data.energy = 1800.0
    rim_data.color = (1.0, 0.55, 0.15)
    rim_light = bpy.data.objects.new(name='RimLight', object_data=rim_data)
    scene.collection.objects.link(rim_light)
    rim_light.location = (-4.0, 4.0, -1.0)

# Render frames directory
ws_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
anim_dir = os.path.join(ws_dir, 'animation_5s')
os.makedirs(anim_dir, exist_ok=True)
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(anim_dir, 'cube_frame_')

print(f'Starting 5-second animation render (120 frames at 24fps) into: {anim_dir}', flush=True)
bpy.ops.render.render(animation=True)
print('Blender 120-frame animation sequence render completed successfully!', flush=True)
