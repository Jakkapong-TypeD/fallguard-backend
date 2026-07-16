import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# 1. พยายามดึงค่า JSON String จาก Environment Variable บน Render
firebase_creds_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

if firebase_creds_json:
    # สำหรับรันบน Render: แปลง String JSON กลับมาเป็น Dictionary เพื่อใช้งาน
    cred_dict = json.loads(firebase_creds_json)
    _cred = credentials.Certificate(cred_dict)
else:
    # สำหรับรันเทสในเครื่องตัวเอง (Local): หากไม่มี Env ให้ไปดึงจากไฟล์ในเครื่องเหมือนเดิม
    _cred = credentials.Certificate("serviceAccountKey.json")

firebase_app = firebase_admin.initialize_app(_cred)
db = firestore.client()

# โค้ดฟังก์ชัน def send_push_to_tokens ด้านล่างของคุณคงไว้เหมือนเดิมได้เลยครับ...
