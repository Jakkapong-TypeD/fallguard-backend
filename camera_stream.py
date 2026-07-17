"""
camera_stream.py
----------------
จำลองกล้องวงจรปิดในบ้านด้วยกล้อง Webcam

- อ่านภาพแบบ real-time ด้วย OpenCV
- ส่งภาพให้ FallDetector วิเคราะห์
- ถ้าพบการล้ม ส่งแจ้งเตือนไป Backend
- ส่งสถานะท่าทางไป Backend ทุก 1 วินาที
"""

import base64
import os
import time

import cv2
import requests
from dotenv import load_dotenv

from ai.fall_detector import FallDetector


load_dotenv()


camera_source = os.getenv("CAMERA_SOURCE", "0")

CAMERA_SOURCE = (
    int(camera_source)
    if camera_source.isdigit()
    else camera_source
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://my-app-backend-xt03.onrender.com",
)

DEVICE_ID = os.getenv(
    "DEVICE_ID",
    "living-room-cam-01",
)

DEVICE_TOKEN = os.getenv(
    "DEVICE_TOKEN",
    "dev-secret-token",
)


def send_alert(event, device_id: str):
    """ส่งข้อมูลการล้มไปยัง Backend พร้อมภาพ snapshot"""

    snapshot_b64 = None

    if event.frame_snapshot is not None:
        ok, buffer = cv2.imencode(
            ".jpg",
            event.frame_snapshot,
        )

        if ok:
            snapshot_b64 = base64.b64encode(
                buffer
            ).decode("utf-8")

    payload = {
        "device_id": device_id,
        "timestamp": event.timestamp,
        "confidence": event.confidence,
        "snapshot_base64": snapshot_b64,
    }

    headers = {
        "Authorization": f"Bearer {DEVICE_TOKEN}",
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/alerts/fall",
            json=payload,
            headers=headers,
            timeout=10,
        )

        print(
            f"[ALERT SENT] "
            f"status={response.status_code} "
            f"confidence={event.confidence}"
        )

        if response.status_code != 200:
            print(f"[ALERT RESPONSE] {response.text}")

    except requests.RequestException as error:
        print(f"[ALERT FAILED] {error}")


def send_status(posture: str, confidence: float):
    """ส่งสถานะท่าทางล่าสุดไปยัง Backend"""

    payload = {
        "device_id": DEVICE_ID,
        "posture": posture,
        "confidence": confidence,
    }

    headers = {
        "Authorization": f"Bearer {DEVICE_TOKEN}",
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/devices/status",
            json=payload,
            headers=headers,
            timeout=10,
        )

        print(
            f"[STATUS SENT] "
            f"status={response.status_code} "
            f"posture={posture} "
            f"confidence={confidence}"
        )

        if response.status_code != 200:
            print(f"[STATUS RESPONSE] {response.text}")

    except requests.RequestException as error:
        print(f"[STATUS FAILED] {error}")


def main():
    cap = cv2.VideoCapture(CAMERA_SOURCE)

    if not cap.isOpened():
        raise RuntimeError(
            f"เปิดกล้องไม่ได้: {CAMERA_SOURCE}"
        )

    detector = FallDetector()

    print(
        f"เริ่มตรวจจับ... "
        f"device_id={DEVICE_ID}, "
        f"source={CAMERA_SOURCE}"
    )

    last_status_sent = 0.0

    try:
        while True:
            success, frame = cap.read()

            if not success:
                print("อ่านเฟรมไม่ได้ ลองใหม่...")
                time.sleep(0.5)
                continue

            event = detector.process_frame(frame)

            if event is not None:
                print(
                    f"!! ตรวจพบการล้ม "
                    f"confidence={event.confidence} "
                    f"เวลา={event.timestamp}"
                )

                send_alert(
                    event,
                    DEVICE_ID,
                )

            now = time.time()

            if now - last_status_sent >= 1.0:
                send_status(
                    detector.current_posture,
                    detector.posture_confidence,
                )

                last_status_sent = now

            detector.draw_landmarks(frame)

            cv2.putText(
                frame,
                (
                    f"Posture: {detector.current_posture} "
                    f"({detector.posture_confidence:.2f})"
                ),
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(
                "Fall Detection - Simulated CCTV",
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nหยุดโปรแกรมแล้ว")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()


if __name__ == "__main__":
    main()
