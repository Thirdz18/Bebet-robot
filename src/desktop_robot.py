"""Local desktop robot assistant prototype.

Features:
- Opens the laptop webcam with OpenCV.
- Uses MediaPipe to detect whether a face is visible.
- Uses Tkinter for a simple desktop control panel.
- Uses speech_recognition for microphone input.
- Uses pyttsx3 for offline text-to-speech output.

Run with:
    python src/desktop_robot.py
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import mediapipe as mp
import pyttsx3
import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox, scrolledtext


@dataclass
class RobotState:
    """Shared state for the camera and assistant threads."""

    running: bool = False
    listening: bool = False
    face_visible: bool = False
    last_heard: str = ""
    last_response: str = ""


class DesktopRobotApp:
    """Tkinter desktop app for a camera + voice robot prototype."""

    def __init__(self) -> None:
        self.state = RobotState()
        self.events: queue.Queue[str] = queue.Queue()
        self.camera_thread: Optional[threading.Thread] = None
        self.listen_thread: Optional[threading.Thread] = None
        self.camera: Optional[cv2.VideoCapture] = None
        self.face_detector = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.6,
        )
        self.recognizer = sr.Recognizer()
        self.tts = pyttsx3.init()

        self.root = tk.Tk()
        self.root.title("Local Desktop Robot Assistant")
        self.root.geometry("620x480")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.status_var = tk.StringVar(value="Status: stopped")
        self.face_var = tk.StringVar(value="Face: not detected")
        self.heard_var = tk.StringVar(value="Last heard: —")

        self._build_ui()
        self.root.after(200, self._drain_events)

    def _build_ui(self) -> None:
        title = tk.Label(
            self.root,
            text="🤖 Local Desktop Robot Assistant",
            font=("Arial", 18, "bold"),
        )
        title.pack(pady=12)

        tk.Label(self.root, textvariable=self.status_var, font=("Arial", 11)).pack()
        tk.Label(self.root, textvariable=self.face_var, font=("Arial", 11)).pack()
        tk.Label(self.root, textvariable=self.heard_var, font=("Arial", 11)).pack(pady=(0, 10))

        controls = tk.Frame(self.root)
        controls.pack(pady=8)

        self.start_button = tk.Button(controls, text="Start Robot", width=14, command=self.start)
        self.start_button.grid(row=0, column=0, padx=6)

        self.listen_button = tk.Button(
            controls,
            text="Listen Once",
            width=14,
            command=self.listen_once,
            state=tk.DISABLED,
        )
        self.listen_button.grid(row=0, column=1, padx=6)

        self.stop_button = tk.Button(
            controls,
            text="Stop",
            width=14,
            command=self.stop,
            state=tk.DISABLED,
        )
        self.stop_button.grid(row=0, column=2, padx=6)

        self.log = scrolledtext.ScrolledText(self.root, height=16, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)
        self._log("Tip: click Start Robot, then Listen Once. Press 'q' in the camera window to close it.")

    def run(self) -> None:
        self.root.mainloop()

    def start(self) -> None:
        if self.state.running:
            return

        self.state.running = True
        self.status_var.set("Status: running")
        self.start_button.config(state=tk.DISABLED)
        self.listen_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)

        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()
        self._say_async("Hello, ako ang local desktop robot assistant mo.")
        self._log("Robot started. Camera window should open shortly.")

    def stop(self) -> None:
        self.state.running = False
        self.state.listening = False
        self.status_var.set("Status: stopped")
        self.face_var.set("Face: not detected")
        self.start_button.config(state=tk.NORMAL)
        self.listen_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        if self.camera is not None:
            self.camera.release()
            self.camera = None
        cv2.destroyAllWindows()
        self._log("Robot stopped.")

    def close(self) -> None:
        self.stop()
        self.face_detector.close()
        self.root.destroy()

    def listen_once(self) -> None:
        if not self.state.running or self.state.listening:
            return

        self.state.listening = True
        self.status_var.set("Status: listening...")
        self.listen_button.config(state=tk.DISABLED)
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def _camera_loop(self) -> None:
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.events.put("ERROR: Hindi mabuksan ang camera. Check camera permission or camera index.")
            self.state.running = False
            return

        while self.state.running:
            ok, frame = self.camera.read()
            if not ok:
                self.events.put("ERROR: Hindi mabasa ang camera frame.")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb_frame)
            self.state.face_visible = bool(results.detections)

            status_text = "Face detected" if self.state.face_visible else "No face detected"
            color = (0, 200, 0) if self.state.face_visible else (0, 0, 255)
            cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.imshow("Robot Camera - press q to close", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.state.running = False
                break

        self.events.put("CAMERA_STOPPED")

    def _listen_loop(self) -> None:
        try:
            with sr.Microphone() as source:
                self.events.put("Listening... magsalita ka ngayon.")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)

            text = self.recognizer.recognize_google(audio, language="tl-PH")
            self.state.last_heard = text
            response = self._build_response(text)
            self.state.last_response = response
            self.events.put(f"You: {text}")
            self.events.put(f"Robot: {response}")
            self._say(response)
        except sr.WaitTimeoutError:
            self.events.put("Walang narinig na boses. Subukan ulit.")
        except sr.UnknownValueError:
            self.events.put("Hindi ko naintindihan ang sinabi mo. Pakiulit.")
        except sr.RequestError as exc:
            self.events.put(f"Speech recognition error: {exc}")
        except OSError as exc:
            self.events.put(f"Microphone error: {exc}")
        finally:
            self.state.listening = False
            self.events.put("LISTEN_DONE")

    def _build_response(self, text: str) -> str:
        lowered = text.lower()
        if "hello" in lowered or "hi" in lowered or "kamusta" in lowered:
            return "Hello! Okay ako. Ready akong tumulong sa iyo."
        if "oras" in lowered:
            return f"Ang oras ngayon ay {time.strftime('%I:%M %p')}."
        if "pangalan" in lowered:
            return "Ako ang local desktop robot assistant mo."
        if "salamat" in lowered:
            return "Walang anuman. Masaya akong makatulong."
        return f"Narinig ko ang sinabi mo: {text}. Sa susunod, pwede natin itong ikonekta sa AI model para mas matalino ang sagot ko."

    def _say_async(self, message: str) -> None:
        threading.Thread(target=self._say, args=(message,), daemon=True).start()

    def _say(self, message: str) -> None:
        self.tts.say(message)
        self.tts.runAndWait()

    def _drain_events(self) -> None:
        while not self.events.empty():
            event = self.events.get_nowait()
            if event == "LISTEN_DONE":
                self.status_var.set("Status: running")
                if self.state.running:
                    self.listen_button.config(state=tk.NORMAL)
            elif event == "CAMERA_STOPPED":
                self.stop()
            elif event.startswith("ERROR:"):
                messagebox.showerror("Robot error", event.replace("ERROR: ", ""))
                self.stop()
            else:
                self._log(event)

        self.face_var.set("Face: detected" if self.state.face_visible else "Face: not detected")
        self.heard_var.set(f"Last heard: {self.state.last_heard or '—'}")
        self.root.after(200, self._drain_events)

    def _log(self, message: str) -> None:
        self.log.insert(tk.END, f"{message}\n")
        self.log.see(tk.END)


if __name__ == "__main__":
    DesktopRobotApp().run()
