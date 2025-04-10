import sounddevice as sd
import numpy as np
import sys

def list_audio_devices():
    """List all available audio devices"""
    print("\nAvailable Audio Devices:")
    print("-" * 50)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"Device {i}: {device['name']}")
        print(f"  Max Input Channels: {device['max_input_channels']}")
        print(f"  Default Sample Rate: {device['default_samplerate']}")
        print("-" * 50)

def test_microphone():
    """Test microphone with detailed feedback"""
    print("\nStarting Microphone Test...")
    print("Please speak into your microphone...")
    
    # Audio parameters
    duration = 5  # seconds
    sample_rate = 16000
    channels = 1
    
    try:
        # List devices before starting
        list_audio_devices()
        
        # Get default input device info
        device_info = sd.query_devices(kind='input')
        print(f"\nUsing Input Device: {device_info['name']}")
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            volume_norm = np.linalg.norm(indata) * 10
            print(f"Audio level: {volume_norm:.2f}")
        
        # Create and start the input stream
        with sd.InputStream(callback=audio_callback,
                          channels=channels,
                          samplerate=sample_rate):
            print("\nRecording started...")
            print("Speak now (recording for 5 seconds)...")
            sd.sleep(int(duration * 1000))
            print("\nRecording finished.")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Check if your microphone is properly connected")
        print("2. Check if your microphone is set as the default input device")
        print("3. Check if your microphone has necessary permissions")
        print("4. Try selecting a specific input device")

if __name__ == "__main__":
    print("=== Microphone Test Program ===")
    test_microphone()