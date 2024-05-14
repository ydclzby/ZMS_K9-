from pydub.utils import mediainfo

def get_audio_duration(file_path):
        # Use mediainfo function to get metadata of the audio file
        metadata = mediainfo(file_path)
        
        # Extract duration from metadata
        duration_ms = float(metadata.get('duration', 0))  # Ensure duration is parsed as float
        
        # Convert duration from milliseconds to seconds
        duration_sec = duration_ms
        print("duration: ", duration_sec)
        return duration_sec

get_audio_duration("temp_speech.mp3")