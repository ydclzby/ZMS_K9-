import os 
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.get_authenticator import IAMAuthenticator
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
import numpy as np

# api settings
itunes_search_url = "https://itunes.apple.com/search"

api_key = "pi8pPj2tKQ21SjXaWZhRH5QJHemD1VUh9OCNk4_mxZll"
service_url = "https://api.us-south.assistant.watson.cloud.ibm.com/instances/331ce7d9-5f6f-4f18-ae44-6418b93a1753"
assistant_id = "7d57aa96-2f2f-472a-8427-85181a6f5768"

news_api_key = "a0ff4132-cf60-48d7-b23f-d0523e7c67aa"
news_endpoint = "https://content.guardianapis.com/search"

threading_lock = threading.Lock()
podcast_lock = threading.Lock()
music_lock = threading.Lock()

podcast_history_fp = "../data/history/playback_history.json"

api_url = "https://api.jamendo.com/v3.0/tracks"

CLIENT_ID = 'cd92fac2'

# class

# Podcast Class
class PodcastPlayer(object):
    def __init__(self, history_fp):
        self.history_fp = history_fp
        self.player = None
        self.current_start_time = None
        self.paused_arg = False
        self.quit_arg = False
        self.history_data = {}
        self.control_command = None
    
    def read_podcast_history(self):
        try:
            with open(self.history_fp, "r") as file:
                self.history_data = json.load(file)
        except FileNotFoundError:
            print(f"No history file found at {self.history_fp}.")
            self.history_data = None
    
    def save_padcast_history(self):
        with open(self.history_fp, "w") as file:
            json.dump(self.history_data, file, indent=4)  # Save only a single episode
        print(f"Playback history saved to {self.history_fp}")
        
    def first_podcast(self, topic):
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
                    self.player = instance.media_player_new()
                    media = instance.media_new(first_episode_url)

                    self.player.set_media(media)
                    self.player.audio_set_volume(100)  # Adjust volume
                    print("Streaming the first episode...")
                    self.player.play()

                    # Record the start time and add a record to the history
                    self.current_start_time = time.time()
                    history_entry = {
                        "title": episode_title,
                        "url": first_episode_url,
                        "duration_listened": 0  # Initialize with zero; updated when stopping
                    }
                    self.history_data = history_entry  # Replace existing entries with the new one
                    self.control_playback()
        else:
            print(f"Error fetching data: {response.status_code}")
    
    def control_playback(self):
        while True:
            command = self.control_command
            with podcast_lock:
                if command == "stop" and self.player and not self.paused_arg:
                    print("Pausing playback...")
                    self.player.pause()
                    self.paused_arg = True
                    if self.current_start_time is not None:
                        elapsed_time = time.time() - self.current_start_time
                        self.history_data["duration_listened"] += elapsed_time
                    self.control_command = None
                elif command == "resume" and self.player and self.paused_arg:
                    print("Resuming playback...")
                    self.player.play()
                    self.paused_arg = False
                    self.current_start_time = time.time()
                    self.control_command = None
                elif command == "quit":
                    print("Quitting playback and updating history...")
                    self.quit_arg = True
                    if self.player:
                        self.player.stop()
                    # Update the final duration listened
                    if self.current_start_time is not None:
                        elapsed_time = time.time() - self.current_start_time
                        self.history_data["duration_listened"] += elapsed_time
                    self.save_padcast_history()
                    self.control_command = None
                    break
                else:
                    pass
        
    def play_history(self):
        self.read_podcast_history()
        if not self.history_data:
            return
        
        url = self.history_data["url"]
        duration_listened = self.history_data["duration_listened"]
        print(f"Resuming '{self.history_data['title']}' from {duration_listened} seconds...")
        
        instance = vlc.Instance()
        self.player = instance.media_player_new()
        media = instance.media_new(url)
        
        self.player.set_media(media)
        self.player.audio_set_volume(100)  # Adjust volume
        self.player.play()
        
        while self.player.get_state() not in (vlc.State.Playing, vlc.State.Paused):
            time.sleep(0.1)
        self.player.set_time(int(duration_listened * 1000))

        self.paused_arg = False
        self.current_start_time = time.time()
        self.control_playback()
                   
    def update_control_command(self, new_command):
        self.control_command = new_command             

