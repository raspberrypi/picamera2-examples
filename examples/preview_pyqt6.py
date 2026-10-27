#!/usr/bin/python3

# Show the standalone preview window using PyQt6 instead of the default PyQt5.
# The same can be done without changing the code by setting the environment
# variable PICAMERA2_QT_BINDING=PyQt6.

import time

try:
    import PyQt6  # noqa: F401
except ImportError:
    print("SKIPPED (no PyQt6)")
    quit()

from picamera2 import Picamera2, Preview

# This must be set before starting any Qt preview.
Picamera2.qt_binding = "PyQt6"

picam2 = Picamera2()
picam2.start_preview(Preview.QTGL)

preview_config = picam2.create_preview_configuration()
picam2.configure(preview_config)

picam2.start()
time.sleep(5)
