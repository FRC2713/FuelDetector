# Raspberry Pi 5: start FuelDetector automatically at boot

This guide is for someone who is comfortable in the terminal (navigating folders, using `sudo`, editing a file) but may be new to **systemd** (the Linux service manager). Follow the steps in order.

**What you get:** After a reboot, the Pi runs two programs in the background:

1. **`main.py`** — Hailo + USB camera → publishes fuel detections to NetworkTables (`fuelDetector/fuelData`).
2. **`fuelgrid.py`** — reads those detections → publishes `clusterHeading` and `totalFuel`.

**Scope:** This is only for the **Pi AI Kit (Hailo + USB camera)** path. It does not set up Ultralytics, `visual.py`, or `rpi.py`.

---

## 1. Before you start (checklist)

Do these **once** on the Pi (or confirm they already work):

| Step | What to check |
|------|----------------|
| A | Hailo software is installed the way your team already uses for `main.py` (examples repo or hailo-apps). You know the path to **`setup_env.sh`**. |
| B | From a terminal, after sourcing that script, `python main.py` runs without errors (camera plugged in). |
| C | File **`yolov11n.hef`** is in the FuelDetector folder (or you know its full path). |
| D | Python can import **`ntcore`**. If not: activate the same environment you use for Hailo, then run `pip install ntcore`. |
| E | Your Linux user can use the camera. Run: `sudo usermod -aG video YOUR_USERNAME` then **log out and back in** (replace `YOUR_USERNAME` with your login name, e.g. `frc2713`). |

**NetworkTables:** The code tries the robot at `10.27.13.2`, then may fall back to localhost. The robot (or another NT server) must be reachable when you care about live data.

---

## 2. Big picture (why two “services”?)

- **systemd** can start programs at boot and restart them if they crash.
- Running **two separate systemd services** (one for `main.py`, one for `fuelgrid.py`) is clearer than one script that backgrounds a process: you get separate logs and reliable stop/start behavior.
- Hailo needs many environment variables (`GST_PLUGIN_PATH`, etc.). A small **wrapper script** runs `source setup_env.sh` for you so you do not paste dozens of lines into systemd.

---

## 3. Paths you must know

Write these down (use `pwd` and `ls` to find them):

1. **`FUEL_REPO`** — Full path to the FuelDetector git repo (directory that contains `main.py`).
2. **`HAILO_SETUP`** — Full path to Hailo’s `setup_env.sh`.
3. **`PYTHON`** — Full path to the **Python interpreter** that works with Hailo (often inside a virtualenv), e.g. `.../venv/hailo/bin/python`.

Example (yours will differ):

```text
FUEL_REPO=/home/frc2713/FuelDetector
HAILO_SETUP=/home/frc2713/hailo-rpi5-examples/setup_env.sh
PYTHON=/home/frc2713/hailo-rpi5-examples/venv/hailo/bin/python
```

---

## 4. Create `/etc/default/fueldetector`

This file holds **your** paths. systemd and the scripts read it.

1. Open a terminal on the Pi.
2. Create the file:

   ```bash
   sudo nano /etc/default/fueldetector
   ```

3. Paste the block below, **edit every path and username**, save (Ctrl+O, Enter) and exit (Ctrl+X).

```bash
# FuelDetector — paths for YOUR Pi (required)
FUEL_REPO=/home/YOUR_USERNAME/FuelDetector
HAILO_SETUP=/home/YOUR_USERNAME/path/to/setup_env.sh
PYTHON=/home/YOUR_USERNAME/path/to/hailo-venv/bin/python

# Wait up to 30s at boot for this device before starting the detector
FUEL_CAMERA_DEVICE=/dev/video0

# Optional: main.py already reads these if exported (see project README)
# export FUEL_CAMERA=/dev/video0
# export FUEL_HEF_PATH=/home/YOUR_USERNAME/FuelDetector/yolov11n.hef
# export HAILO_ENV_FILE=/usr/local/hailo/resources/.env
# export FUEL_TRACKER_CLASS_ID=0
```

4. Lock down permissions (good habit):

   ```bash
   sudo chmod 644 /etc/default/fueldetector
   ```

---

## 5. Install the wrapper script `fueldetector-run`

This script loads `/etc/default/fueldetector`, sources Hailo’s environment, `cd`s to the repo, and runs Python.

1. Create the file:

   ```bash
   sudo nano /usr/local/bin/fueldetector-run
   ```

2. Paste **exactly**:

```bash
#!/bin/bash
set -euo pipefail

if [[ ! -r /etc/default/fueldetector ]]; then
  echo "fueldetector-run: missing or unreadable /etc/default/fueldetector" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source /etc/default/fueldetector
set +a

if [[ -z "${FUEL_REPO:-}" || -z "${HAILO_SETUP:-}" || -z "${PYTHON:-}" ]]; then
  echo "fueldetector-run: set FUEL_REPO, HAILO_SETUP, and PYTHON in /etc/default/fueldetector" >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$HAILO_SETUP"
cd "$FUEL_REPO"
exec "$PYTHON" "$@"
```

3. Make it executable:

   ```bash
   sudo chmod +x /usr/local/bin/fueldetector-run
   ```

4. Quick manual test (should start the detector; Ctrl+C to stop):

   ```bash
   fueldetector-run main.py
   ```

   If that fails, fix paths in `/etc/default/fueldetector` before continuing.

---

## 6. Install the camera wait script (recommended)

USB cameras sometimes appear a few seconds after boot. This script waits up to 30 seconds for the device file.

