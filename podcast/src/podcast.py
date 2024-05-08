import requests
import feedparser
from playsound import playsound
import os
from urllib.parse import urlparse

itunes_search_url = "https://itunes.apple.com/search"

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
    first_podcast("python")

if __name__ == '__main__':
    main()