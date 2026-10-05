import time

from picamera2 import Picamera2, Preview
from picamera2.previews.drm_preview import list_devices as drm_list_devices

for disp in drm_list_devices():
    print(disp['device'], disp['resolution'], disp['pixel_formats'])

if len(Picamera2.global_camera_info()) <= 1:
    print("SKIPPED (one camera)")
    quit()

picam2a = Picamera2(0)
picam2a.start_preview(Preview.DRM, x=1000, y=0)
picam2a.start()
time.sleep(1)

picam2b = Picamera2(1)
picam2b.start_preview(Preview.DRM, x=1000, y=500)
picam2b.start()
time.sleep(1)

picam2a.close()
picam2a = Picamera2(0)
picam2a.start_preview(Preview.DRM, x=0, y=0)
picam2a.start()
time.sleep(1)

picam2b.close()
picam2b = Picamera2(1)
picam2b.start_preview(Preview.DRM, x=0, y=500)
picam2b.start()
time.sleep(1)
