import speech_recognition as sr

def listening_thread():
    global wait_command
    global command_text

    # Initialize the recognizer
    recognizer = sr.Recognizer()
    with sr.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic)
        while(True):
                print("Listening...")

                audio_data = recognizer.listen(mic, timeout=10, phrase_time_limit=3)

                # Recognize the speech and save it to a text file
                try:
                    # Recognize speech using Google Speech-to-Text
                    recognized_text = recognizer.recognize_google(audio_data)
                    print("You said:", recognized_text)

                    #key word detection
                    if "stop" in recognized_text:
                         print("stop detected")
                    elif "continue" in recognized_text:
                         print("continue detected")
                    elif "quit" in recognized_text:
                         print("quit detected")

                except sr.UnknownValueError:
                    print("Could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Error with the speech recognition service; {e}")

def main():
     listening_thread()
    
if __name__ == "__main__":
     main()