import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import speech_recognition as sr
import requests
import feedparser
from playsound import playsound
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pyttsx3
import threading

itunes_search_url = "https://itunes.apple.com/search"
# Initialize the recognizer
api_key = 'pi8pPj2tKQ21SjXaWZhRH5QJHemD1VUh9OCNk4_mxZll'
service_url = 'https://api.us-south.assistant.watson.cloud.ibm.com/instances/331ce7d9-5f6f-4f18-ae44-6418b93a1753'
assistant_id = '7d57aa96-2f2f-472a-8427-85181a6f5768'

news_api_key = 'a0ff4132-cf60-48d7-b23f-d0523e7c67aa' 
news_endpoint = 'https://content.guardianapis.com/search'

wait_command = False
command_text = ""
lock = threading.Lock()

def get_news(topic):
    #get news url
    params = {
        'api-key': news_api_key,
        'q': topic,  # Search term, can be customized
        'page-size': 1,  # Number of results per page
        'order-by': 'relevance',  # or relevance
    }

    response = requests.get(news_endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        articles = data.get('response', {}).get('results', [])

        for article in articles:
            news_title = article.get('webTitle', 'No title')
            news_url = article.get('webUrl', '#')
            print(f"Title: {news_title}")
            print(f"URL: {news_url}")
            print()
    else:
        print("Failed to fetch content. HTTP status code:", response.status_code)
    
    #get news content
    response = requests.get(news_url)

    if response.status_code == 200:
        #clear the original txt file
        with open("../data/news_content.txt", 'w') as file:
            pass

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract relevant parts of the article (e.g., the headline and content)
        headline = soup.find('h1')  # Assuming the headline is in an <h1> tag
        paragraphs = soup.find_all('p')  # Extract all paragraph content

        # Display the headline
        if headline:
            print(f"Headline: {headline.get_text()}")

        # Display the content of the article
        for p in paragraphs:
            with open("../data/news_content.txt", 'a') as file:
                file.write('\n' + p.get_text())
            print(p.get_text())
    else:
        print('Failed to fetch the article content. Status Code:', response.status_code)

def read_news():
    with open("../data/news_content.txt", "r") as file:
        news_text = file.read()

    # # Convert the text to speech
    # tts = gTTS(text=news_text, lang="en")
    # output_file = "../data/news_sound.mp3"
    # tts.save(output_file)

    # playsound('../data/news_sound.mp3')
        
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')  # Get available voices
    engine.setProperty('voice', voices[14].id)  # Choose a voice male:14 female:66
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1)  # Volume (0 to 1)
    engine.say(news_text)
    engine.runAndWait()

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
                local_filename = "../data/podcast.m4a"
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

def chatbot_thread():
    global wait_command
    global command_text

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
            if(wait_command == False):
                #user_input = input('u:')
                user_input = command_text
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
                        engine = pyttsx3.init()
                        voices = engine.getProperty('voices')  # Get available voices
                        engine.setProperty('voice', voices[14].id)  # Choose a voice male:14 female:66
                        engine.setProperty('rate', 150)  # Speed of speech
                        engine.setProperty('volume', 1)  # Volume (0 to 1)
                        engine.say(response_str[5:])
                        engine.runAndWait()
                    elif response_str[1] == '1':
                        first_podcast(response_str[5:])
                    elif response_str[1] == '2':
                        get_news(response_str[5:])
                        read_news()
                else:
                    print("Assistant: No response generated.")

                with lock:
                    wait_command = not wait_command


    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Always try to close the session
        if 'session_id' in locals():  # Check if session was created
            assistant.delete_session(assistant_id=assistant_id, session_id=session_id)

def listening_thread():
    global wait_command
    global command_text

    # Initialize the recognizer
    recognizer = sr.Recognizer()
    while(True):
        # Use a microphone to capture audio
        if(wait_command == True):
            with sr.Microphone() as mic:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(mic)

                print("Listening...")

                audio_data = recognizer.listen(mic, timeout=5, phrase_time_limit=3)

                # Recognize the speech and save it to a text file
                try:
                    # Recognize speech using Google Speech-to-Text
                    recognized_text = recognizer.recognize_google(audio_data)
                    print("You said:", recognized_text)

                    with lock:
                        command_text = recognized_text

                except sr.UnknownValueError:
                    print("Could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Error with the speech recognition service; {e}")
            with lock:
                wait_command = not wait_command

def main():
    threading.Thread(target=chatbot_thread).start()
    threading.Thread(target=listening_thread).start()

if __name__ == "__main__":
    main()
