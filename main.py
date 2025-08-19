import json
import os
import sys
import platform
import subprocess
import shlex
import logging
import webbrowser
import pyttsx3
import pyaudio
from rapidfuzz import process, fuzz
from vosk import Model, KaldiRecognizer

# ---------------- Config ----------------
WAKE_WORDS = ["hey agent", "agent"]  # wake words
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "model"))
COMMANDS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "commands.json"))
SAMPLE_RATE = 16000
CHUNK_SIZE = 4000
FUZZY_THRESHOLD = 70

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Persistent TTS engine
engine = pyttsx3.init()


# ---------------- Helpers ----------------
def say(text: str):
    """Speak text using pyttsx3"""
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"TTS error: {e}")


def expand_path(p: str) -> str:
    """Expand ~, %VARS%, and {{username}} placeholders"""
    if not p:
        return p
    try:
        username = os.environ.get("USERNAME") or os.getlogin()
    except Exception:
        username = ""
    p = p.replace("{{username}}", username)
    p = os.path.expandvars(p)
    p = os.path.expanduser(p)
    return os.path.abspath(p)


def load_commands():
    """Load and normalize commands"""
    if not os.path.exists(COMMANDS_FILE):
        raise FileNotFoundError(f"Commands file not found: {COMMANDS_FILE}")
    try:
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in commands file: {e}")

    alias_to_intent = {}
    intents = {}

    for intent, cfg in raw.items():
        intents[intent] = cfg
        alias_to_intent[intent] = intent
        for alias in cfg.get("aliases", []):
            alias_to_intent[alias.lower()] = intent

    return intents, alias_to_intent


def run_action(canonical_intent: str, cfg: dict, argument: str | None = None):
    """Execute action based on intent config"""
    try:
        system = platform.system().lower()
        action_type = cfg.get("type")

        if action_type == "app":
            if system == "windows":
                path = expand_path(cfg.get("win_path"))
                if not path or not os.path.exists(path):
                    raise FileNotFoundError(f"App not found: {path}")
                subprocess.Popen([path])  # ✅ Windows apps
            elif system == "darwin":
                subprocess.run(["open", "-a", cfg.get("mac_app")], check=True)
            elif system == "linux":
                subprocess.run(shlex.split(cfg.get("linux_cmd")), check=True)

        elif action_type == "folder":
            path = expand_path(cfg.get("path"))
            if not os.path.exists(path):
                raise FileNotFoundError(f"Folder not found: {path}")
            if system == "windows":
                subprocess.Popen(["explorer", path])  # ✅ Windows folders
            elif system == "darwin":
                subprocess.run(["open", path], check=True)
            elif system == "linux":
                subprocess.run(["xdg-open", path], check=True)

        elif action_type == "url":
            webbrowser.open(cfg.get("url"))

        elif action_type == "search":
            base = cfg.get("url")
            q = (argument or "").strip()
            full = base + (q.replace(" ", "+") if q else "")
            webbrowser.open(full)

        elif action_type == "system":
            cmd = cfg.get(f"{system}_cmd")
            subprocess.run(cmd, shell=True)

        say(f"Executing {canonical_intent}")

    except Exception as e:
        msg = f"Error executing '{canonical_intent}': {e}"
        logging.error(msg)
        say(msg)


def strip_wake(text: str) -> str:
    """Remove wake word"""
    t = text
    for w in WAKE_WORDS:
        t = t.replace(w, " ")
    return " ".join(t.split()).strip()


def best_intent_match(user_text: str, alias_to_intent: dict[str, str]) -> tuple[str | None, int]:
    """Hybrid: substring + fuzzy match"""
    user_text = user_text.lower().strip()

    # --- Substring direct match ---
    for alias, intent in alias_to_intent.items():
        if alias in user_text:
            return intent, 100

    # --- Fuzzy fallback ---
    all_phrases = list(alias_to_intent.keys())
    if not all_phrases:
        return None, 0

    match, score, _ = process.extractOne(user_text, all_phrases, scorer=fuzz.ratio)
    if match is None:
        return None, 0
    canonical = alias_to_intent.get(match)
    return (canonical, score) if canonical else (None, score)


def build_grammar_phrases(alias_to_intent: dict[str, str]) -> list[str]:
    """Build recognition grammar"""
    phrases = set()
    for phrase in alias_to_intent.keys():
        base = phrase.lower().strip()
        phrases.add(base)
        for w in WAKE_WORDS:
            phrases.add(f"{w} {base}")
    for w in WAKE_WORDS:
        phrases.add(w)
    return sorted(phrases)


# ---------------- Main ----------------
def main():
    if not os.path.exists(MODEL_PATH):
        logging.error(f"Vosk model not found at {MODEL_PATH}")
        say("Vosk model not found. Please put the model in the folder.")
        sys.exit(1)

    intents, alias_to_intent = load_commands()

    model = Model(MODEL_PATH)
    grammar_list = build_grammar_phrases(alias_to_intent)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE, json.dumps(grammar_list))

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )
    stream.start_stream()

    logging.info("Voice agent running. Say 'hey agent' + command.")
    say("Voice agent ready.")

    try:
        while True:
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower().strip()

                if not text:
                    continue

                logging.info(f"Heard: {text}")

                if any(text == w for w in WAKE_WORDS):
                    say("Yes, I am listening.")
                    continue

                if any(w in text for w in WAKE_WORDS):
                    text = strip_wake(text)

                if not text:
                    continue

                intent, score = best_intent_match(text, alias_to_intent)

                if intent and score >= FUZZY_THRESHOLD:
                    cfg = intents[intent]
                    argument = None
                    if cfg.get("type") == "search" and text.startswith(intent):
                        argument = text[len(intent):].strip()
                    run_action(intent, cfg, argument=argument)
                else:
                    say("Command not recognized.")

    except KeyboardInterrupt:
        logging.info("Exiting...")
        say("Shutting down.")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        engine.stop()


if __name__ == "__main__":
    main()
