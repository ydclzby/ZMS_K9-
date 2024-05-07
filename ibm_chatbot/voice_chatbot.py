from gtts import gTTS
import speech_recognition as sr
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import time

api_key = 'MD6EtN06mXxtG-cncRkrZCT0Ckt3Hj3rX91FjnbNj4G6'
service_url = 'https://api.us-south.assistant.watson.cloud.ibm.com/instances/a556627a-309f-4fed-aad4-23962294f55a'
assistant_id = 'a6973f24-9444-446a-bdb1-647949cdf540'
user_request= ""

recognizer = sr.Recognizer()

authenticator = IAMAuthenticator(api_key)
assistant = AssistantV2(
    version='2024-05-03', 
    authenticator=authenticator
)
assistant.set_service_url(service_url)
response = assistant.create_session(assistant_id=assistant_id).get_result()
session_id = response['session_id']


def voice_detect(recognizer):
    with sr.Microphone() as mic:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(mic)

        print("Listening...")

        # Listen for 5 seconds
        audio_data = recognizer.listen(mic, timeout=5, phrase_time_limit=3)

    # Recognize the speech and save it to a text file
    try:
        # Recognize speech using Google Speech-to-Text
        recognized_text = recognizer.recognize_google(audio_data)
        #print("You said:", recognized_text)
        audio_text = recognized_text
        return audio_text
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        audio_text = "Could not understand the audio."
        return ""
        

def get_response(text_input):
    message_input = {
        'message_type': 'text',
        'text': text_input
    }

    response = assistant.message(
        assistant_id=assistant_id,
        session_id=session_id,
        input=message_input
    ).get_result()

    return response['output']['generic'][0]['text']

def play_response(chatbot_response):
    # Create a gTTS object
    tts = gTTS(text=chatbot_response, lang="en")  # Change 'en' to your desired language code

    # Save the speech to an MP3 file in the current directory
    filename = "example.mp3"  # Filename to save the audio
    tts.save(filename)  # This saves the file in the current directory

    # Play the MP3 file using the appropriate system command
    if os.name == "posix":
        # For macOS and Linux
        os.system(f"open {filename}")  # macOS
        # os.system(f"xdg-open {filename}")  # Linux
    else:
        # For Windows
        os.system(f"start {filename}")

def main():
    while(True):
        audio_text = voice_detect(recognizer)
        if(audio_text != ""):
            print("You said:", audio_text)
            text_response = get_response(audio_text)
            play_response(text_response)
        
        time.sleep(5)


#assistant.delete_session(assistant_id=assistant_id, session_id=session_id)
            
if __name__ == '__main__':
    main()
