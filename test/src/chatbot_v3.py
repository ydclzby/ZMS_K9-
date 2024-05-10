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
import vlc
import time
import json

# podcast api
itunes_search_url = "https://itunes.apple.com/search"
# chatbot api
api_key = 'pi8pPj2tKQ21SjXaWZhRH5QJHemD1VUh9OCNk4_mxZll'
service_url = 'https://api.us-south.assistant.watson.cloud.ibm.com/instances/331ce7d9-5f6f-4f18-ae44-6418b93a1753'
assistant_id = '7d57aa96-2f2f-472a-8427-85181a6f5768'
# news api
news_api_key = 'a0ff4132-cf60-48d7-b23f-d0523e7c67aa' 
news_endpoint = 'https://content.guardianapis.com/search'

#chatbot response
#{0} ---> response for unknown command
#{1} ---> return plain text
#{2} ---> for podcast
#{3} ---> for news
#{4} ---> for music
#{5} ---> control command(stop, continue and quit)


wait_command = True
command_text = ""
control_command = "none"
threading_lock = threading.Lock()
mode = ""
topic = ""

#podcast
history_file = "playback_history.json"
player = None
paused = False
quit_playback = False
current_start_time = None
podcast_lock = threading.Lock()
history = []  # This will now store only a single episode

