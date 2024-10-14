import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pynput import keyboard
import json
from dotenv import load_dotenv
import time
import subprocess
import pygame

# Load environment variables
load_dotenv()

# Initialize pygame mixer for playing the jingle
pygame.mixer.init()

# Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Spotify authentication and initialization
scope = "user-library-read user-read-playback-state user-modify-playback-state playlist-read-private"
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)

# Path to the JSON file where commands are stored
COMMAND_FILE = 'command.json'

# Path to the JSON file where playlists are stored
PLAYLIST_FILE = 'playlists.json'

# Path to the jingle file
JINGLE_FILE = os.path.join('songs', 'Jingle.mp3')

# Global variables
radio_channels = []  # List of Spotify playlist URIs
current_channel = 0  # Current channel index
custom_command = None  # Store the custom command
song_about_to_end_triggered = False  # Prevent multiple triggers

# Load playlists from the JSON file dynamically
def load_playlists():
    global radio_channels
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, 'r') as file:
            radio_channels = json.load(file)
            print(f"Loaded playlists: {radio_channels}")
    else:
        print("No playlists found. Please add playlists via the web interface.")
    
    return radio_channels

# Load command from the JSON file dynamically
def load_command():
    global custom_command
    if os.path.exists(COMMAND_FILE):
        with open(COMMAND_FILE, 'r') as file:
            try:
                command_data = json.load(file)
                custom_command = command_data.get('command', None)
                print(f"Loaded command from file: {custom_command}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {COMMAND_FILE}")
                custom_command = None
    else:
        print(f"{COMMAND_FILE} not found.")
        custom_command = None
    
    return custom_command

# Authenticate and get Spotify client
def get_spotify_client():
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        token_info = sp_oauth.get_access_token()
    else:
        if sp_oauth.is_token_expired(token_info):
            print("Token expired, refreshing...")
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    
    return spotipy.Spotify(auth=token_info['access_token'])

sp = get_spotify_client()

# Play the current channel (playlist)
def play_channel(channel_index):
    global sp
    devices = sp.devices()  # Get available devices
    
    radio_channels = load_playlists()
    
    if devices['devices'] and radio_channels:
        device_id = devices['devices'][0]['id']
        playlist_uri = radio_channels[channel_index]

        try:
            sp.shuffle(True, device_id=device_id)
            sp.start_playback(device_id=device_id, context_uri=playlist_uri)
            print(f"Playing (shuffled) playlist: {playlist_uri} on device: {device_id}")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                print("Received 403 error, retrying in 2 seconds...")
                time.sleep(2)
                try:
                    sp.start_playback(device_id=device_id, context_uri=playlist_uri)
                    print(f"Retry successful: Playing playlist: {playlist_uri} on device: {device_id}")
                except Exception as e:
                    print(f"Error during retry: {e}")
            else:
                print(f"Error starting playback: {e}")
    else:
        print("No active devices found or no playlists available!")

# Toggle play/pause for the current channel
def play_pause():
    global sp
    
    playback = sp.current_playback()
    print(f"Playback state: {playback}")
    
    if playback is None or playback['item'] is None:
        print("No current playback. Starting the first playlist.")
        play_channel(0)
    else:
        if playback['is_playing']:
            sp.pause_playback()
            print("Playback paused.")
        else:
            sp.start_playback()
            print("Playback resumed.")

# Zap to the next channel (playlist)
def zap_next_channel():
    global current_channel
    
    radio_channels = load_playlists()
    
    if len(radio_channels) == 0:
        print("No playlists available. Please set some playlists.")
        return

    current_channel = (current_channel + 1) % len(radio_channels)
    print(f"Zapping to channel {current_channel}")
    play_channel(current_channel)

# Play the jingle, then execute the custom command, and finally resume the playlist
def play_jingle_and_execute_command():
    global custom_command
    command = load_command()  # Fetch the latest command from the file
    if command:
        try:
            print(f"Received custom command: {command}")

            # Stop current Spotify playback before playing the jingle
            print("Pausing Spotify playback for jingle.")
            sp.pause_playback()

            # Play the jingle
            if os.path.exists(JINGLE_FILE):
                print(f"Playing jingle: {JINGLE_FILE}")
                pygame.mixer.music.load(JINGLE_FILE)
                pygame.mixer.music.play()

                # Wait for the jingle to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(1)
                print("Jingle finished.")

                # Display the command on the radio after the jingle
                display_on_radio(f"Executing command: {command}")

                # Execute the custom command after the jingle
                subprocess.run(command, shell=True)

                # Clear the command from the JSON file after executing
                with open(COMMAND_FILE, 'w') as file:
                    json.dump({}, file)
                print("Cleared command after execution.")

                # Resume Spotify playback after the command
                print("Resuming Spotify playback.")
                play_channel(current_channel)  # Resume the current channel
            else:
                print(f"Jingle file not found: {JINGLE_FILE}")
        except Exception as e:
            print(f"Error during jingle/command execution: {e}")
        finally:
            custom_command = None  # Clear the command after execution

# Fetch and display command, then pause playback for 5 seconds
def fetch_and_display_command():
    global custom_command
    command = load_command()
    
    if command:
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            progress_ms = playback['progress_ms']
            print(f"Command to be shown: {command} | Song progress: {progress_ms} ms")

        # Display the command on the radio
        display_on_radio(f"Command: {command}")

# Monitor Spotify playback and fetch/display the command 1 second before the song ends
def monitor_playback():
    global sp
    global song_about_to_end_triggered
    while True:
        try:
            playback = sp.current_playback()
            
            if playback is not None and playback['is_playing']:
                progress = playback['progress_ms']
                total_duration = playback['item']['duration_ms']

                print(f"Playback progress: {progress} / {total_duration}")

                # Check if the song is about to end (1 second before)
                if total_duration - progress <= 1000 and not song_about_to_end_triggered:
                    print("Song is about to end.")
                    fetch_and_display_command()
                    song_about_to_end_triggered = True  # Trigger only once

                if progress <= 1000:  # Reset for the next song
                    song_about_to_end_triggered = False
            else:
                print("No active playback detected.")

            time.sleep(1)  # Check playback every second
        except Exception as e:
            print(f"Error monitoring playback: {e}")
            time.sleep(1)

# Placeholder function for displaying a message on the radio
def display_on_radio(message):
    print(f"Radio Display: {message}")

# Handle key presses
def on_press(key):
    try:
        if key.char == '-':
            zap_next_channel()
        elif key.char == '=':
            play_pause()
    except AttributeError:
        pass

if __name__ == "__main__":
    load_playlists()

    print("Starting playback monitor in the background...")
    from threading import Thread
    monitor_thread = Thread(target=monitor_playback, daemon=True)
    monitor_thread.start()

    print("Press '-' to zap channels and '=' to play/pause.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
