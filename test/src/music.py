import os
import requests
import time

# Set VLC library paths
os.environ['VLC_PLUGIN_PATH'] = '/Applications/VLC.app/Contents/MacOS/plugins'
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/Applications/VLC.app/Contents/MacOS/lib'

import vlc

# Replace 'your_client_id_here' with your actual Jamendo client ID.
CLIENT_ID = 'cd92fac2'

def get_popular_jazz_song():
    # Define the API endpoint
    api_url = "https://api.jamendo.com/v3.0/tracks"
    
    # Set the parameters for the API request
    params = {
        'client_id': CLIENT_ID,
        'format': 'json',
        'limit': 1,  # Get only the top result
        'tags': 'pop',
        'order': 'popularity_total_desc'
    }
    
    # Make the request to Jamendo API
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raises an exception for HTTP error responses
        
        # Parse the JSON response
        data = response.json()
        
        # Check if any tracks were found
        if data['headers']['status'] == 'success' and data['results']:
            track = data['results'][0]
            return track['name'], track['artist_name'], track['audio']
        else:
            return "No jazz tracks found.", None, None
    except requests.RequestException as e:
        return f"An error occurred: {str(e)}", None, None

def play_song(audio_url):
    # Create a VLC instance
    player = vlc.Instance()
    
    # Create a media player with this instance
    media_player = player.media_player_new()
    
    # Create a media with the audio URL
    media = player.media_new(audio_url)
    
    # Set the media to the player
    media_player.set_media(media)
    
    # Play the media
    media_player.play()
    
    # Wait for the audio to finish playing
    while True:
        state = media_player.get_state()
        if state in [vlc.State.Ended, vlc.State.Error, vlc.State.Stopped]:
            break
        time.sleep(0.1)  # Check every 0.1 seconds

# Call the function and print the result
song_name, artist_name, audio_url = get_popular_jazz_song()
print(f"Song Name: {song_name}")
print(f"Artist Name: {artist_name}")
print(f"Listen Here: {audio_url}")

# If a song was found, play it
if audio_url:
    print("Streaming and playing the song...")
    play_song(audio_url)
