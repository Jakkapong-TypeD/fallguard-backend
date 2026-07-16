import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# 1. เช็คก่อนว่าอยู่บน Render หรือไม่ (ดึงค่า String JSON จาก Env บน Render)
firebase_creds_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

if firebase_creds_json:
    # === [สำหรับรันบน Render] ===
    # แปลงข้อความจาก Env ให้กลับเป็น Dictionary เพื่อใช้รันแอป
    cred_dict = json.loads(firebase_creds_json)
    _cred = credentials.Certificate(cred_dict)
else:
    # === [สำหรับรันในคอมคุณเอง (Local)] ===
    # จะวิ่งไปดึงไฟล์ serviceAccountKey.json ในโฟลเดอร์ของคุณมาทำงานทันที
    _cred = credentials.Certificate("serviceAccountKey.json")

# เริ่มทำงาน Firebase
firebase_app = firebase_admin.initialize_app(_cred)
db = firestore.client()


# === โค้ดส่งแจ้งเตือนเดิมของคุณ (ทำงานได้ปกติเหมือนเดิมทุกอย่าง) ===
def send_push_to_tokens(tokens: list[str], title: str, body: str, data: dict | None = None):
    """ส่ง push notification ไปหลายเครื่องพร้อมกัน (สมาชิกในกลุ่มครอบครัว)"""
    if not tokens:
        return None

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        tokens=tokens,
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(aps=messaging.Aps(sound="default"))
        ),
    )
    return messaging.send_multicast(message)
