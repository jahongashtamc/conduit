import subprocess
import shutil
import os

ffmpeg = shutil.which('ffmpeg')
print('FFmpeg found:', ffmpeg)
if ffmpeg:
    cmd = [
        ffmpeg, '-y',
        '-framerate', '24',
        '-i', 'animation_5s/cube_frame_%04d.png',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        'rotating_cube_5s.mp4'
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print('Encoding return code:', res.returncode)
    if os.path.exists('rotating_cube_5s.mp4'):
        print('MP4 file created successfully! Size:', os.path.getsize('rotating_cube_5s.mp4'))