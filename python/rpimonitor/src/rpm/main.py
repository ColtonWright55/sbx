import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
from picamera2 import Picamera2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rpm.find_display import find_displays

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
INTERVAL_S = 3.0


def main():
    OUT_DIR.mkdir(exist_ok=True)
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration())
    picam2.start()
    time.sleep(1)  # let AE/AWB settle

    video_path = OUT_DIR / f"{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.mp4"
    writer = None

    print(f"Logging to {video_path} (Ctrl+C to stop)")
    try:
        while True:
            start = time.monotonic()
            frame = cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)

            if writer is None:
                h, w = frame.shape[:2]
                writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 1 / INTERVAL_S, (w, h))

            for quad in find_displays(frame):  # empty if none found this frame, that's fine
                cv2.drawContours(frame, [quad.astype(int)], -1, (0, 255, 0), 3)

            writer.write(frame)
            time.sleep(max(0, INTERVAL_S - (time.monotonic() - start)))
    except KeyboardInterrupt:
        pass
    finally:
        if writer:
            writer.release()
        picam2.stop()


if __name__ == "__main__":
    main()