1. Create the file:

   ```bash
   sudo nano /usr/local/bin/fueldetector-wait-camera
   ```

2. Paste **exactly**:

```bash
#!/bin/bash
set -euo pipefail

if [[ ! -r /etc/default/fueldetector ]]; then
  exit 1
fi

set -a
# shellcheck disable=SC1091
source /etc/default/fueldetector
set +a

dev="${FUEL_CAMERA_DEVICE:-/dev/video0}"
for _ in $(seq 1 30); do
  if [[ -e "$dev" ]]; then
    exit 0
  fi
  sleep 1
done

echo "fueldetector-wait-camera: timed out waiting for $dev" >&2
exit 1
```

3. Make it executable:

   ```bash
   sudo chmod +x /usr/local/bin/fueldetector-wait-camera
   ```

**If your camera is not `/dev/video0`**, set `FUEL_CAMERA_DEVICE` (and usually `FUEL_CAMERA`) in `/etc/default/fueldetector`. You can list devices with:

```bash
v4l2-ctl --list-devices
```

---

## 7. Install systemd unit files

Replace **`YOUR_USERNAME`** in both `[Service]` sections with your Linux login name (the same user that owns the repo and can use the camera).

### 7a. `fueldetector-cluster.service`

```bash
sudo nano /etc/systemd/system/fueldetector-cluster.service
```

Paste:

```ini
[Unit]
Description=FuelDetector cluster processor (fuelgrid.py)
After=network-online.target
Wants=network-online.target
PartOf=fueldetector.target

[Service]
Type=simple
User=YOUR_USERNAME
SupplementaryGroups=video
ExecStart=/usr/local/bin/fueldetector-run fuelgrid.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=fueldetector.target
```

### 7b. `fueldetector-detect.service`

```bash
sudo nano /etc/systemd/system/fueldetector-detect.service
```

Paste:

```ini
[Unit]
Description=FuelDetector Hailo detector (main.py)
After=network-online.target
Wants=network-online.target
PartOf=fueldetector.target

[Service]
Type=simple
User=YOUR_USERNAME
SupplementaryGroups=video
ExecStartPre=/usr/local/bin/fueldetector-wait-camera
ExecStart=/usr/local/bin/fueldetector-run main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=fueldetector.target
```

### 7c. `fueldetector.target`

```bash
sudo nano /etc/systemd/system/fueldetector.target
```

Paste:

```ini
[Unit]
Description=FuelDetector (detector + cluster)
Wants=network-online.target fueldetector-detect.service fueldetector-cluster.service
After=network-online.target

[Install]
WantedBy=multi-user.target
```

The two `Wants=` lines for the services make it obvious that starting this target starts both programs. (Enabling the services also adds them under `fueldetector.target.wants/`; the explicit `Wants=` keeps behavior clear if someone only `start`s the target.)

---

## 8. Enable and start (and turn on at every boot)

```bash
sudo systemctl daemon-reload
sudo systemctl enable fueldetector-detect.service fueldetector-cluster.service fueldetector.target
sudo systemctl start fueldetector.target
```

Check status:

```bash
systemctl status fueldetector-detect.service
systemctl status fueldetector-cluster.service
```

Follow logs (two terminals, or one combined):

```bash
journalctl -u fueldetector-detect.service -f
```

```bash
journalctl -u fueldetector-cluster.service -f
```

Or both at once:

```bash
journalctl -u fueldetector-detect.service -u fueldetector-cluster.service -f
```

**Reboot test:** `sudo reboot`. After login, run `systemctl status fueldetector-detect.service` again; both should be **active (running)**.

---

## 9. Stop or disable

```bash
sudo systemctl stop fueldetector.target
```

Turn off autostart:

```bash
sudo systemctl disable fueldetector-detect.service fueldetector-cluster.service fueldetector.target
```

---

## 10. Troubleshooting

| Symptom | Things to try |
|--------|----------------|
| Service fails immediately | Run `fueldetector-run main.py` manually; read the error. Check `FUEL_REPO`, `HAILO_SETUP`, `PYTHON` in `/etc/default/fueldetector`. |
| “Permission denied” on camera | Confirm `User=` in the unit matches your account; run `groups` and ensure **`video`** appears (after logout/login). |
| Camera wait times out | Wrong `FUEL_CAMERA_DEVICE` or camera not plugged in; use `v4l2-ctl --list-devices`. |
| NetworkTables empty / no robot | Ping roboRIO; confirm Pi and robot on same network. Code uses `10.27.13.2` by default (`ntinit.py`). |
| “Network online” too early | Rare on Pi OS: if NT connects only after a long delay, ask a mentor about `network-online.target` or a short delay (only after you see the problem). |

---

## 11. Optional improvements (later)

- **Different robot IP:** Today `ntinit.py` hardcodes `10.27.13.2`. Making that configurable would require a small code change.
- **Stable camera path:** Use a symlink under `/dev/v4l/by-id/` in `FUEL_CAMERA` / `FUEL_CAMERA_DEVICE` if the `videoN` number changes when you unplug devices.

---

## 12. Files this guide creates on the Pi

| Path | Role |
|------|------|
| `/etc/default/fueldetector` | Your paths and optional env vars |
| `/usr/local/bin/fueldetector-run` | Sources Hailo env, runs `python …` |
| `/usr/local/bin/fueldetector-wait-camera` | Waits for camera device |
| `/etc/systemd/system/fueldetector-*.service` | Service definitions |
| `/etc/systemd/system/fueldetector.target` | Starts both services at boot |

None of these replace your git repo; they live on the Pi’s system directories so you can still `git pull` FuelDetector normally.
