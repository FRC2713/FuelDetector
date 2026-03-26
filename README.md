# FuelDetector

Real-time FRC vision pipeline that detects fuel in camera frames, publishes detections to NetworkTables, and computes a heading toward the densest fuel cluster.

## Overview

This repository contains two logical stages:

1. **Detection stage**  
   Runs object detection on live camera input and publishes detections as a serialized string. On the **Raspberry Pi AI Kit**, `main.py` uses **Hailo GStreamer** with your compiled `yolov11n.hef` and a **USB camera**. For laptop debugging, use `visual.py` (Ultralytics + OpenCV) or `rpi.py` (Pi Camera Module + Ultralytics).

2. **Clustering/targeting stage**  
   Subscribes to detections, projects them into a grid, identifies the largest cluster, and publishes:
   - `clusterHeading` (degrees to turn toward the largest cluster)
   - `totalFuel` (count of accepted detections in the current frame)

All data is exchanged over the NetworkTables table `fuelDetector`.

## Architecture Breakdown

### Data flow

1. Camera frame is captured.
2. Inference runs on the frame (Hailo NPU in `main.py` on Pi AI Kit, or Ultralytics in other scripts) and returns bounding boxes + confidence.
3. Detections are published to `fuelDetector/fuelData` as:
   - `x_center,y_center,width,height,confidence;...`
4. Grid processor reads `fuelData`, filters detections by confidence threshold, and bins into a 2D grid.
5. Largest cluster is selected and converted to a heading using camera FOV.
6. Results are published:
   - `fuelDetector/clusterHeading`
   - `fuelDetector/totalFuel`

### Module map

- `main.py`  
  **Raspberry Pi AI Kit** detector: USB camera → Hailo GStreamer pipeline → `yolov11n.hef`. Publishes `fuelData`. Requires Hailo’s Python/GStreamer stack (see below).

- `visual.py`  
  Detector with OpenCV visualization window for debugging. Publishes `fuelData`.

- `rpi.py`  
  Raspberry Pi camera detector path using `picamera2`. Publishes `fuelData`.

- `fuelgrid.py`  
  Subscriber + clustering process. Publishes `clusterHeading` and `totalFuel`.

- `fuelcluster.py`  
  Helper class representing cluster aggregate state (`fuel_count`, average position).

- `ntinit.py`  
  NetworkTables setup helper. Tries robot address `10.27.13.2`, then localhost `127.0.0.1`.

## NetworkTables Topics

Table: `fuelDetector`

- `fuelData` (`string`, published by detector)
- `clusterHeading` (`double`, published by `fuelgrid.py`)
- `totalFuel` (`integer`, published by `fuelgrid.py`)
- `robotConnected` (`boolean`, expected to be provided by server/robot for connection detection)

## Requirements

- Python 3.10+ recommended
- A running NetworkTables server (robot or localhost)

### Raspberry Pi AI Kit (`main.py`)

