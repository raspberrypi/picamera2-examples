# picamera2-examples

Examples, demo apps and the test suite for [Picamera2](https://github.com/raspberrypi/picamera2).

## Requirements

Picamera2 must already be installed with the following command:

```bash
sudo apt install python3-picamera2
```

## Running the tests

```bash
./run_tests.py
```

By default the runner uses the tests, examples and apps alongside this file,
runs each test in `/home/pi/picamera2_tests`, and reads the test list from
`tests/test_list_drm.txt` and `tests/test_list.txt`. Use `-p`, `-d` and `-t`
to override these; see `./run_tests.py --help`.
