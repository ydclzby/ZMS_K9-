import requests
import feedparser
import vlc
import threading
import json
import time

itunes_search_url = "https://itunes.apple.com/search"
player = None
paused = False
quit_playback = False
lock = threading.Lock()
history = []
current_start_time = None

def first_podcast(topic):
    global player, history, current_start_time
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
                history.append({
                    "title": episode_title,
                    "url": first_episode_url,
                    "start_time": current_start_time,
                    "duration_listened": 0  # Initialize with zero; updated when stopping
                })

                # Keep the player running until stopped
                while not quit_playback:
                    pass
                print("Podcast playback ended.")
    else:
        print(f"Error fetching data: {response.status_code}")

def control_playback():
    global paused, quit_playback, player, current_start_time, history
    while True:
        command = input("Enter command (stop/resume/quit): ").strip().lower()
        with lock:
            if command == "stop" and player and not paused:
                print("Stopping playback...")
                player.pause()
                paused = True
                if current_start_time is not None:
                    # Update the duration listened for the last episode
                    elapsed_time = time.time() - current_start_time
                    history[-1]["duration_listened"] = elapsed_time
            elif command == "resume" and player and paused:
                print("Resuming playback...")
                player.play()
                paused = False
                # Reset the start time to calculate new listening duration
                current_start_time = time.time()
            elif command == "quit":
                print("Quitting playback and saving history...")
                quit_playback = True
                if player:
                    player.stop()
                # Update the final duration listened for the last episode
                if current_start_time is not None:
                    elapsed_time = time.time() - current_start_time
                    history[-1]["duration_listened"] = elapsed_time
                break
            else:
                print(f"Invalid command or action not applicable: {command}")

def save_history_to_json(file_path):
    """Save playback history to a JSON file."""
    with open(file_path, "w") as file:
        json.dump(history, file, indent=4)
    print(f"Playback history saved to {file_path}")

def main():
    podcast_thread = threading.Thread(target=first_podcast, args=("finance",))
    podcast_thread.start()

    # Start the control playback thread to listen for user inputs
    control_thread = threading.Thread(target=control_playback)
    control_thread.start()

    podcast_thread.join()
    control_thread.join()

    # Save the playback history to a JSON file
    save_history_to_json("playback_history.json")

if __name__ == '__main__':
    main()