- `yolov11n.hef` in the repository root (or pass `--hef-path`)
- USB camera (default device `/dev/video0`, or pass `--input` / use `usb` for auto-detect)
- Hailo software stack for Raspberry Pi: follow [Hailo RPi5 examples](https://github.com/hailo-ai/hailo-rpi5-examples) or [hailo-apps](https://github.com/hailo-ai/hailo-apps) installation so that:
  - `hailo` Python module and GStreamer plugins are available
  - `HAILO_ENV_FILE` points at your Hailo `.env` (default in code: `/usr/local/hailo/resources/.env`)
  - Typical workflow: `source setup_env.sh` from the Hailo examples repo, then run `main.py` from the same environment

Python packages for this path (usually provided by the Hailo venv + system packages):

- `ntcore`
- `PyGObject` (`gi`) for GStreamer
- Hailo’s `hailo_apps` package (`hailo_apps.python.*` or legacy `hailo_apps.hailo_app_python.*`)

### Desktop / legacy Ultralytics paths (`visual.py`, `rpi.py`)

- A trained YOLO weights file `best302.pt` in the repository root
- `ultralytics`, `ntcore`, `opencv-python` (`visual.py`)
- `picamera2` (`rpi.py`, Pi Camera Module)

## Setup

### Pi AI Kit (recommended for competition coprocessor)

1. Install the Hailo Raspberry Pi environment per Hailo’s docs (examples repo `install.sh` / `setup_env.sh`).
2. Copy or build `yolov11n.hef` into this repo root (same directory as `main.py`).
3. In the Hailo-enabled shell:

```bash
pip install ntcore   # if not already in that environment
```

Optional environment variables:

| Variable | Purpose |
|----------|---------|
| `HAILO_ENV_FILE` | Path to Hailo `.env` (overrides default) |
| `FUEL_HEF_PATH` | Default `.hef` path if you omit `--hef-path` |
| `FUEL_CAMERA` | Default camera (`/dev/video0` or `usb`) |
| `FUEL_TRACKER_CLASS_ID` | Hailo tracker class id (`-1` = all classes, `0` for single-class models) |

### Desktop / `visual.py` / `rpi.py`

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install ultralytics ntcore opencv-python
```

For Raspberry Pi camera support (CSI, not USB):

```bash
pip install picamera2
```

Place weights at:

```text
./best302.pt
```

## How To Run

Run the pipeline as **two processes**: detector + cluster processor.

### 1) Start detector process

**Raspberry Pi AI Kit + USB camera + Hailo** (from Hailo-configured shell):

```bash
source /path/to/hailo-rpi5-examples/setup_env.sh   # or your hailo-apps setup
cd /path/to/FuelDetector
python main.py
# Optional: python main.py --input /dev/video1 --hef-path ./yolov11n.hef --no-headless
```

`--no-headless` uses the normal video sink (e.g. monitor attached). Default is headless (`fakesink`) for coprocessor use.

Debug visualization (laptop / webcam, Ultralytics):

```bash
python visual.py
```

Raspberry Pi **CSI** camera + Ultralytics (`rpi.py`):

```bash
python rpi.py
```

### 2) Start cluster processor

In a second terminal:

```bash
python fuelgrid.py
```

This process continuously reads `fuelData` and publishes:

- `clusterHeading`
- `totalFuel`

## Typical Deployment Pattern

- Vision coprocessor runs `main.py` on **Pi AI Kit**, or `visual.py` / `rpi.py` for Ultralytics-based setups.
- Same or another process runs `fuelgrid.py`.
- Robot code reads `clusterHeading` and `totalFuel` from NetworkTables and uses them for aiming/intake decisions.

To start the **Pi AI Kit** pipeline (`main.py` + `fuelgrid.py`) automatically when the Pi boots, follow [docs/PI_BOOT_AUTOSTART.md](docs/PI_BOOT_AUTOSTART.md) (systemd, wrapper script, and config on the Pi).

## Operational Notes

- Detector confidence threshold is currently set in `fuelgrid.py`:
  - `FuelGrid.fuel_chance_threshold = 0.75`
- Grid size/FOV tuning is in `fuelgrid.py`:
  - `FuelGrid(12, 12, 60)`
- Camera geometry assumptions are:
  - `image_width = 640`
  - `image_height = 480`
- `ntinit.py` first attempts robot NT server (`10.27.13.2`) and then localhost.

## Troubleshooting

- **No NetworkTables connection**
  - Verify robot IP and subnet (`10.27.13.2`) or run local NT server.
  - Check whether `robotConnected` topic is present/updated by your server.

- **No detections**
  - **Hailo (`main.py`):** Confirm `yolov11n.hef` path, USB device (`v4l2-ctl --list-devices`), and that `HAILO_ENV_FILE` / `TAPPAS_POSTPROC_PATH` are set (source `setup_env.sh`). Try `--tracker-class-id 0` for a single-class model.
  - **Ultralytics:** Confirm `best302.pt` exists and camera index/source matches the model.

- **No heading updates**
  - Ensure `fuelgrid.py` is running in parallel with detector process.
  - Inspect `fuelData` topic to verify detections are being published.

- **Raspberry Pi script issues**
  - `rpi.py` may require validation/tweaks for frame capture order depending on environment.
- **`main.py` import errors on Pi**
  - Install/activate the Hailo examples or `hailo-apps` Python environment; `main.py` needs `hailo`, `gi.repository.Gst`, and `hailo_apps` detection pipelines.

## Repository Status

This repository currently has no lockfile/requirements file; dependency installation is manual as shown above.
