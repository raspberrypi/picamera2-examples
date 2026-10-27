#!/usr/bin/python3

# Check that the unqualified QGlPicamera2 widget uses whichever Qt binding the
# application has already imported. The binding comes from the command line
# (e.g. "app_qtgl_binding.py PySide6"), or the PICAMERA2_QT_BINDING environment
# variable, otherwise PyQt6.

import importlib
import os
import sys

binding = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PICAMERA2_QT_BINDING", "PyQt6")
try:
    QtCore = importlib.import_module(binding + ".QtCore")
    QtWidgets = importlib.import_module(binding + ".QtWidgets")
except ImportError:
    print(f"SKIPPED (no {binding})")
    quit()

from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2, is_wayland_gl_widget

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())

app = QtWidgets.QApplication([])

widget = QGlPicamera2(picam2, width=640, height=480)
widget.setWindowTitle(f"QtGL {Picamera2.get_qt_binding()}")
widget.show()
picam2.start()

expected_wayland = app.platformName() == 'wayland'


def check_and_quit():
    if Picamera2.get_qt_binding() != binding or not isinstance(widget, QtWidgets.QWidget):
        print(f"ERROR: widget does not use {binding}")
    got_wayland = is_wayland_gl_widget(widget)
    if got_wayland != expected_wayland:
        platform = "Wayland" if expected_wayland else "X11"
        print(f"ERROR: expected {platform} widget ({binding} active platform)")
    app.quit()


QtCore.QTimer.singleShot(3000, check_and_quit)
app.exec()
