import bpy
import math
import os

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 120

# Add cube
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = RotatingCube

# Animate rotation: 5 seconds (120 frames at 24 fps)
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path=rotation_euler, frame=1)

cube.rotation_euler = (math.radians(360), 0, math.radians(360))
cube.keyframe_insert(data_path=rotation_euler, frame=120)

# Linear interpolation
if cube.animation_data and cube.animation_data.action:
    for fcurve in cube.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'LINEAR'

# Camera
cam_data = bpy.data.cameras.new(Camera)
cam = bpy.data.objects.new(Camera, cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (4.5, -4.5, 3.5)
cam.rotation_euler = (math.radians(60), 0, math.radians(45))
scene.camera = cam

# Light
light_data = bpy.data.lights.new(name=SunLight, type='SUN')
light_data.energy = 4.0
light = bpy.data.objects.new(name=SunLight, object_data=light_data)
bpy.context.collection.objects.link(light)
light.location = (5.0, -2.0, 6.0)

# Render settings
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100

# Video output settings
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.filepath = os.path.abspath('rotating_cube_5s.mp4')

print('Starting animation render...')
bpy.ops.render.render(animation=True)
print('Animation render complete! File:', scene.render.filepath)