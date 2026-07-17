"""
camera_stream.py
-----------------
จำลองกล้องวงจรปิดในบ้าน โดยใช้กล้องของโน้ตบุ๊ก/2-in-1
- ดึงภาพ real-time ด้วย OpenCV
- ส่งแต่ละเฟรมเข้า FallDetector
- ถ้าพบ FallEvent -> POST ไป backend endpoint /alerts/fall

ภายหลังถ้าจะเปลี่ยนเป็นกล้องวงจรปิดจริง แค่เปลี่ยน CAMERA_SOURCE
เป็น RTSP URL เช่น "rtsp://user:pass@192.168.1.50:554/stream1"
"""

import os
import time
import base64
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
BACKEND_URL = os.getenv("BACKEND_URL", "https://my-app-backend-xt03.onrender.com")
DEVICE_ID = os.getenv("DEVICE_ID", "living-room-cam-01")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "dev-secret-token")  # ใช้ยืนยันตัวกล้องกับ backend


def send_alert(event, device_id: str):
    """ส่ง event การล้มไป backend พร้อมภาพ snapshot (base64)"""
    snapshot_b64 = None
    if event.frame_snapshot is not None:
        ok, buf = cv2.imencode(".jpg", event.frame_snapshot)
        if ok:
            snapshot_b64 = base64.b64encode(buf).decode("utf-8")

    payload = {
        "device_id": device_id,
        "timestamp": event.timestamp,
        "confidence": event.confidence,
        "snapshot_base64": snapshot_b64,
    }
    headers = {"Authorization": f"Bearer {DEVICE_TOKEN}"}

    try:
        resp = requests.post(f"{BACKEND_URL}/alerts/fall", json=payload, headers=headers, timeout=5)
        print(f"[ALERT SENT] status={resp.status_code} confidence={event.confidence}")
    except requests.RequestException as e:
        print(f"[ALERT FAILED] {e}")


def main():
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    if not cap.isOpened():
        raise RuntimeError(f"เปิดกล้องไม่ได้: {CAMERA_SOURCE}")

    detector = FallDetector()
    print(f"เริ่มตรวจจับ... device_id={DEVICE_ID}, source={CAMERA_SOURCE}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("อ่านเฟรมไม่ได้ ลองใหม่...")
                time.sleep(0.5)
                continue

            event = detector.process_frame(frame)
            if event:
                print(f"!! ตรวจพบการล้ม confidence={event.confidence} เวลา={event.timestamp}")
                send_alert(event, DEVICE_ID)

            # แสดงผลสำหรับ debug (ปิดได้ถ้ารันบน server ไม่มีจอ)
            cv2.imshow("Fall Detection - Simulated CCTV", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()


if __name__ == "__main__":
    main()
