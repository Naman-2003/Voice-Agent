import os
import queue
import sounddevice as sd
import pyttsx3
from vosk import Model, KaldiRecognizer
from rapidfuzz import process

# ---------------- Config ----------------
WAKE_WORDS = ["hey agent", "agent"]
COMMANDS = {
    "open browser": "Opening browser...",
    "hello": "Hello! How can I help you?",
    "exit": "Goodbye!"
}

# ---------------- Setup ----------------
print("Loading model...")
model = Model("model")  # put vosk model folder inside project dir
recognizer = KaldiRecognizer(model, 16000)

engine = pyttsx3.init()
q = queue.Queue()

# ---------------- Capture ----------------
def callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

def speak(text):
    print("Agent:", text)
    engine.say(text)
    engine.runAndWait()

# ---------------- Main Loop ----------------
def main():
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("Say 'hey agent' to wake me up...")
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = eval(result).get("text", "")
                if text:
                    print("You said:", text)

                    # Wake word detection
                    if any(word in text for word in WAKE_WORDS):
                        speak("I'm listening...")

                    # Command matching
                    best_match = process.extractOne(text, COMMANDS.keys())
                    if best_match and best_match[1] > 70:
                        response = COMMANDS[best_match[0]]
                        speak(response)
                        if "exit" in best_match[0]:
                            break

if __name__ == "__main__":
    main()
