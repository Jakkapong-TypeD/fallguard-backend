import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging

firebase_creds_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

if firebase_creds_json:
    cred_dict = json.loads(firebase_creds_json)
    _cred = credentials.Certificate(cred_dict)
else:
    _cred = credentials.Certificate("serviceAccountKey.json")
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
