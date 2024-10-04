# spotify.py
from flask import Flask, redirect, request, session, url_for, render_template
from spotify_integration import SpotifyIntegration
import os
import spotipy

app = Flask(__name__)
app.secret_key = "random_secret_key"  # Needed for session management

# Load Spotify credentials from environment variables
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID', 'your_client_id')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET', 'your_client_secret')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5001/callback')

# Initialize the SpotifyIntegration instance
spotify = SpotifyIntegration(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)

@app.route('/')
def login():
    # Redirect the user to Spotify's authorization URL
    auth_url = spotify.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Get the authorization code sent by Spotify
    code = request.args.get('code')
    if not code:
        return "Error: Missing authorization code", 400
    
    try:
        # Exchange the authorization code for an access token using the SpotifyIntegration instance
        token_info = spotify.get_access_token(code)
        session['token_info'] = token_info
        return redirect(url_for('playlists'))
    except Exception as e:
        return f"Error during token exchange: {e}", 500

def get_spotify_client():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    # Use the SpotifyIntegration instance to refresh token if necessary
    access_token = spotify.refresh_token_if_needed()
    if not access_token:
        return None

    sp = spotipy.Spotify(auth=access_token)
    return sp

@app.route('/playlists')
def playlists():
    sp = get_spotify_client()
    if sp:
        # Fetch user's playlists
        playlists = sp.current_user_playlists()
        return render_template('playlists.html', playlists=playlists['items'])  # Passing playlists to the template
    return redirect(url_for('login'))

@app.route('/play/<playlist_uri>')
def play_playlist(playlist_uri):
    sp = get_spotify_client()
    if sp:
        devices = sp.devices()
        if devices['devices']:
            device_id = devices['devices'][0]['id']
            sp.start_playback(device_id=device_id, context_uri=playlist_uri)
            return "Started playing the playlist."
        return "No active devices found."
    return redirect(url_for('login'))

@app.route('/pause')
def pause():
    sp = get_spotify_client()
    if sp:
        sp.pause_playback()
        return "Paused playback."
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
