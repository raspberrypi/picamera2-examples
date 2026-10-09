#!/usr/bin/python3

# How to do digital zoom using the "ScalerCrop" control.

import time

from picamera2 import Picamera2, Preview

picam2 = Picamera2()
picam2.start_preview(Preview.QTGL)

preview_config = picam2.create_preview_configuration()
picam2.configure(preview_config)

# The default crop is the largest aspect-ratio preserving size allowed by the camera mode.
crop = picam2.camera_controls['ScalerCrop'][2]

picam2.start()
time.sleep(2)

for _ in range(20):
    # This syncs us to the arrival of a new camera frame:
    picam2.capture_metadata()

    # Zoom in on 95% of what we had before. To stay centred, half of what we skip becomes "offset".
    crop = [crop[0] + 0.025 * crop[2], crop[1] + 0.025 * crop[3], 0.95 * crop[2], 0.95 * crop[3]]
    picam2.set_controls({"ScalerCrop": [round(x) for x in crop]})

time.sleep(2)
