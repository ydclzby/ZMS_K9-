import requests
import feedparser
import vlc
import json
import time
import threading

itunes_search_url = "https://itunes.apple.com/search"
history_file = "playback_history.json"
player = None
paused = False
quit_playback = False
current_start_time = None
lock = threading.Lock()
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
    global player, paused, current_start_time
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
    """Control playback with user commands like stop, resume, or quit."""
    global paused, player, current_start_time
    while True:
        command = input("Enter command (stop/resume/quit): ").strip().lower()
        with lock:
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
                print(f"Invalid command or action not applicable: {command}")

def first_podcast(topic):
    global player, current_start_time, history
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

def main():
    # Load playback history
    global history
    history = read_history_from_json(history_file)

    # Ask the user if they want to resume playback from the history or play a new one
    choice = input("Do you want to resume playback from the history (yes/no)? ").strip().lower()
    if choice == "yes":
        episode_to_resume = list_history(history)
        resume_playback(episode_to_resume)
    else:
        topic = input("Enter the podcast topic to search for: ").strip()
        first_podcast(topic)
        
if __name__ == '__main__':
    main()