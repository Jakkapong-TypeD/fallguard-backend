"""
fall_detector.py
-----------------
ตรวจจับการล้มจาก pose keypoints (MediaPipe Pose)
วิธีคิด: ติดตาม 3 ตัวชี้วัดร่วมกัน
  1. Aspect ratio ของ bounding box ร่างกาย (ยืน = สูงกว่ากว้าง, ล้ม = กว้างกว่าสูง)
  2. ความเร็วแนวดิ่งของจุดศูนย์กลางลำตัว (สะโพก) — ล้มจะเคลื่อนลงเร็วผิดปกติ
  3. มุมของลำตัว (เส้นไหล่-สะโพก) เทียบกับแนวราบ — ยืน/นั่ง มุมจะชันเข้าใกล้ 90 องศา, ล้มจะแบนราบ

ใช้ threshold + สถานะ "ล้มค้าง" (ไม่ลุกใน N วินาที) เพื่อลด false alarm
เช่น สะดุดแล้วลุกเองได้เร็วจะไม่แจ้งเตือน
"""

import time
import math
from collections import deque
from dataclasses import dataclass

import numpy as np
import mediapipe as mp


@dataclass
class FallEvent:
    timestamp: float
    confidence: float
    frame_snapshot: "np.ndarray | None" = None


class FallDetector:
    def __init__(
        self,
        aspect_ratio_threshold: float = 0.9,
        vertical_speed_threshold: float = 0.06,
        torso_angle_threshold: float = 40.0,
        confirm_seconds: float = 3.0,
        history_len: int = 15,
    ):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.last_pose_landmarks = None

        self.pose = self.mp_pose.Pose(
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.aspect_ratio_threshold = aspect_ratio_threshold
        self.vertical_speed_threshold = vertical_speed_threshold
        self.torso_angle_threshold = torso_angle_threshold
        self.confirm_seconds = confirm_seconds

        self.hip_y_history = deque(maxlen=history_len)
        self.fall_suspect_since: float | None = None
        self.last_event_time: float = 0.0
        self.cooldown_seconds = 30  # กันแจ้งเตือนซ้ำถี่เกินไป

    def _landmark_xy(self, landmarks, idx, frame_w, frame_h):
        lm = landmarks[idx]
        return np.array([lm.x * frame_w, lm.y * frame_h])

    def _compute_metrics(self, landmarks, frame_w, frame_h):
        L = self.mp_pose.PoseLandmark

        left_shoulder = self._landmark_xy(landmarks, L.LEFT_SHOULDER, frame_w, frame_h)
        right_shoulder = self._landmark_xy(landmarks, L.RIGHT_SHOULDER, frame_w, frame_h)
        left_hip = self._landmark_xy(landmarks, L.LEFT_HIP, frame_w, frame_h)
        right_hip = self._landmark_xy(landmarks, L.RIGHT_HIP, frame_w, frame_h)

        shoulder_mid = (left_shoulder + right_shoulder) / 2
        hip_mid = (left_hip + right_hip) / 2

        # 1) มุมลำตัว เทียบแนวราบ (0 = นอนราบ, 90 = ยืนตรง)
        dx = shoulder_mid[0] - hip_mid[0]
        dy = shoulder_mid[1] - hip_mid[1]
        torso_angle = math.degrees(math.atan2(abs(dy), abs(dx) + 1e-6))

        # 2) bounding box ของทุกจุดที่มองเห็น เพื่อหา aspect ratio
        xs, ys = [], []
        for lm in landmarks:
            if lm.visibility > 0.5:
                xs.append(lm.x * frame_w)
                ys.append(lm.y * frame_h)
        if not xs:
            return None
        box_w = max(xs) - min(xs)
        box_h = max(ys) - min(ys)
        aspect_ratio = box_w / (box_h + 1e-6)

        return {
            "torso_angle": torso_angle,
            "aspect_ratio": aspect_ratio,
            "hip_y_norm": hip_mid[1] / frame_h,
        }

    def process_frame(self, frame_bgr) -> FallEvent | None:
        """
        เรียกทุกเฟรม ส่งเฟรมภาพ (BGR จาก OpenCV) เข้ามา
        คืนค่า FallEvent ถ้ายืนยันว่าเกิดการล้ม (มี cooldown กันสแปม), ไม่งั้นคืน None
        """
        frame_h, frame_w = frame_bgr.shape[:2]
        frame_rgb = frame_bgr[:, :, ::-1]
        results = self.pose.process(frame_rgb)

        now = time.time()

        if not results.pose_landmarks:
            # ไม่เจอคนในเฟรม รีเซ็ตสถานะสงสัย
            self.fall_suspect_since = None
            return None

        metrics = self._compute_metrics(results.pose_landmarks.landmark, frame_w, frame_h)
        if metrics is None:
            return None

        self.hip_y_history.append((now, metrics["hip_y_norm"]))

        vertical_speed = 0.0
        if len(self.hip_y_history) >= 2:
            t0, y0 = self.hip_y_history[0]
            t1, y1 = self.hip_y_history[-1]
            if t1 - t0 > 0:
                vertical_speed = (y1 - y0) / (t1 - t0)

        is_horizontal_pose = (
            metrics["aspect_ratio"] > self.aspect_ratio_threshold
            and metrics["torso_angle"] < self.torso_angle_threshold
        )
        fell_fast = vertical_speed > self.vertical_speed_threshold

        suspect_now = is_horizontal_pose or fell_fast

        if suspect_now:
            if self.fall_suspect_since is None:
                self.fall_suspect_since = now
            duration = now - self.fall_suspect_since

            if duration >= self.confirm_seconds and (now - self.last_event_time) > self.cooldown_seconds:
                self.last_event_time = now
                confidence = min(1.0, (metrics["aspect_ratio"] / self.aspect_ratio_threshold) * 0.7 + 0.3)
                return FallEvent(timestamp=now, confidence=round(confidence, 2), frame_snapshot=frame_bgr)
        else:
            self.fall_suspect_since = None

        return None

    def close(self):
        self.pose.close()
