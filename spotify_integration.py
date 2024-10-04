# spotify_integration.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session

class SpotifyIntegration:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp_oauth = SpotifyOAuth(client_id=client_id,
                                     client_secret=client_secret,
                                     redirect_uri=redirect_uri,
                                     scope="user-library-read user-read-playback-state user-modify-playback-state playlist-read-private")
    
    def get_authorize_url(self):
        return self.sp_oauth.get_authorize_url()

    def get_access_token(self, code):
        return self.sp_oauth.get_access_token(code)

    def refresh_token_if_needed(self):
        token_info = session.get('token_info')
        if self.sp_oauth.is_token_expired(token_info):
            token_info = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
        return token_info['access_token']
