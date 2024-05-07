import speech_recognition as sr

# Initialize the recognizer
recognizer = sr.Recognizer()

# Use a microphone to capture audio
with sr.Microphone() as mic:
    # Adjust for ambient noise
    recognizer.adjust_for_ambient_noise(mic)

    print("Listening for 5 seconds...")

    # Listen for 5 seconds
    audio_data = recognizer.listen(mic, timeout=5, phrase_time_limit=3)

    print(type(audio_data))

# Recognize the speech and save it to a text file
try:
    # Recognize speech using Google Speech-to-Text
    recognized_text = recognizer.recognize_google(audio_data)
    print("You said:", recognized_text)

    # Save the recognized text to a file in the current directory
    file_path = "recognized_text.txt"  # This will be saved in the current directory
    with open(file_path, "w") as file:
        file.write(recognized_text)

except sr.UnknownValueError:
    print("Could not understand the audio.")
except sr.RequestError as e:
    print(f"Error with the speech recognition service; {e}")
