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
import queue
from gtts import gTTS
from datetime import datetime
import noisereduce as nr
import numpy as np

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

class ChatbotState(object):
    def __init__(self, history_file):
        self.history_file = history_file
        self.wait_command = True
        self.command_text = ""
        self.control_command = "none"
        self.mode = ""
        self.topic = ""
        
        self.player = None
        self.paused = False
        self.quit_playback = False
        self.current_start_time = None
        self.history = []



threading_lock = threading.Lock()


#podcast
history_file = "../data/history/playback_history.json"
ibm_Chatbot = ChatbotState(history_file)

podcast_lock = threading.Lock()

def reduce_noise(audio_data):
    # Assuming 'audio_data' is a numpy array containing the audio waveform
    reduced_data = nr.reduce_noise(y=audio_data, sr=16000)
    return reduced_data

def read_text(text_to_speak): 
    # Create a gTTS object
    tts = gTTS(text=text_to_speak, lang='en')
    
    # Save the speech as a temporary file
    tts_file = "temp_speech.mp3"
    tts.save(tts_file)
    
    # Play the speech using playsound
    playsound(tts_file)
    
    # Delete the temporary file
    os.remove(tts_file)

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
    #global player, paused, current_start_time, control_command
    if not episode:
        return

    url = episode["url"]
    duration_listened = episode["duration_listened"]
    print(f"Resuming '{episode['title']}' from {duration_listened} seconds...")

    instance = vlc.Instance()
    ibm_Chatbot.player = instance.media_player_new()
    media = instance.media_new(url)

    ibm_Chatbot.player.set_media(media)
    ibm_Chatbot.player.audio_set_volume(100)  # Adjust volume
    ibm_Chatbot.player.play()

    # Wait for the media player to be ready, then seek to the appropriate position
    while ibm_Chatbot.player.get_state() not in (vlc.State.Playing, vlc.State.Paused):
        time.sleep(0.1)
    ibm_Chatbot.player.set_time(int(duration_listened * 1000))  # VLC time is in milliseconds

    ibm_Chatbot.paused = False
    ibm_Chatbot.current_start_time = time.time()
    control_playback(episode)

def control_playback(episode):
    #global control_command
    """Control playback with user commands like stop, resume, or quit."""
    #global paused, player, current_start_time
    while True:
        #command = input("Enter command (stop/resume/quit): ").strip().lower()
        command = ibm_Chatbot.control_command
        with podcast_lock:
            if command == "stop" and ibm_Chatbot.player and not ibm_Chatbot.paused:
                print("Pausing playback...")
                ibm_Chatbot.player.pause()
                ibm_Chatbot.paused = True
                if ibm_Chatbot.current_start_time is not None:
                    elapsed_time = time.time() - ibm_Chatbot.current_start_time
                    episode["duration_listened"] += elapsed_time
            elif command == "resume" and ibm_Chatbot.player and ibm_Chatbot.paused:
                print("Resuming playback...")
                ibm_Chatbot.player.play()
                ibm_Chatbot.paused = False
                ibm_Chatbot.current_start_time = time.time()
            elif command == "quit":
                print("Quitting playback and updating history...")
                ibm_Chatbot.quit_playback = True
                if ibm_Chatbot.player:
                    ibm_Chatbot.player.stop()
                # Update the final duration listened
                if ibm_Chatbot.current_start_time is not None:
                    elapsed_time = time.time() - ibm_Chatbot.current_start_time
                    episode["duration_listened"] += elapsed_time
                save_history_to_json(history_file, episode)
                break
            else:
                pass
                #print(f"Invalid command or action not applicable: {command}")

def first_podcast(topic):
    #global player, current_start_time, history, control_command
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
                ibm_Chatbot.player = instance.media_player_new()
                media = instance.media_new(first_episode_url)

                ibm_Chatbot.player.set_media(media)
                ibm_Chatbot.player.audio_set_volume(100)  # Adjust volume
                print("Streaming the first episode...")
                ibm_Chatbot.player.play()

                # Record the start time and add a record to the history
                ibm_Chatbot.current_start_time = time.time()
                history_entry = {
                    "title": episode_title,
                    "url": first_episode_url,
                    "duration_listened": 0  # Initialize with zero; updated when stopping
                }
                ibm_Chatbot.history = [history_entry]  # Replace existing entries with the new one
                control_playback(history_entry)
    else:
        print(f"Error fetching data: {response.status_code}")

