#!/usr/bin/python3

# Check that Picamera2.qt_binding selects the Qt binding used by the standalone
# previews and by the unqualified widget names, and that no other Qt binding gets
# imported. Each installed binding is tested in a subprocess where all the other
# bindings are made unimportable, as if they were not installed.

import importlib.util
import subprocess
import sys

BINDINGS = ("PyQt5", "PyQt6", "PySide2", "PySide6")
EXPLICIT_NAMES = {"PyQt5": "Q5Picamera2", "PyQt6": "Q6Picamera2", "PySide2": "QSide2Picamera2", "PySide6": "QSide6Picamera2"}

CHILD = """
import sys
binding, preview = sys.argv[1], sys.argv[2]
for other in {bindings}:
    if other != binding:
        sys.modules[other] = None

from picamera2 import Picamera2, Preview

Picamera2.qt_binding = binding
from picamera2.previews import qt

assert qt.QPicamera2 is getattr(qt, {names}[binding]), "QPicamera2 does not match the default binding"

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start_preview(getattr(Preview, preview))
picam2.start()
for _ in range(10):
    picam2.capture_metadata()
picam2.close()

loaded = {{name.split('.')[0] for name, mod in sys.modules.items() if mod is not None and name.split('.')[0] in {bindings}}}
assert loaded == {{binding}}, f"Unexpected Qt bindings imported: {{loaded}}"
""".format(bindings=BINDINGS, names=EXPLICIT_NAMES)

# Check how the default binding is chosen, without needing the camera. Each case gives the
# binding to import first (or None), the value for Picamera2.qt_binding (or None), the
# PICAMERA2_QT_BINDING environment variable (or None), and the binding that should result.
RESOLVE = """
import os
import sys
imported, attr, env, expected = [None if arg == "None" else arg for arg in sys.argv[1:]]
if env:
    os.environ["PICAMERA2_QT_BINDING"] = env
if imported:
    __import__(imported + ".QtCore")

from picamera2 import Picamera2

if attr:
    Picamera2.qt_binding = attr
from picamera2.previews import qt

got = Picamera2.get_qt_binding()
assert got == expected, f"Got {{got}}, expected {{expected}}"
assert qt.QPicamera2 is getattr(qt, {names}[expected]), "QPicamera2 does not match the default binding"
""".format(names=EXPLICIT_NAMES)

failures = 0
tested = 0
installed = [binding for binding in BINDINGS if importlib.util.find_spec(binding) is not None]
other = installed[-1] if installed else None
for case in (
    (None, None, None, "PyQt5"),  # nothing imported or set: PyQt5
    (None, None, other, other),  # environment variable
    (other, None, None, other),  # detect the binding the application imported
    (other, None, "PyQt5", other),  # detection beats the environment variable
    (None, other, "PyQt5", other),  # Picamera2.qt_binding beats the environment variable
):
    if None in case[3:] or (case[3] not in installed):
        continue
    result = subprocess.run([sys.executable, "-c", RESOLVE, *map(str, case)], capture_output=True, text=True)
    if result.returncode == 0:
        print("Resolve", case, "OK")
    else:
        failures += 1
        print("Resolve", case, "FAILED")
        print(result.stderr[-2000:])

for binding in BINDINGS:
    if importlib.util.find_spec(binding) is None:
        print(binding, "not installed, skipping")
        continue
    for preview in ("QT", "QTGL"):
        tested += 1
        result = subprocess.run([sys.executable, "-c", CHILD, binding, preview], capture_output=True, text=True)
        if result.returncode == 0:
            print(binding, preview, "OK")
        else:
            failures += 1
            print(binding, preview, "FAILED with return code", result.returncode)
            print(result.stderr[-2000:])

if tested == 0:
    print("SKIPPED (no Qt bindings)")
    quit()

if failures:
    print("ERROR:", failures, "failures")
    sys.exit(1)