# News Class
class NewsPlayer(object):
    def __init__(self):
        self.control_command = None
        self.player = None
          
    def get_news(self, topic):
        #get news url
        quit = False
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
            player = vlc.MediaPlayer()
            # Display the content of the article
            for p in paragraphs:
                if not quit:
                    with open("../data/news_content.txt", 'a') as file:
                        file.write('\n' + p.get_text())
                    print(p.get_text())
                    tts = gTTS(text=p.get_text(), lang='en')
                    tts_file = "temp_speech.mp3"
                    tts.save(tts_file)
                    self.player = None
                    media = vlc.Media(tts_file)
                    instance = vlc.Instance()
                    self.player = instance.media_player_new()
                    self.player.set_media(media)
                    self.player.play()
                    
                    while self.player.is_playing():
                        if self.control_command == "quit":
                            quit = True
                            self.player.stop()
                            self.player = None
                            self.control_command = None
                            break
                    os.remove(tts_file)
        else:
            print('Failed to fetch the article content. Status Code:', response.status_code)

    def read_text(self, text_to_speak):
        tts = gTTS(text=text_to_speak, lang='en')
    
        # Save the speech as a temporary file
        tts_file = "temp_speech.mp3"
        tts.save(tts_file)
        
        # Play the speech using playsound
        playsound(tts_file)
        
        # Delete the temporary file
        os.remove(tts_file)

    def update_control_command(self, new_command):
        self.control_command = new_command 

# Music Class
class MusicPlayer(object):
    def __init__(self):
        self.control_command = None
        self.player = None
        self.paused_arg = False
        self.quit_arg = False
        
    def get_song(self, topic):
        params = {
            'client_id': CLIENT_ID,
            'format': 'json',
            'limit': 1,  # Get only the top result
            'tags': topic,
            'order': 'popularity_total_desc'
        }
        
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()  # Raises an exception for HTTP error responses
            
            # Parse the JSON response
            data = response.json()
            
            # Check if any tracks were found
            if data['headers']['status'] == 'success' and data['results']:
                track = data['results'][0]
                # return track['name'], track['artist_name'], track['audio']
                instance = vlc.Instance()
                self.player = instance.media_player_new()
                media = instance.media_new(track['audio'])
                
                self.player.set_media(media)
                self.player.audio_set_volume(100)
                print("Streaming music")
                self.player.play()
                self.control_playback()

            else:
                return "No suitable tracks found.", None, None
        except requests.RequestException as e:
            return f"An error occurred: {str(e)}", None, None

    def control_playback(self):
        while True:
            command = self.control_command
            with music_lock:
                if command == "stop" and self.player and not self.paused_arg:
                    print("Pausing the song...")
                    self.player.pause()
                    self.paused_arg = True
                    self.control_command = None

                elif command == "resume" and self.player and self.paused_arg:
                    print("Resuming playback...")
                    self.player.play()
                    self.paused_arg = False
                    self.control_command = None

                elif command == "quit":
                    print("Quitting the song...")
                    self.quit_arg = True
                    if self.player:
                        self.player.stop()
                    self.control_command = None
                    break
                else:
                    pass 
    
    def update_control_command(self, new_command):
        self.control_command = new_command
        

