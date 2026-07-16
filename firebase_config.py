import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# 1. ดึงค่า String JSON จาก Render
firebase_creds_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

# 2. ตรวจสอบเงื่อนไขการใช้กุญแจ
if firebase_creds_json:
    try:
        # แปลงข้อความ String ให้กลายเป็น Dictionary JSON
        cred_dict = json.loads(firebase_creds_json)
        _cred = credentials.Certificate(cred_dict)
        print("--- [Firebase] เชื่อมต่อผ่าน Environment Variable สำเร็จ! ---")
    except Exception as e:
        print(f"--- [Firebase Error] แปลง JSON ผิดพลาด: {e} ---")
        raise e
else:
    # สำหรับรันเทสในคอมตัวเอง (Local)
    _cred = credentials.Certificate("serviceAccountKey.json")
    print("--- [Firebase] เชื่อมต่อผ่านไฟล์ serviceAccountKey.json ในเครื่องสำเร็จ! ---")

# 3. เริ่มทำงาน
firebase_app = firebase_admin.initialize_app(_cred)
db = firestore.client()


# === โค้ดฟังก์ชันเดิมของคุณ (ห้ามลบ) ===
def send_push_to_tokens(tokens: list[str], title: str, body: str, data: dict | None = None):
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
