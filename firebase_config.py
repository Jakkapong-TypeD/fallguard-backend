"""
firebase_config.py
-------------------
เชื่อม Firebase Admin SDK สำหรับ:
- Firestore: เก็บข้อมูล user, family group, alert log
- Cloud Messaging (FCM): ส่ง push notification ไปแอปมือถือญาติ
วิธีตั้งค่า:
1. ไปที่ Firebase Console -> Project Settings -> Service Accounts
2. กด "Generate new private key" จะได้ไฟล์ json
3. เซฟไว้ที่ backend/serviceAccountKey.json (อย่า commit เข้า git!)
   หรือถ้า deploy บน Render ให้ใช้ Secret Files (ดูคอมเมนต์ด้านล่าง)
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging

def _load_credential():
    # 1) ถ้ามี environment variable ที่ใส่ JSON ทั้งก้อนไว้ตรงๆ (ทางเลือกที่ยืดหยุ่นสุด)
    raw_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if raw_json:
        return credentials.Certificate(json.loads(raw_json))

    # 2) ถ้าเป็น Render Secret File จะถูกวางไว้ที่ /etc/secrets/<filename>
    render_secret_path = "/etc/secrets/serviceAccountKey.json"
    if os.path.exists(render_secret_path):
        return credentials.Certificate(render_secret_path)

    # 3) กรณีรัน local ปกติ ไฟล์อยู่ข้างๆ โค้ด
    local_path = "serviceAccountKey.json"
    if os.path.exists(local_path):
        return credentials.Certificate(local_path)

    raise FileNotFoundError(
        "ไม่พบ Firebase credentials — ตั้งค่า FIREBASE_CREDENTIALS_JSON "
        "หรือวางไฟล์ serviceAccountKey.json ไว้ตาม path ที่รองรับ"
    )

_cred = _load_credential()
firebase_app = firebase_admin.initialize_app(_cred)
db = firestore.client()

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
