import cv2
import time
import datetime
import os
import threading
import pyaudio
import wave
import shutil

# --- ⚙️ SYSTEM CONFIGURATION ---
CONFIG = {
    "SENSITIVITY_AREA": 500,    # Lower = More Sensitive
    "SAVE_DIR": "Secure_Vault",
    "MAX_DIR_SIZE_MB": 500,     # Auto-cleanup limit
    "BUFFER_TIME": 3,           # Recording buffer
    "AUDIO_CHUNK": 1024,
    "AUDIO_RATE": 44100
}

# --- 🎤 AUDIO MODULE ---
class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.recording = False
        self.stream = None

    def start(self, filename):
        self.frames = []
        self.filename = filename
        try:
            self.stream = self.audio.open(format=pyaudio.paInt16, channels=1,
                                          rate=CONFIG["AUDIO_RATE"], input=True,
                                          frames_per_buffer=CONFIG["AUDIO_CHUNK"])
            self.recording = True
            t = threading.Thread(target=self._record_loop)
            t.daemon = True
            t.start()
        except Exception as e:
            print(f"[ERROR] Mic Failed: {e}")

    def _record_loop(self):
        while self.recording:
            try:
                data = self.stream.read(CONFIG["AUDIO_CHUNK"], exception_on_overflow=False)
                self.frames.append(data)
            except:
                break

    def stop(self):
        self.recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.filename and self.frames:
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(CONFIG["AUDIO_RATE"])
            wf.writeframes(b''.join(self.frames))
            wf.close()

    def terminate(self):
        self.audio.terminate()

# --- 📹 SPY CAMERA ENGINE ---
class SpyCamEngine:
    def __init__(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # CAP_DSHOW for faster Windows start
        
        # --- WINDOWS 11 OPTIMIZATION ---
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=20, detectShadows=False)
        self.mic = AudioRecorder()
        
        if not os.path.exists(CONFIG["SAVE_DIR"]):
            os.makedirs(CONFIG["SAVE_DIR"])
            
        self.recording = False
        self.out_video = None
        self.timer = None
        self.window_visible = True
        
        ret, frame = self.cap.read()
        if ret:
            self.h, self.w, _ = frame.shape
            self.w = int(self.w)
            self.h = int(self.h)
        else:
            print("[ERROR] Camera Init Failed")
            self.w, self.h = 640, 480

    def manage_storage(self):
        """Auto-deletes old files to save disk space."""
        total_size = 0
        files = []
        for f in os.listdir(CONFIG["SAVE_DIR"]):
            fp = os.path.join(CONFIG["SAVE_DIR"], f)
            total_size += os.path.getsize(fp)
            files.append(fp)
        
        size_mb = total_size / (1024 * 1024)
        if size_mb > CONFIG["MAX_DIR_SIZE_MB"]:
            files.sort(key=os.path.getmtime)
            try:
                os.remove(files[0])
                print(f"[SYSTEM] Cleanup: Deleted {os.path.basename(files[0])}")
            except:
                pass

    def run(self):
        # --- 🕵️‍♂️ BOOT SEQUENCE INJECTED HERE ---
        print("\n")
        print("===================================================")
        print("   🕵️‍♂️  S P Y   D E T E C T O R   P R O   v 2.0")
        print("===================================================")
        time.sleep(0.5) # Thora delay taake real lagay
        print("   [SYSTEM]  Initializing Core Modules...   [OK]")
        time.sleep(0.3)
        print(f"   [VIDEO]   Calibrating Optical Sensors... [OK] ({self.w}x{self.h})")
        time.sleep(0.3)
        print("   [AUDIO]   Engaging Acoustic Array...     [OK]")
        time.sleep(0.5)
        print("   [MODE]    Active Surveillance: STARTED")
        print("---------------------------------------------------")
        print("   ⚠️  STATUS: ARMED & MONITORING")
        print("===================================================")
        print("   Press 'q' to Quit, 'h' to Hide Window.\n")

        try:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret: break

                vis_frame = frame.copy()
                fgmask = self.fgbg.apply(frame)
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, (3,3))
                contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                motion_detected = False
                for cnt in contours:
                    if cv2.contourArea(cnt) > CONFIG["SENSITIVITY_AREA"]:
                        motion_detected = True
                        (x, y, w, h) = cv2.boundingRect(cnt)
                        cv2.rectangle(vis_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(vis_frame, "REC", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                timestamp = datetime.datetime.now()
                ts_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")

                if motion_detected:
                    if not self.recording:
                        self.recording = True
                        base_path = os.path.join(CONFIG["SAVE_DIR"], ts_str)
                        
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        self.out_video = cv2.VideoWriter(f"{base_path}_VIDEO.mp4", fourcc, 20.0, (self.w, self.h))
                        self.mic.start(f"{base_path}_AUDIO.wav")
                        cv2.imwrite(f"{base_path}_SNAPSHOT.jpg", frame)
                        print(f"   [ALERT] 🚨 Recording Started: {ts_str}")
                    
                    self.timer = None
                else:
                    if self.recording:
                        if self.timer is None: self.timer = time.time()
                        if time.time() - self.timer > CONFIG["BUFFER_TIME"]:
                            self.recording = False
                            if self.out_video: self.out_video.release()
                            self.mic.stop()
                            print(f"   [INFO]  💾 Evidence Saved.")
                            self.manage_storage()

                if self.recording and self.out_video:
                    self.out_video.write(vis_frame)

                # Status Bar
                cv2.rectangle(vis_frame, (0, self.h-30), (self.w, self.h), (0, 0, 0), -1)
                status = "● REC" if self.recording else "● MONITORING"
                color = (0, 0, 255) if self.recording else (0, 255, 0)
                cv2.putText(vis_frame, f"{status} | {timestamp.strftime('%H:%M:%S')}", (10, self.h-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

                if self.window_visible:
                    cv2.imshow("Spy Master Pro", vis_frame)

                key = cv2.waitKey(1)
                if key == ord('q'): break
                elif key == ord('h'): 
                    self.window_visible = False
                    cv2.destroyAllWindows()
                    print("   [STEALTH] Window Hidden (Press 's' to show)")
                elif key == ord('s'): 
                    self.window_visible = True
                    print("   [GUI] Window Visible")

        finally:
            if self.recording:
                self.mic.stop()
                if self.out_video: self.out_video.release()
            
            self.mic.terminate()
            self.cap.release()
            cv2.destroyAllWindows()
            print("===================================================")
            print("   [SYSTEM]  Shutting Down... [OFFLINE]")
            print("===================================================")

if __name__ == "__main__":
    app = SpyCamEngine()
    app.run()