import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import os
from playsound import playsound
import pyttsx3
import objc

news_api_key = 'a0ff4132-cf60-48d7-b23f-d0523e7c67aa' 
news_endpoint = 'https://content.guardianapis.com/search'

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
    engine.setProperty('rate', 180)  # Speed of speech
    engine.setProperty('volume', 1)  # Volume (0 to 1)
    engine.say(news_text)
    engine.runAndWait()


def main():
    #topic = input()
    get_news("apple")
    read_news()

if __name__ == "__main__":
    main()    