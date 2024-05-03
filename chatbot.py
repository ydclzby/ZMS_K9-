import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

import speech_recognition as sr

# Initialize the recognizer




def main():
    api_key = 'pi8pPj2tKQ21SjXaWZhRH5QJHemD1VUh9OCNk4_mxZll'
    service_url = 'https://api.us-south.assistant.watson.cloud.ibm.com/instances/331ce7d9-5f6f-4f18-ae44-6418b93a1753'
    assistant_id = '7d57aa96-2f2f-472a-8427-85181a6f5768'

    # Set up the authenticator and assistant
    authenticator = IAMAuthenticator(api_key)
    assistant = AssistantV2(
        version='2024-05-03',  # Use the correct version date
        authenticator=authenticator
    )
    assistant.set_service_url(service_url)

    # Create a new session
    try:
        response = assistant.create_session(assistant_id=assistant_id).get_result()
        session_id = response['session_id']

        while True:
            # Get input from the user
            recognizer = sr.Recognizer()

# Use a microphone to capture audio
            with sr.Microphone() as mic:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(mic)

                print("Listening for 5 seconds...")

                # Listen for 5 seconds
                audio_data = recognizer.listen(mic, timeout=5, phrase_time_limit=5)
                
            recognized_text = recognizer.recognize_google(audio_data)

            user_input = recognized_text
            if user_input.lower() == 'quit':
                break

            # Send a message to the chatbot
            message_input = {
                'message_type': 'text',
                'text': user_input
            }

            response = assistant.message(
                assistant_id=assistant_id,
                session_id=session_id,
                input=message_input
            ).get_result()

            # Print the chatbot's response
            if response['output']['generic']:
                print("Assistant:", response['output']['generic'][0]['text'])
            else:
                print("Assistant: No response generated.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Always try to close the session
        if 'session_id' in locals():  # Check if session was created
            assistant.delete_session(assistant_id=assistant_id, session_id=session_id)

if __name__ == "__main__":
    main()
