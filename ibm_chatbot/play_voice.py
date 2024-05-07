from gtts import gTTS
import os

# Text to be converted to speech
text_to_speak = "shao du shao du"

# Create a gTTS object
tts = gTTS(text=text_to_speak, lang="en")  # Change 'en' to your desired language code

# Save the speech to an MP3 file in the current directory
filename = "example.mp3"  # Filename to save the audio
tts.save(filename)  # This saves the file in the current directory

# Play the MP3 file using the appropriate system command
if os.name == "posix":
    # For macOS and Linux
    os.system(f"open {filename}")  # macOS
    # os.system(f"xdg-open {filename}")  # Linux
else:
    # For Windows
    os.system(f"start {filename}")

