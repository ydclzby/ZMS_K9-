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

api_url = "https://api.jamendo.com/v3.0/tracks"

CLIENT_ID = 'cd92fac2'

def get_song(topic):
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
            print(data)
            # Check if any tracks were found
            if data['headers']['status'] == 'success' and data['results']:
                track = data['results'][0]
                # return track['name'], track['artist_name'], track['audio']
                instance = vlc.Instance()
                player = instance.media_player_new()
                media = instance.media_new(track['audio'])
                
                player.set_media(media)
                player.audio_set_volume(100)
                print("Streaming music")
                player.play()

            else:
                return "No suitable tracks found.", None, None
        except requests.RequestException as e:
            return f"An error occurred: {str(e)}", None, None
def main():
    get_song('finance')
    time.sleep(10)

if __name__ == '__main__':
    main()
