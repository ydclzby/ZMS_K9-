import requests
import vlc
import time

itunes_search_url = "https://itunes.apple.com/search"

def first_song_search(topic):
    params = {
        "term": topic,
        "media": "music",
        "limit": 1
    }

    response = requests.get(itunes_search_url, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])

        if results:
            preview_url = results[0].get("previewUrl")
            track_name = results[0].get("trackName")
            artist_name = results[0].get("artistName")
            print(f"Playing: '{track_name}' by {artist_name}")
            print(f"Preview URL: {preview_url}")

            # Create VLC instance with network caching
            instance = vlc.Instance("--network-caching=1000")
            player = instance.media_player_new()
            media = instance.media_new(preview_url)

            player.set_media(media)
            player.audio_set_volume(100)  # Adjust the volume
            print("Streaming the first song...")
            player.play()

            # Wait until the preview ends
            while player.get_state() != vlc.State.Ended:
                time.sleep(1)

    else:
        print(f"Error fetching data: {response.status_code}")

def main():
    first_song_search("Thriller")

if __name__ == '__main__':
    main()
