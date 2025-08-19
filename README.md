🎙️ Voice-Agent

An AI-powered voice assistant built with Python, Vosk, and Pyttsx3 that listens for wake words, processes voice commands, and responds in natural speech.

🚀 Features

🔊 Wake Word Detection – Activates on keywords like "Hey Agent" or "Agent"
<img width="1566" height="128" alt="image" src="https://github.com/user-attachments/assets/84de1441-64d7-498e-9e89-4ec0327aa21f" />

🎤 Offline Speech Recognition – Uses Vosk
 for accurate speech-to-text

🗣️ Text-to-Speech (TTS) – Converts AI responses into natural voice using Pyttsx3

🔧 Cross-platform Support – Runs on Windows, Linux, and macOS

📡 Extensible – Add custom commands and integrations easily

🌐 Optional Web Integrations – Open websites, run apps, and more

🛠️ Tech Stack

Python 3.8+

Vosk
 – Offline speech recognition

Pyttsx3
 – Text-to-speech engine

pyaudio
 – Audio input

RapidFuzz
 – Fuzzy matching for flexible commands

📦 Installation

Clone the repository

git clone https://github.com/your-username/voice-agent.git
cd voice-agent


Create & activate virtual environment (recommended)

python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows


Install dependencies

pip install -r requirements.txt


Download Vosk speech model (English example)

wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d model

▶️ Usage

Run the voice assistant:

python main.py


Speak the wake word (e.g., "Hey Agent") followed by your command.

Example:

🗣️ "Hey Agent, open Google"
🤖 "Opening Google..."

📂 Project Structure
voice-agent/
│── main.py              # Entry point
│── config.py            # Settings & wake words
│── commands/            # Custom command modules
│── model/               # Vosk speech model
│── requirements.txt     # Dependencies
│── README.md            # Documentation

🔧 Adding Custom Commands

You can extend functionality by editing commands/ and updating main.py.
For example, to add a "play music" command:

elif "play music" in user_command:
    engine.say("Playing music...")
    os.system("start spotify")  # Windows example


    
![Uploading image.png…]()