# SysState Class
class SysState(object):
    def __init__(self):
        self.podcastPlayer = PodcastPlayer(podcast_history_fp)
        self.newsPlayer = NewsPlayer()
        self.musicPlayer = MusicPlayer()
        self.mode = None
        self.wait_command = True
        self.command_text = ""
        self.response = ""
        self.topic = ""
        self.control_command = "none"
        self.audio_queue = queue.Queue()
        self.mic = True
        
    def chatbot_thread(self):
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
                if(self.wait_command == False):

                    self.podcastPlayer.update_control_command(None)
                    self.newsPlayer.update_control_command(None)
                    self.musicPlayer.update_control_command(None)
                    
                    print("------------------")
                    print("user input is:", self.command_text)
                    # Send a message to the chatbot
                    message_input = {
                        'message_type': 'text',
                        'text': self.command_text
                    }

                    response = assistant.message(
                        assistant_id=assistant_id,
                        session_id=session_id,
                        input=message_input
                    ).get_result()

                    # Print the chatbot's response
                    if response['output']['generic']:
                        self.response = response['output']['generic'][0]['text']
                        response_label = response['output']['generic'][-1]['text'][1]
                        response_content = ""
                        for message in response['output']['generic']:
                            response_content += message['text'][5:]

                        #print("Assistant:", response['output']['generic'][0]['text'])
                        if response_label == '0': #unknown commands
                            print("unknown command")
                        elif response_label == '1': #plain text
                            print(response_content)
                            with threading_lock:
                                self.mode = "1"
                                self.topic = response_content
                        elif response_label == '2': #podcast
                            self.mic = True
                            if response_content == "continue_podcast":
                                print("continue_podcast")
                                
                                with threading_lock:
                                    self.mode = "2.1"
                                print('out of lock')
                            else:
                                
                                print("new_podcast")
                                with threading_lock:
                                    self.mode = "2.2"
                                    self.topic = response_content
                        elif response_label == '3': #news
                            self.mic = True
                            with threading_lock:
                                self.mode = "3"
                                self.topic = response_content
                        elif response_label == '4': #music
                            self.mic = True
                            with threading_lock:
                                self.mode = "4"
                                self.topic = response_content
                        elif response_label == '5': #control
                            self.mic = True
                            print("control command")
                            print(response_content)
                            with threading_lock:
                                self.mode = "5"
                                self.control_command = response_content
                                self.podcastPlayer.update_control_command(self.control_command)
                                self.newsPlayer.update_control_command(self.control_command)
                                self.musicPlayer.update_control_command(self.control_command)
                        elif response_label == '6':
                            self.mic = True
                            print(response_content)
                            with threading_lock:
                                self.mode = "6"
                            print('out of lock')
                        with threading_lock:
                            self.wait_command = True
                    else:
                        print("Assistant: No response generated.")


        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Always try to close the session
            if 'session_id' in locals():  # Check if session was created
                assistant.delete_session(assistant_id=assistant_id, session_id=session_id)
        
    def audio_thread(self):
        while True:
            if self.mic == False:
                continue
            else:
                recognizer = sr.Recognizer()
                mic = sr.Microphone()
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source)
                    print("Ready to receive audio...")
                    try:
                        print('mic on')
                        audio = recognizer.listen(source, timeout=5.0, phrase_time_limit=3.0)
                        
                        recognized_text = recognizer.recognize_google(audio)
                        print("You said:", recognized_text)
                        #recognized_text = input('user:')
                        keywords = {"stop", "continue", "quit", "name"}
                        detected_keywords = [kw for kw in keywords if kw in recognized_text.lower()]
                        if detected_keywords:
                            print("keyword detected")
                        self.command_text = recognized_text
                        self.wait_command = False
                        self.mic = False
                        print('mic off')
                    except Exception as e:
                        print(f"Error capturing audio: {e}")

    def recognize_thread(self):
        recognizer = sr.Recognizer()
        while True:
            if not self.audio_queue.empty():
                audio = self.audio_queue.get()

                try:
                    # raw_data = audio.get_wav_data()
                    # np_data = np.frombuffer(raw_data, dtype=np.int16)
                    # clean_data = reduce_noise(np_data)
                    # recognized_text = recognizer.recognize_google(audio)
                    recognized_text = input('use:')
                    print("You said:", recognized_text)
                    
                    keywords = {"stop", "continue", "quit", "name"}
                    detected_keywords = [kw for kw in keywords if kw in recognized_text.lower()]
                    if detected_keywords:
                        print("keyword detected")
                    
                    if detected_keywords or self.wait_command:
                        with threading_lock:
                            self.command_text = recognized_text
                            self.wait_command = False
                        print(self.wait_command)
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")

    def mode_thread(self):    
        while True:

            if self.mode == "0":
                pass
            elif self.mode == "1":
                self.newsPlayer.read_text(self.topic)
                self.mic = True
            elif self.mode == "2.1":
                self.podcastPlayer.play_history()
            elif self.mode == "2.2":
                self.podcastPlayer.first_podcast(self.topic)
            elif self.mode == "3":
                self.newsPlayer.get_news(self.topic)
            elif self.mode == "4":
                self.musicPlayer.get_song(self.topic)
        
            else:
                pass
            
            with threading_lock:
                self.mode = "0"


#chatbot response
#{0} ---> response for unknown command
#{1} ---> return plain text
#{2} ---> for podcast
#{3} ---> for news
#{4} ---> for music
#{5} ---> control command(stop, continue and quit)

def main():
    ibm_Chatbot = SysState()
    
    threading.Thread(target=ibm_Chatbot.chatbot_thread).start()
    #threading.Thread(target=listening_thread).start()
    threading.Thread(target=ibm_Chatbot.audio_thread).start()
    #threading.Thread(target=ibm_Chatbot.recognize_thread, daemon=True).start()
    threading.Thread(target=ibm_Chatbot.mode_thread).start()


if __name__ == '__main__':
    main()