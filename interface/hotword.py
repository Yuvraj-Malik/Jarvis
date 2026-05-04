import pvporcupine
import struct
import os
from dotenv import load_dotenv

try:
    import pyaudio
except ImportError:
    pyaudio = None

load_dotenv()
ACCESS_KEY = os.getenv("PICOVOICE_API_KEY") # Ensure this is in your .env file
_WAKE_WORD_WARNING_SHOWN = False

def listen_for_wake_word():
    """
    Blocks execution until 'Jarvis' is heard.
    Ignores music and background noise.
    """
    porcupine = None
    pa = None
    audio_stream = None

    try:
        global _WAKE_WORD_WARNING_SHOWN
        if pyaudio is None:
            if not _WAKE_WORD_WARNING_SHOWN:
                print("Wake-word disabled: 'pyaudio' is not installed. Type commands instead.")
                _WAKE_WORD_WARNING_SHOWN = True
            return False

        # Check if Key exists
        if not ACCESS_KEY:
            print("❌ Error: PICOVOICE_API_KEY missing in .env")
            return False

        # Init Porcupine
        porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=["jarvis"])
        
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print("🦅 Guard Mode: Listening for 'Jarvis'...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                print("⚡ Wake Word Detected!")
                return True

    except Exception as e:
        print(f"Hotword Error: {e}")
        return False

    finally:
        if porcupine: porcupine.delete()
        if audio_stream: audio_stream.close()
        if pa: pa.terminate()