#!/usr/bin/python3

# Test that we can read the sensor modes, and then configure the camera
# into each mode and get the correct framerate

import fcntl
import os
import time
from math import isclose

from libcamera import Transform
from videodev2 import (
    V4L2_CID_HFLIP,
    V4L2_CID_VFLIP,
    V4L2_CTRL_FLAG_MODIFY_LAYOUT,
    VIDIOC_QUERYCTRL,
    v4l2_queryctrl,
)

from picamera2 import Picamera2
from picamera2.sensor_format import SensorFormat


def flips_modify_layout(camera_id):
    # Find the sensor's subdevice from the camera id (its device tree path),
    # and report whether its flip controls change the Bayer order.
    for i in range(16):
        of_node = f"/sys/class/video4linux/v4l-subdev{i}/device/of_node"
        if not (os.path.islink(of_node) and camera_id in os.readlink(of_node)):
            continue
        with open(f"/dev/v4l-subdev{i}", "rb+", buffering=0) as fd:
            for cid in (V4L2_CID_HFLIP, V4L2_CID_VFLIP):
                ctrl = v4l2_queryctrl(id=cid)
                try:
                    fcntl.ioctl(fd, VIDIOC_QUERYCTRL, ctrl)
                except OSError:
                    continue
                if ctrl.flags & V4L2_CTRL_FLAG_MODIFY_LAYOUT:
                    return True
        return False
    # Sensor subdevice not found: assume the flips do change the Bayer order.
    return True


Picamera2.set_logging()
picam2 = Picamera2()
modify_layout = flips_modify_layout(picam2.camera.id)


def check(raw_config, fps):
    # Don't bother checking anything over 5MP, as that may cause buffer issues
    if raw_config["size"][0] * raw_config["size"][1] > 5e6:
        print("Not checking", raw_config)
        return
    picam2.video_configuration = picam2.create_video_configuration(raw=raw_config)
    picam2.configure("video")
    # Check we got the correct raw format
    camera_config = picam2.camera_configuration()
    assert camera_config["raw"]["size"] == raw_config["size"]
    set_format = SensorFormat(camera_config["raw"]["format"])
    requested_format = SensorFormat(raw_config["format"])
    # The sensor modes report the native Bayer order, so undo the flips that
    # correct the sensor's rotation -- but only if they change the Bayer order.
    if modify_layout:
        rotation = picam2.camera_properties["Rotation"]
        set_format.transform(Transform(rotation=rotation))
    # Bayer order should match, as should bit depth (taking it from the sensor config
    # if present). Insist that there either is packing of some form on both, or none.
    if 'sensor' in camera_config and camera_config['sensor'] is not None:
        if 'bit_depth' in camera_config['sensor']:
            set_format.bit_depth = camera_config['sensor']['bit_depth']
    assert (
        set_format.bayer_order == requested_format.bayer_order
        and set_format.bit_depth == requested_format.bit_depth
        and (set_format.packing == '') == (requested_format.packing == '')
    ), f'{picam2.camera_configuration()["raw"]["format"]} != {raw_config["format"]}'
    picam2.set_controls({"FrameRate": fps})
    picam2.start(show_preview=True)
    time.sleep(1)
    # Check we got roughly the right framerate
    metadata = picam2.capture_metadata()
    framerate = 1000000 / metadata["FrameDuration"]
    print(metadata)
    print(f"Framerate: {framerate:.2f}, requested: {fps:.2f}")
    assert isclose(framerate, fps, abs_tol=1.0)
    picam2.stop()


modes = picam2.sensor_modes
# Make sure less than 5 modes, to avoid timing out
modes = modes[:5]
for mode in modes:
    # Check packed mode works
    check({"size": mode["size"], "format": mode["format"].format}, mode["fps"])
    # Check unpacked mode works
    check({"size": mode["size"], "format": mode["unpacked"]}, mode["fps"])
