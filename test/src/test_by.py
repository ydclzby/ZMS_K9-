import os
import queue
import threading
import time
import speech_recognition as sr
import noisereduce as nr
import numpy as np
import json

# This function is to be called after capturing the audio
def reduce_noise(audio_data):
    # Assuming 'audio_data' is a numpy array containing the audio waveform
    reduced_data = nr.reduce_noise(y=audio_data, sr=16000)
    return reduced_data

def audio_thread(audio_queue):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Ready to receive audio...")
        while True:
            try:
                audio = recognizer.listen(source, timeout=5.0, phrase_time_limit=5.0)
                audio_queue.put(audio)
            except Exception as e:
                print(f"Error capturing audio: {e}")

def recognize_thread(audio_queue):
    recognizer = sr.Recognizer()
    while True:
        if not audio_queue.empty():
            audio = audio_queue.get()
            try:
                # Convert SpeechRecognition audio data to NumPy array for processing
                raw_data = audio.get_wav_data()
                np_data = np.frombuffer(raw_data, dtype=np.int16)
                clean_data = reduce_noise(np_data)
                # Process cleaned audio...
                recognized_text = recognizer.recognize_google(audio)
                print("You said:", recognized_text)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

def main():
    # audio_queue = queue.Queue()

    # # Create and start the audio capture thread
    # threading.Thread(target=audio_thread, args=(audio_queue,), daemon=True).start()

    # # Create and start the speech recognition thread
    # threading.Thread(target=recognize_thread, args=(audio_queue,), daemon=True).start()

    # # Keep the main thread alive to let the other threads run continuously
    # while True:
    #     time.sleep(0.1)
    file_path = "1.json"
    with open(file_path, "r") as file:
        a = json.load(file)
    print(type(a))
    print("\n")
    print(a["url"])

if __name__ == "__main__":
    main()