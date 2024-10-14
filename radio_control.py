import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pynput import keyboard  # Use pynput for cross-platform keyboard controls
import json  # For loading playlists from playlists.json
from dotenv import load_dotenv
import time  # For retry delays
import subprocess  # For running custom commands
import pygame  # For playing the jingle

# Load environment variables from .env file
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

# Path to the JSON file where playlists are stored
PLAYLIST_FILE = 'playlists.json'

# Path to the jingle file
JINGLE_FILE = os.path.join('songs', 'Jingle.mp3')

# Global variables
radio_channels = []  # List of Spotify playlist URIs
current_channel = 0  # Current channel index
custom_command = None  # Store the custom command

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

# Authenticate and get Spotify client (automatically handles callback URL)
def get_spotify_client():
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        # This will automatically open the browser, handle the callback, and return the token
        token_info = sp_oauth.get_access_token()
    else:
        # Refresh the token if it's expired
        if sp_oauth.is_token_expired(token_info):
            print("Token expired, refreshing...")
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    
    return spotipy.Spotify(auth=token_info['access_token'])

sp = get_spotify_client()  # Get the authenticated Spotify client

# Play the current channel (playlist)
def play_channel(channel_index):
    global sp
    devices = sp.devices()  # Get available devices
    
    # Load the updated playlists every time a channel is played
    radio_channels = load_playlists()
    
    if devices['devices'] and radio_channels:
        device_id = devices['devices'][0]['id']  # Use the first available device
        playlist_uri = radio_channels[channel_index]  # Get the playlist URI

        try:
            sp.shuffle(True, device_id=device_id)  # Enable shuffle mode
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
    global sp  # Make sure to declare this inside the function
    
    # Fetch the current playback status
    playback = sp.current_playback()
    print(f"Playback state: {playback}")  # Debugging line
    
    # If there's no playback (Spotify isn't playing anything)
    if playback is None or playback['item'] is None:
        print("No current playback. Starting the first playlist.")
        play_channel(0)  # Start playing the first playlist (index 0)
    else:
        # If Spotify is playing something, toggle play/pause
        if playback['is_playing']:
            sp.pause_playback()
            print("Playback paused.")
        else:
            sp.start_playback()
            print("Playback resumed.")

# Zap to the next channel (playlist)
def zap_next_channel():
    global current_channel
    
    # Reload playlists every time a channel is zapped
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
    if custom_command:
        try:
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

                # Execute the custom command after the jingle
                print(f"Executing custom command: {custom_command}")
                subprocess.run(custom_command, shell=True)

                # Resume Spotify playback after the command
                print("Resuming Spotify playback.")
                play_channel(current_channel)  # Resume the current channel
            else:
                print(f"Jingle file not found: {JINGLE_FILE}")
        except Exception as e:
            print(f"Error during jingle/command execution: {e}")
        finally:
            custom_command = None  # Clear the command after execution

# Monitor Spotify playback and execute the command when the song ends
def monitor_playback():
    global sp
    while True:
        try:
            playback = sp.current_playback()
            if playback is not None and playback['is_playing']:
                progress = playback['progress_ms']
                total_duration = playback['item']['duration_ms']

                print(f"Playback progress: {progress} / {total_duration}")  # Log song progress

                # If the song is about to end (within 5 seconds)
                if progress >= total_duration - 5000 and custom_command:
                    print("Song is about to end. Playing jingle and executing custom command.")
                    play_jingle_and_execute_command()
            else:
                print("No active playback detected.")
            time.sleep(1)  # Check every second
        except Exception as e:
            print(f"Error monitoring playback: {e}")
            time.sleep(1)

# Handle key presses
def on_press(key):
    try:
        if key.char == '-':  # Next channel
            zap_next_channel()
        elif key.char == '=':  # Play/Pause
            play_pause()
    except AttributeError:
        pass

if __name__ == "__main__":
    # Load playlaists at the start
    load_playlists()

    # Start monitoring the Spotify playback for song end
    print("Starting playback monitor in the background...")
    from threading import Thread
    monitor_thread = Thread(target=monitor_playback, daemon=True)
    monitor_thread.start()

    # Listen for key presses using pynput
    print("Press '-' to zap channels and '=' to play/pause.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
