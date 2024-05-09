import requests
from gtts import gTTS
import pygame

# Fetch news (replace with your actual API key)
api_key = 'a0ff4132-cf60-48d7-b23f-d0523e7c67aa'
url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}'
response = requests.get(url)
articles = response.json().get('articles', [])

# Prepare news text
news_content = '\n\n'.join([article['title'] + ' - ' + article['description'] for article in articles[:5]])

# Convert to speech
tts = gTTS(news_content)
tts.save('/mnt/data/news_audio.mp3')

# Play the audio
pygame.mixer.init()
pygame.mixer.music.load('/mnt/data/news_audio.mp3')
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    pass
