import soundfile as sf
import sounddevice as sd
import numpy as np
import json
import asyncio
import websockets
import os
from dotenv import load_dotenv

def create_test_audio():
    """Creates a test audio file for verification"""
    try:
        duration = 2  # seconds
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        frequency = 440  # Hz
        amplitude = np.iinfo(np.int16).max
        data = amplitude * np.sin(2 * np.pi * frequency * t)
        data = data.astype(np.int16)

        filename = "test_audio.wav"
        sf.write(filename, data, sample_rate)
        print(f"Test audio file '{filename}' created successfully")
        return filename
    except Exception as e:
        print(f"Error creating test audio: {e}")
        return None