#news
def get_news(topic):
    global control_command
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
            if ibm_Chatbot.control_command == "stop" or ibm_Chatbot.control_command == "quit":
                break
            read_text(p.get_text())
    else:
        print('Failed to fetch the article content. Status Code:', response.status_code)

#music

#threadings
#thread for communication with chatbot
def chatbot_thread():
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
            if(ibm_Chatbot.wait_command == False):
                print("chatbot----")
                #user_input = input('u:')
                user_input = ibm_Chatbot.command_text
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
                        with threading_lock:
                            ibm_Chatbot.mode = "1"
                            ibm_Chatbot.topic = response_str[5:]
                    elif response_str[1] == '2': #podcast
                        if response_str[5:] == "continue_podcast":
                            print("continue_podcast")
                            with threading_lock:
                                ibm_Chatbot.mode = "2.1"
                        else:
                            print("new_podcast")
                            with threading_lock:
                                ibm_Chatbot.mode = "2.2"
                                ibm_Chatbot.topic = response_str[5:]
                    elif response_str[1] == '3': #news
                        with threading_lock:
                            ibm_Chatbot.mode = "3"
                            ibm_Chatbot.topic = response_str[5:]
                    elif response_str[1] == '4': #music
                        pass
                    elif response_str[1] == '5': #control
                        print("control command")
                        print(response_str[5:])
                        with threading_lock:
                            ibm_Chatbot.control_command = response_str[5:]
                    
                    with threading_lock:
                        ibm_Chatbot.wait_command = True
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
    # global wait_command
    # global command_text

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

                    if detected_keywords or ibm_Chatbot.wait_command:
                        with threading_lock:
                            ibm_Chatbot.command_text = recognized_text
                            ibm_Chatbot.wait_command = False

                except sr.UnknownValueError:
                    print("Could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Error with the speech recognition service; {e}")

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
                # raw_data = audio.get_wav_data()
                # np_data = np.frombuffer(raw_data, dtype=np.int16)
                # clean_data = reduce_noise(np_data)
                recognized_text = recognizer.recognize_google(audio)
                print("You said:", recognized_text)
                
                keywords = {"stop", "continue", "quit", "name"}
                detected_keywords = [kw for kw in keywords if kw in recognized_text.lower()]
                if detected_keywords:
                    print("keyword detected")
                
                if detected_keywords or ibm_Chatbot.wait_command:
                    with threading_lock:
                        ibm_Chatbot.command_text = recognized_text
                        ibm_Chatbot.wait_command = False
                    print(ibm_Chatbot.wait_command)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

#thread for controlling speaker
def speaking_thread():    
    while True:
        if ibm_Chatbot.mode == "0":
            pass
        elif ibm_Chatbot.mode == "1":
            read_text(ibm_Chatbot.topic)
        elif ibm_Chatbot.mode == "2.1":
            ibm_Chatbot.history = read_history_from_json(history_file)
            episode_to_resume = list_history(ibm_Chatbot.history)
            resume_playback(episode_to_resume)
        elif ibm_Chatbot.mode == "2.2":
            first_podcast(ibm_Chatbot.topic)
        elif ibm_Chatbot.mode == "3":
            get_news(ibm_Chatbot.topic)
        else:
            pass
        with threading_lock:
            ibm_Chatbot.mode = "0"

def main():
    audio_queue = queue.Queue()
    threading.Thread(target=chatbot_thread).start()
    #threading.Thread(target=listening_thread).start()
    threading.Thread(target=audio_thread, args=(audio_queue,), daemon=True).start()
    threading.Thread(target=recognize_thread, args=(audio_queue,), daemon=True).start()
    threading.Thread(target=speaking_thread).start()

if __name__ == "__main__":
    main()
