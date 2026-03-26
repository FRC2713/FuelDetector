"""
Fuel detector for Raspberry Pi AI Kit (Hailo): USB camera -> yolov11n.hef -> NetworkTables.

Requires a Pi environment with hailo-apps installed and its setup_env.sh sourced.
See README.md for setup.

Preserves the legacy `fuelData` format: x_center,y_center,width,height,confidence;...
(pixel coordinates, matching fuelgrid.py expectations for 640x480).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# --- Fuel-specific CLI (parsed before Hailo re-parses sys.argv) ----------------


def _parse_fuel_argv() -> tuple[argparse.Namespace, list[str]]:
    repo_root = Path(__file__).resolve().parent
    default_hef = repo_root / "yolov11n.hef"

    p = argparse.ArgumentParser(
        description="FuelDetector on Raspberry Pi AI Kit (Hailo + USB camera).",
    )
    p.add_argument(
        "--hef-path",
        "-n",
        default=os.environ.get("FUEL_HEF_PATH", str(default_hef)),
        help="Path to compiled .hef model (default: ./yolov11n.hef or $FUEL_HEF_PATH).",
    )
    p.add_argument(
        "--input",
        "-i",
        default=os.environ.get("FUEL_CAMERA", "/dev/video0"),
        help="USB camera device (e.g. /dev/video0) or 'usb' for auto-detect.",
    )
    p.add_argument(
        "--hailo-env",
        default=os.environ.get(
            "HAILO_ENV_FILE", "/usr/local/hailo/resources/.env"
        ),
        help="Path to Hailo .env file (sets TAPPAS paths). Loaded by hailo-apps setup_env.sh. Default: /usr/local/hailo/resources/.env",
    )
    p.add_argument(
        "--width",
        "-W",
        type=int,
        default=int(os.environ.get("FUEL_FRAME_WIDTH", "640")),
        help="Capture width (default 640; fuelgrid.py assumes 640).",
    )
    p.add_argument(
        "--height",
        "-H",
        type=int,
        default=int(os.environ.get("FUEL_FRAME_HEIGHT", "480")),
        help="Capture height (default 480; fuelgrid.py assumes 480).",
    )
    p.add_argument(
        "--frame-rate",
        "-f",
        type=int,
        default=int(os.environ.get("FUEL_FRAME_RATE", "30")),
        help="USB camera frame rate cap (default 30).",
    )
    p.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use fakesink for video (default true for coprocessor / no display).",
    )
    p.add_argument(
        "--tracker-class-id",
        type=int,
        default=int(os.environ.get("FUEL_TRACKER_CLASS_ID", "-1")),
        help="Hailo tracker class-id (-1 = all classes; use 0 for single-class models).",
    )
    known, rest = p.parse_known_args()
    return known, rest


def _bbox_to_xywh_pixels(bbox, frame_w: int | None, frame_h: int | None) -> tuple[float, float, float, float]:
    """Convert Hailo bbox to center-x, center-y, width, height in pixels."""
    xmin, ymin, xmax, ymax = bbox.xmin(), bbox.ymin(), bbox.xmax(), bbox.ymax()
    fw = float(frame_w or 640)
    fh = float(frame_h or 480)
    # Heuristic: Hailo bbox values are usually normalized when max <= ~1
    if max(xmax, ymax, xmin, ymin) <= 1.5:
        xmin, xmax = xmin * fw, xmax * fw
        ymin, ymax = ymin * fh, ymax * fh
    w = max(0.0, xmax - xmin)
    h = max(0.0, ymax - ymin)
    xc = xmin + w / 2.0
    yc = ymin + h / 2.0
    return xc, yc, w, h


def _import_hailo_stack():
    """Import hailo-apps (hailo_apps.python.*) detection pipeline modules."""
    det_m = "hailo_apps.python.pipeline_apps.detection.detection_pipeline"
    gst_m = "hailo_apps.python.core.gstreamer.gstreamer_app"
    buf_m = "hailo_apps.python.core.common.buffer_utils"
    hp_m = "hailo_apps.python.core.gstreamer.gstreamer_helper_pipelines"
    core_m = "hailo_apps.python.core.common.core"
    try:
        det = __import__(det_m, fromlist=["GStreamerDetectionApp"])
        gst = __import__(gst_m, fromlist=["app_callback_class"])
        buf = __import__(buf_m, fromlist=["get_caps_from_pad"])
        hp = __import__(
            hp_m,
            fromlist=[
                "DISPLAY_PIPELINE",
                "INFERENCE_PIPELINE",
                "INFERENCE_PIPELINE_WRAPPER",
                "SOURCE_PIPELINE",
                "TRACKER_PIPELINE",
                "USER_CALLBACK_PIPELINE",
            ],
        )
        cor = __import__(core_m, fromlist=["get_pipeline_parser"])
        return {
            "GStreamerDetectionApp": det.GStreamerDetectionApp,
            "app_callback_class": gst.app_callback_class,
            "get_caps_from_pad": buf.get_caps_from_pad,
            "DISPLAY_PIPELINE": hp.DISPLAY_PIPELINE,
            "INFERENCE_PIPELINE": hp.INFERENCE_PIPELINE,
            "INFERENCE_PIPELINE_WRAPPER": hp.INFERENCE_PIPELINE_WRAPPER,
            "SOURCE_PIPELINE": hp.SOURCE_PIPELINE,
            "TRACKER_PIPELINE": hp.TRACKER_PIPELINE,
            "USER_CALLBACK_PIPELINE": hp.USER_CALLBACK_PIPELINE,
            "get_pipeline_parser": cor.get_pipeline_parser,
        }
    except ImportError as e:
        raise ImportError(
            f"Could not import hailo-apps detection stack ({det_m}): {e}\n"
            "Install hailo-apps and source its setup_env.sh before running."
        ) from e


def _build_hailo_argv(fuel: argparse.Namespace, passthrough: list[str]) -> list[str]:
    hef = str(Path(fuel.hef_path).expanduser().resolve())
    argv = [
        sys.argv[0],
        "--input",
        fuel.input,
        "--hef-path",
        hef,
        "--width",
        str(fuel.width),
        "--height",
        str(fuel.height),
        "--frame-rate",
        str(fuel.frame_rate),
        "--disable-sync",
    ]
    argv.extend(passthrough)
    return argv


def main() -> None:
    fuel, passthrough = _parse_fuel_argv()

    if not Path(fuel.hef_path).expanduser().is_file():
        print(f"ERROR: HEF not found: {fuel.hef_path}", file=sys.stderr)
        sys.exit(1)

    os.environ["HAILO_ENV_FILE"] = str(Path(fuel.hailo_env).expanduser())
    sys.argv = _build_hailo_argv(fuel, passthrough)

    import gi

    gi.require_version("Gst", "1.0")
    from gi.repository import Gst  # noqa: F401 — registers GStreamer

    import hailo

    stack = _import_hailo_stack()
    GStreamerDetectionApp = stack["GStreamerDetectionApp"]
    app_callback_class = stack["app_callback_class"]
    get_caps_from_pad = stack["get_caps_from_pad"]
    SOURCE_PIPELINE = stack["SOURCE_PIPELINE"]
    INFERENCE_PIPELINE = stack["INFERENCE_PIPELINE"]
    INFERENCE_PIPELINE_WRAPPER = stack["INFERENCE_PIPELINE_WRAPPER"]
    TRACKER_PIPELINE = stack["TRACKER_PIPELINE"]
    USER_CALLBACK_PIPELINE = stack["USER_CALLBACK_PIPELINE"]
    DISPLAY_PIPELINE = stack["DISPLAY_PIPELINE"]
    get_pipeline_parser = stack["get_pipeline_parser"]

    try:
        from hailo_apps.python.core.common.hailo_logger import get_logger
        hailo_logger = get_logger("fueldetector.main")
    except ImportError:
        import logging
        hailo_logger = logging.getLogger("fueldetector.main")

    import ntinit

    inst = ntinit.getNT("detectorClient")
    time.sleep(1)
    fuel_table = inst.getTable("fuelDetector")
    fuel_publish = fuel_table.getStringTopic("fuelData").publish()

    class FuelUserData(app_callback_class):
        def __init__(self):
            super().__init__()
            self.fuel_publish = fuel_publish

    class FuelDetectorHailoApp(GStreamerDetectionApp):
        """Same as upstream detection app but tracker class-id matches custom single-class models."""

        def __init__(self, app_callback, user_data, parser=None, *, headless: bool, tracker_class_id: int):
            self._fuel_headless = headless
            self._fuel_tracker_class_id = tracker_class_id
            if parser is None:
                parser = get_pipeline_parser()
            super().__init__(app_callback, user_data, parser=parser)

        def get_pipeline_string(self):
            source_pipeline = SOURCE_PIPELINE(
                video_source=self.video_source,
                video_width=self.video_width,
                video_height=self.video_height,
                frame_rate=self.frame_rate,
                sync=self.sync,
            )
            detection_pipeline = INFERENCE_PIPELINE(
                hef_path=self.hef_path,
                post_process_so=self.post_process_so,
                post_function_name=self.post_function_name,
                batch_size=self.batch_size,
                config_json=self.labels_json,
                additional_params=self.thresholds_str,
            )
            detection_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(detection_pipeline)
            tracker_pipeline = TRACKER_PIPELINE(class_id=self._fuel_tracker_class_id)
            user_callback_pipeline = USER_CALLBACK_PIPELINE()
            video_sink = "fakesink" if self._fuel_headless else self.video_sink
            display_pipeline = DISPLAY_PIPELINE(
                video_sink=video_sink, sync=self.sync, show_fps=self.show_fps
            )
            pipeline_string = (
                f"{source_pipeline} ! "
                f"{detection_pipeline_wrapper} ! "
                f"{tracker_pipeline} ! "
                f"{user_callback_pipeline} ! "
                f"{display_pipeline}"
            )
            hailo_logger.debug("Fuel pipeline string: %s", pipeline_string)
            return pipeline_string

    def app_callback(pad, info, user_data):
        buffer = info.get_buffer()
        if buffer is None:
            return Gst.PadProbeReturn.OK

        fmt, width, height = get_caps_from_pad(pad)
        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

        box_string = ""
        for det in detections:
            bbox = det.get_bbox()
            conf = float(det.get_confidence())
            xc, yc, w, h = _bbox_to_xywh_pixels(bbox, width, height)
            box_string += f"{xc},{yc},{w},{h},{conf};"

        user_data.fuel_publish.set(box_string)
        return Gst.PadProbeReturn.OK

    user_data = FuelUserData()
    app = FuelDetectorHailoApp(
        app_callback,
        user_data,
        headless=fuel.headless,
        tracker_class_id=fuel.tracker_class_id,
    )
    print(
        f"FuelDetector: HEF={fuel.hef_path} input={fuel.input} "
        f"{fuel.width}x{fuel.height}@{fuel.frame_rate} headless={fuel.headless} "
        f"tracker_class_id={fuel.tracker_class_id}",
        flush=True,
    )
    app.run()


if __name__ == "__main__":
    try:
        main()
    except ImportError as ie:
        print(ie, file=sys.stderr)
        sys.exit(1)
