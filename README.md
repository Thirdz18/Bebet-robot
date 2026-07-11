# Local Desktop Robot Assistant

A starter Python desktop robot prototype that can run locally on a laptop. It uses the laptop camera, microphone, and speaker to create a simple robot-style assistant.

## Features

- Opens the laptop webcam with OpenCV.
- Detects whether a face is visible with MediaPipe.
- Provides a small Tkinter desktop control panel.
- Listens through the microphone when you click **Listen Once**.
- Speaks responses using offline text-to-speech via pyttsx3.
- Includes simple Tagalog/English rule-based replies that can later be replaced with an AI model.

## Requirements

- Python 3.10 or newer is recommended.
- A working webcam.
- A working microphone.
- Speakers or headphones.
- Camera and microphone permissions enabled for your terminal or Python app.
- Internet connection for the default Google speech recognition backend used by `SpeechRecognition`.

## Setup

### Easiest setup on Windows

Double-click or run:

```bat
install_windows.bat
```

This creates `.venv` and installs the Python packages from `requirements.txt`. You still need Python installed first.

After setup, run:

```bat
run_windows.bat
```

### Manual setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/desktop_robot.py
```

## Run in Visual Studio Code

Yes, this project can run in Visual Studio Code. Recommended steps:

1. Open this folder in VS Code.
2. Install the VS Code Python extension if it is not installed yet.
3. Select the `.venv` Python interpreter after running the setup steps.
4. Run the **Install robot requirements** task if dependencies are not installed yet.
5. Open the Run and Debug panel and choose **Run Desktop Robot**.

The app still needs local camera and microphone permissions, even when launched from VS Code.


Click **Start Robot** to open the camera window. Click **Listen Once** and speak after the status changes to listening. Press `q` inside the camera window or click **Stop** to stop the robot.

## What you need to install

You need to install Python once on your computer. After that, this project needs Python packages from `requirements.txt`:

- `opencv-python` for the laptop camera.
- `mediapipe` for face detection.
- `pyttsx3` for robot voice output.
- `SpeechRecognition` for microphone speech-to-text.
- `PyAudio` so Python can access the microphone.

If you run `install_windows.bat` or `pip install -r requirements.txt`, those packages are installed for you inside `.venv`.

## Notes

- If `PyAudio` fails to install on Windows, install a compatible wheel or use a Python distribution that includes microphone support.
- `SpeechRecognition` with `recognize_google` needs internet. You can replace it later with a local Whisper model for offline speech-to-text.
- The current response logic is intentionally simple. The `_build_response` method in `src/desktop_robot.py` is the best place to connect an AI chatbot later.
