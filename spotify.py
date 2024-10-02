import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "random_secret_key"  # Needed to keep track of sessions
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# Set your Spotify credentials from environment variables (recommended for security)
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID', '05e81a0716f64a5d92186077e52f4c1c')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET', 'f80a4e4d1ebd413c98094e2d3b46ec5e')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://localhost:5001/callback')  # Use 127.0.0.1

# Set the scope of the permissions you need
SCOPE = "user-library-read user-read-playback-state user-modify-playback-state playlist-read-private"

# Initialize the Spotify OAuth object
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=SCOPE)

@app.route('/')
def login():
    # Redirect the user to Spotify's authorization URL
    auth_url = sp_oauth.get_authorize_url()
    print(f"Redirecting to Spotify authorization URL: {auth_url}")  # Debugging line
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Debugging: print the full request URL and parameters
    print(f"Request URL: {request.url}")

    # Get the authorization code sent by Spotify
    code = request.args.get('code')
    print(f"Authorization code received: {code}")  # Debugging line

    if not code:
        return "Error: Missing authorization code.", 400

    try:
        # Exchange the authorization code for an access token
        token_info = sp_oauth.get_access_token(code)
        print(f"Access token info: {token_info}")  # Debugging line

        # Store token info in session
        session['token_info'] = token_info
        return redirect(url_for('playlists'))

    except Exception as e:
        # Debugging: print any errors during token exchange
        print(f"Error during token exchange: {e}")
        return f"Error during token exchange: {e}", 500

def get_spotify_client():
    token_info = session.get('token_info', None)
    
    if not token_info:
        return None
    
    # Check if token is expired and refresh if necessary
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

@app.route('/playlists')
def playlists():
    sp = get_spotify_client()
    if sp:
        # Fetch user's playlists
        playlists = sp.current_user_playlists()
        playlist_info = ""
        for playlist in playlists['items']:
            playlist_info += f"{playlist['name']} - {playlist['uri']}<br>"
            print(f"Playlist: {playlist['name']} - {playlist['uri']}")  # Debugging line
        
        # Return the list of playlists
        return f"<h1>Your Playlists:</h1><p>{playlist_info}</p><br>" \
               "<a href='/play'>Click here to play a specific playlist</a>"
    return "User not authenticated."

@app.route('/play')
def play():
    sp = get_spotify_client()
    if sp:
        # Get the user's available devices
        devices = sp.devices()
        if not devices['devices']:
            return "No active devices found! Open Spotify on a device to connect."

        device_id = devices['devices'][0]['id']  # Use the first available device
        print(f"Device found: {devices['devices'][0]['name']} - {device_id}")  # Debugging line

        # Example: Play a specific playlist (replace with your desired playlist URI)
        playlist_uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"  # Example playlist URI
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        
        return f"Started playing the playlist: {playlist_uri} on device: {devices['devices'][0]['name']}"
    
    return "User not authenticated."

@app.route('/search_and_play')
def search_and_play():
    sp = get_spotify_client()
    if sp:
        # Search for a track
        query = "Bohemian Rhapsody"
        results = sp.search(q=query, type='track')

        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            print(f"Track found: {results['tracks']['items'][0]['name']} - {track_uri}")  # Debugging line

            # Get the user's available devices
            devices = sp.devices()
            if not devices['devices']:
                return "No active devices found! Open Spotify on a device to connect."

            device_id = devices['devices'][0]['id']  # Use the first available device

            # Play the track
            sp.start_playback(device_id=device_id, uris=[track_uri])
            
            return f"Started playing the track: {results['tracks']['items'][0]['name']} on device: {devices['devices'][0]['name']}"
    
    return "User not authenticated."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

