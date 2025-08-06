# src/audio/sfx.py
from pathlib import Path
import random
from playsound import playsound

SND_DIR = Path(__file__).parent / "sounds" / "frog"
CROAKS  = sorted(SND_DIR.glob("*.wav"))      # cualquier .wav

def croak():
    if not CROAKS:
        print(f"⚠️  No hay WAV en {SND_DIR}")
        return
    playsound(str(random.choice(CROAKS)), block=True)
