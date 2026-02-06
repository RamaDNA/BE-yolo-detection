import cv2
import time

class StreamService:
    def __init__(self, rtsp_url, retry_delay=2):
        self.rtsp_url = rtsp_url
        self.retry_delay = retry_delay
        self.cap = None
        self.connect()

    def connect(self):
        """Try to connect to RTSP."""
        if self.cap is not None:
            self.cap.release()

        print(f"[StreamService] Connecting to {self.rtsp_url}")
        self.cap = cv2.VideoCapture(
            self.rtsp_url
            ,cv2.CAP_FFMPEG)
            
        # decrease buffer size for lower latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.cap.isOpened():
            print("[StreamService] Failed to connect. Retrying...")
            self.cap = None

    def read(self):
        """Read frame; reconnect if needed."""
        if self.cap is None:
            time.sleep(self.retry_delay)
            self.connect()
            return None

        ok, frame = self.cap.read()

        if not ok:
            print("[StreamService] Frame lost. Reconnecting...")
            time.sleep(self.retry_delay)
            self.connect()
            return None

        return frame

    def release(self):
        try:
            if self.cap:
                self.cap.release()
        except:
            pass
