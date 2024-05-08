import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import speech_recognition as sr
import requests
import feedparser
from playsound import playsound
from urllib.parse import urlparse

itunes_search_url = "https://itunes.apple.com/search"
# Initialize the recognizer
api_key = 'pi8pPj2tKQ21SjXaWZhRH5QJHemD1VUh9OCNk4_mxZll'
service_url = 'https://api.us-south.assistant.watson.cloud.ibm.com/instances/331ce7d9-5f6f-4f18-ae44-6418b93a1753'
assistant_id = '7d57aa96-2f2f-472a-8427-85181a6f5768'

def first_podcast(topic):
    
    # Parameters for searching podcasts
    params = {
        "term": topic,  # Replace with the desired podcast search term
        "media": "podcast",
        "limit": 1  # We're looking for just the first matching podcast
    }


    response = requests.get(itunes_search_url, params=params)

    # Check the API response and get the podcast's RSS feed URL
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        
        if results:
            # Get the RSS feed URL of the first podcast in the search results
            feed_url = results[0].get("feedUrl")
            print(f"Podcast RSS Feed: {feed_url}")

            # Parse the RSS feed to get episodes
            feed = feedparser.parse(feed_url)
            
            if feed.entries:
                # Retrieve the URL of the first episode
                first_episode_url = feed.entries[0].enclosures[0].href
                print(f"First Episode URL: {first_episode_url}")

                
                parsed_url = urlparse(first_episode_url)
                episode_name = os.path.basename(parsed_url.path)
                
                # Download the episode to a local file
                local_filename = "../data/" + episode_name
                print(f"Downloading to {local_filename}...")
                response = requests.get(first_episode_url, stream=True)
                
                if response.status_code == 200:
                    with open(local_filename, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            file.write(chunk)
                    
                    # Play the downloaded episode using playsound
                    print("Playing the first episode...")
                    playsound(local_filename)
                else:
                    print(f"Failed to download the episode: {response.status_code}")
    else:
        print(f"Error fetching data: {response.status_code}")


def main():
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
#             recognizer = sr.Recognizer()

# # Use a microphone to capture audio
#             with sr.Microphone() as mic:
#                 # Adjust for ambient noise
#                 recognizer.adjust_for_ambient_noise(mic)

#                 print("Listening for 5 seconds...")

#                 # Listen for 5 seconds
#                 audio_data = recognizer.listen(mic, timeout=5, phrase_time_limit=5)
                
#             recognized_text = recognizer.recognize_google(audio_data)

            user_input = input('u:')
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
                response_str = response['output']['generic'][0]['text']
                #print("Assistant:", response['output']['generic'][0]['text'])
                if response_str[1] == '0':
                    print(response_str[5:])
                elif response_str[1] == '1':
                    first_podcast(response_str[5:])
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
