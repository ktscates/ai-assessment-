import sounddevice as sd
import soundfile as sf

def test_audio_playback():
    """Test audio playback functionality"""
    try:
        # Generate a simple test tone
        duration = 2  # seconds
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        frequency = 440  # Hz
        audio_data = np.sin(2 * np.pi * frequency * t)

        # Save to temporary file
        temp_file = "test_audio.wav"
        sf.write(temp_file, audio_data, sample_rate)

        # Play the audio
        data, sr = sf.read(temp_file)
        print("Playing test audio...")
        sd.play(data, sr)
        sd.wait()
        print("Test audio played successfully")

        # Clean up
        os.remove(temp_file)
        return True
    except Exception as e:
        print(f"Audio playback test failed: {e}")
        return False