def read_history_from_json(file_path):
    """Read playback history from a JSON file."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"No history file found at {file_path}.")
        return []

def save_history_to_json(file_path, entry):
    """Save a single podcast episode to the JSON file."""
    with open(file_path, "w") as file:
        json.dump([entry], file, indent=4)  # Save only a single episode
    print(f"Playback history saved to {file_path}")

def list_history(history):
    """List the playback history and prompt the user to select an episode."""
    if not history:
        print("No playback history available.")
        return None

    # We assume a single entry in the history file
    episode = history[0]
    print(f"1. {episode['title']}")
    return episode

def resume_playback(episode):
    """Resume playback from the last known point of an episode."""
    global player, paused, current_start_time, control_command
    if not episode:
        return

    url = episode["url"]
    duration_listened = episode["duration_listened"]
    print(f"Resuming '{episode['title']}' from {duration_listened} seconds...")

    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(url)

    player.set_media(media)
    player.audio_set_volume(100)  # Adjust volume
    player.play()

    # Wait for the media player to be ready, then seek to the appropriate position
    while player.get_state() not in (vlc.State.Playing, vlc.State.Paused):
        time.sleep(0.1)
    player.set_time(int(duration_listened * 1000))  # VLC time is in milliseconds

    paused = False
    current_start_time = time.time()
    control_playback(episode)

def control_playback(episode):
    global control_command
    """Control playback with user commands like stop, resume, or quit."""
    global paused, player, current_start_time
    while True:
        #command = input("Enter command (stop/resume/quit): ").strip().lower()
        command = control_command
        with podcast_lock:
            if command == "stop" and player and not paused:
                print("Pausing playback...")
                player.pause()
                paused = True
                if current_start_time is not None:
                    elapsed_time = time.time() - current_start_time
                    episode["duration_listened"] += elapsed_time
            elif command == "resume" and player and paused:
                print("Resuming playback...")
                player.play()
                paused = False
                current_start_time = time.time()
            elif command == "quit":
                print("Quitting playback and updating history...")
                quit_playback = True
                if player:
                    player.stop()
                # Update the final duration listened
                if current_start_time is not None:
                    elapsed_time = time.time() - current_start_time
                    episode["duration_listened"] += elapsed_time
                save_history_to_json(history_file, episode)
                break
            else:
                pass
                #print(f"Invalid command or action not applicable: {command}")

def first_podcast(topic):
    global player, current_start_time, history, control_command
    params = {
        "term": topic,
        "media": "podcast",
        "limit": 1
    }

    response = requests.get(itunes_search_url, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])

        if results:
            feed_url = results[0].get("feedUrl")
            print(f"Podcast RSS Feed: {feed_url}")

            feed = feedparser.parse(feed_url)

            if feed.entries:
                first_episode_url = feed.entries[0].enclosures[0].href
                episode_title = feed.entries[0].title
                print(f"First Episode Title: {episode_title}")
                print(f"First Episode URL: {first_episode_url}")

                instance = vlc.Instance()
                player = instance.media_player_new()
                media = instance.media_new(first_episode_url)

                player.set_media(media)
                player.audio_set_volume(100)  # Adjust volume
                print("Streaming the first episode...")
                player.play()

                # Record the start time and add a record to the history
                current_start_time = time.time()
                history_entry = {
                    "title": episode_title,
                    "url": first_episode_url,
                    "duration_listened": 0  # Initialize with zero; updated when stopping
                }
                history = [history_entry]  # Replace existing entries with the new one
                control_playback(history_entry)
    else:
        print(f"Error fetching data: {response.status_code}")

def play_podcast(topic):
    global history
    history = read_history_from_json(history_file)
    print("Do you want to resume palyback from the history?")
    choice = "yes"
    if choice == "yes":
        episode_to_resume = list_history(history)
        resume_playback(episode_to_resume)
    else:
        topic = input("Enter the podcast topic to search for: ").strip()#should change
        first_podcast(topic)

#news
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

#music

#threadings
#thread for communication with chatbot
def chatbot_thread():
    global wait_command
    global command_text
    global history
    global control_command
    global mode
    global topic

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
                print("chatbot----")
                #user_input = input('u:')
                user_input = command_text
                print("user input is:",user_input)
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
                    if response_str[1] == '0': #unknown commands
                        print("unknown command")
                    elif response_str[1] == '1': #plain text
                        print(response_str[5:])
                    elif response_str[1] == '2': #podcast
                        if response_str[5:] == "continue_podcast":
                            print("continue_podcast")
                            with threading_lock:
                                mode = "2.1"
                        else:
                            print("new_podcast")
                            with threading_lock:
                                mode = "2.2"
                                topic = response_str[5:]
                    elif response_str[1] == '3': #news
                        pass
                    elif response_str[1] == '4': #music
                        pass
                    elif response_str[1] == '5': #control
                        print("control command")
                        print(response_str[5:])
                        with threading_lock:
                            control_command = response_str[5:]
                    
                    with threading_lock:
                        wait_command = True
                else:
                    print("Assistant: No response generated.")


    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Always try to close the session
        if 'session_id' in locals():  # Check if session was created
            assistant.delete_session(assistant_id=assistant_id, session_id=session_id)

#thread for listen what user say
def listening_thread():
    global wait_command
    global command_text

    # Initialize the recognizer
    recognizer = sr.Recognizer()
    with sr.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic)
        while(True):
                print("Listening...")

                audio_data = recognizer.listen(mic, timeout=3, phrase_time_limit=3)

                # Recognize the speech and save it to a text file
                try:
                    # Recognize speech using Google Speech-to-Text
                    recognized_text = recognizer.recognize_google(audio_data)
                    print("You said:", recognized_text)

                    #key word detection
                    keywords = {"stop", "continue", "quit", "name"}
                    detected_keywords = [kw for kw in keywords if kw in recognized_text.lower()]
                    if detected_keywords:
                        print("keyword detected")

                    if detected_keywords or wait_command:
                        with threading_lock:
                            command_text = recognized_text
                            wait_command = False
                        print(wait_command)

                except sr.UnknownValueError:
                    print("Could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Error with the speech recognition service; {e}")

#thread for controlling speaker
def speaking_thread():
    global control_command
    global mode
    global topic
    
    while True:
        if mode == "0":
            pass
        elif mode == "2.1":
            episode_to_resume = list_history(history)
            resume_playback(episode_to_resume)
        elif mode == "2.2":
            first_podcast(topic)
        else:
            pass
        with threading_lock:
            mode = "0"



def main():
    threading.Thread(target=chatbot_thread).start()
    threading.Thread(target=listening_thread).start()
    threading.Thread(target=speaking_thread).start()

if __name__ == "__main__":
    main()
