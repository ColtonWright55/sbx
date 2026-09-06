import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
from picamera2 import Picamera2

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
FPS = 30  # output container rate; frames are repeated as needed to match real elapsed time


def main():
    OUT_DIR.mkdir(exist_ok=True)
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration())
    picam2.start()
    time.sleep(1)  # let AE/AWB settle

    frame = cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)
    h, w = frame.shape[:2]
    video_path = OUT_DIR / f"raw_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.mp4"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))

    print(f"Recording to {video_path} (Ctrl+C to stop)")
    start = time.monotonic()
    frames_written = 0
    try:
        while True:
            frame = cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)
            target_frames = int((time.monotonic() - start) * FPS)
            while frames_written < target_frames:
                writer.write(frame)
                frames_written += 1
    except KeyboardInterrupt:
        pass
    finally:
        writer.release()
        picam2.stop()


if __name__ == "__main__":
    main()
