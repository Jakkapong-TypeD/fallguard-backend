import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from firebase_admin import firestore

from firebase_config import db
router = APIRouter(prefix="/devices", tags=["devices"])


class RegisterDeviceRequest(BaseModel):
    device_id: str
    group_id: str
    label: str = "กล้องห้องนั่งเล่น"


@router.post("/register")
def register_device(req: RegisterDeviceRequest):
    """ผูกกล้อง (เช่น device_id='living-room-cam-01') เข้ากับ family group ที่สร้างไว้"""
    group_doc = db.collection("family_groups").document(req.group_id).get()
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="ไม่พบกลุ่มนี้")

    db.collection("devices").document(req.device_id).set({
        "group_id": req.group_id,
        "label": req.label,
    })
    return {"status": "device_registered", "device_id": req.device_id, "group_id": req.group_id}

DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "dev-secret-token")


class DeviceStatusRequest(BaseModel):
    device_id: str
    posture: str
    confidence: float

def verify_device_token(authorization: str | None):
    if authorization != f"Bearer {DEVICE_TOKEN}":
        raise HTTPException(
            status_code=401,
            detail="Device token ไม่ถูกต้อง",
        )

@router.post("/status")
def update_device_status(
    data: DeviceStatusRequest,
    authorization: str | None = Header(default=None),
):
    verify_device_token(authorization)

    device_doc = db.collection("devices").document(data.device_id).get()

    if not device_doc.exists:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบอุปกรณ์นี้ในระบบ",
        )

    device_data = device_doc.to_dict() or {}
    group_id = device_data.get("group_id")

    db.collection("device_status").document(data.device_id).set(
        {
            "device_id": data.device_id,
            "group_id": group_id,
            "posture": data.posture,
            "confidence": data.confidence,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    return {
        "status": "updated",
        "device_id": data.device_id,
        "posture": data.posture,
    }
