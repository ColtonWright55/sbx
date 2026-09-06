#!/usr/bin/env python3
"""Stage 1: locate the scale's display rectangle. Run directly for a live debug view."""
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

DEBUG_PORT = 8081
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "logs" / "readings.csv"

# segment order: (top, top-left, top-right, middle, bottom-left, bottom-right, bottom)
DIGITS_LOOKUP = {
    (1, 1, 1, 0, 1, 1, 1): 0,
    (0, 0, 1, 0, 0, 1, 0): 1,
    (1, 0, 1, 1, 1, 1, 0): 2,
    (1, 0, 1, 1, 0, 1, 1): 3,
    (0, 1, 1, 1, 0, 1, 0): 4,
    (1, 1, 0, 1, 0, 1, 1): 5,
    (1, 1, 0, 1, 1, 1, 1): 6,
    (1, 0, 1, 0, 0, 1, 0): 7,
    (1, 1, 1, 1, 1, 1, 1): 8,
    (1, 1, 1, 1, 0, 1, 1): 9,
}


def capture_frame(picam2):
    return cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (width, height))


RED_LO1, RED_HI1 = np.array([0, 70, 60]), np.array([12, 255, 255])
RED_LO2, RED_HI2 = np.array([165, 70, 60]), np.array([180, 255, 255])


def red_mask(frame):
    """Mask of the red marker traced along the display's edges."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, RED_LO1, RED_HI1) | cv2.inRange(hsv, RED_LO2, RED_HI2)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8), iterations=2)


def find_displays(frame):
    """Return the hole enclosed by each red RING (marker traced around a display), largest first.

    A traced outline has a hole in the middle; a solid color blob (skin, carpet, etc.) doesn't.
    Requiring a hole is what tells the marker apart from any other red-ish thing in frame.
    """
    contours, hierarchy = cv2.findContours(red_mask(frame), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return []
    quads = []
    for i, c in enumerate(contours):
        child = hierarchy[0][i][2]
        if child != -1 and cv2.contourArea(c) > 500 and cv2.contourArea(contours[child]) > 200:
            quads.append(cv2.boxPoints(cv2.minAreaRect(contours[child])))
    return sorted(quads, key=cv2.contourArea, reverse=True)


def decode_digit(roi):
    h, w = roi.shape
    dW, dH, dHC = int(w * 0.3), int(h * 0.15), int(h * 0.08)
    regions = [
        (0, 0, w, dH),                   # top
        (0, 0, dW, h // 2),               # top-left
        (w - dW, 0, dW, h // 2),          # top-right
        (0, h // 2 - dHC, w, 2 * dHC),    # middle
        (0, h // 2, dW, h // 2),          # bottom-left
        (w - dW, h // 2, dW, h // 2),     # bottom-right
        (0, h - dH, w, dH),               # bottom
    ]
    on = tuple(1 if rw > 0 and rh > 0 and cv2.countNonZero(roi[y:y + rh, x:x + rw]) / (rw * rh) > 0.4 else 0
               for x, y, rw, rh in regions)
    return DIGITS_LOOKUP.get(on)


def decode_digits(warped):
    """Threshold the rectified display crop and decode any 7-segment digits, left to right."""
    h_full, w_full = warped.shape[:2]
    mx, my = int(w_full * 0.08), int(h_full * 0.08)
    warped = warped[my:h_full - my, mx:w_full - mx]  # trim the marker line off the edges

    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    all_boxes = [cv2.boundingRect(c) for c in cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]]
    boxes = sorted(
        (b for b in all_boxes
         if b[3] > 0.5 * thresh.shape[0] and b[3] > b[2]
         and b[2] < 0.9 * thresh.shape[1] and b[3] < 0.9 * thresh.shape[0]),  # reject full-crop border artifacts
        key=lambda b: b[0],
    )

    digits = ""
    for x, y, w, h in boxes:
        digit = decode_digit(thresh[y:y + h, x:x + w])
        if digit is None:
            return None
        digits += str(digit)
    if not digits:
        return None
    return digits[:-1] + "." + digits[-1] if len(digits) > 1 else digits  # decimal one digit from the right


def log_reading(value):
    LOG_PATH.parent.mkdir(exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')},{value}\n")


def debug_tile(frame):
    """2x2 grid: raw | red mask, mask overlay | annotated."""
    mask = red_mask(frame)
    quads = find_displays(frame)

    overlay = frame.copy()
    overlay[mask > 0] = (0, 0, 255)
    annotated = frame.copy()
    for quad in quads:
        cv2.drawContours(annotated, [quad.astype(int)], -1, (0, 255, 0), 3)
        digits = decode_digits(four_point_transform(frame, quad.astype("float32")))
        corner = tuple(quad[quad[:, 1].argmin()].astype(int))
        cv2.putText(annotated, digits or "?", corner, cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

    size = (frame.shape[1] // 2, frame.shape[0] // 2)
    views = [
        cv2.resize(frame, size),
        cv2.resize(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), size),
        cv2.resize(overlay, size),
        cv2.resize(annotated, size),
    ]
    return np.vstack([np.hstack(views[:2]), np.hstack(views[2:])])


def main():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from picamera2 import Picamera2

    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration())
    picam2.start()
    time.sleep(1)  # let AE/AWB settle

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while True:
                    frame = capture_frame(picam2)
                    for quad in find_displays(frame):
                        digits = decode_digits(four_point_transform(frame, quad.astype("float32")))
                        if digits:
                            print(digits)
                            log_reading(digits)

                    ok, jpg = cv2.imencode(".jpg", debug_tile(frame))
                    if not ok:
                        continue
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass

    print(f"Debug stream: ffplay http://pi1.lan:{DEBUG_PORT}/ (Ctrl+C to stop)")
    ThreadingHTTPServer(("0.0.0.0", DEBUG_PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
