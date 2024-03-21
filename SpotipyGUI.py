import os
import spotipy
import random
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifyClient:
    def __init__(self, client_id, client_secret):
        # Set the environment variables for Spotify credentials
        os.environ['SPOTIPY_CLIENT_ID'] = client_id
        os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret

        # Initialize the Spotify client
        client_credentials_manager = SpotifyClientCredentials()
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def get_recommended_song(self, emotion):
        # Define playlists for different emotions
        playlists = {
            'sad': '37i9dQZF1DWV3IJ2kse1M3',
            'anxiety': '37i9dQZF1DX8gS5vh05dnc',
            'hate': '37i9dQZF1DX3YSRoSdA634',
            'happy': '37i9dQZF1DXdPec7aLTmlC',
            'angry': '37i9dQZF1DX1s9knjP51Oa',
            'boring': '37i9dQZF1DWWjGdmeTyeJ6',
            'neutral': '37i9dQZF1DX7K31D69s4M1'
        }

        playlist_id = playlists.get(emotion)
        if playlist_id:
            tracks = self.sp.playlist_tracks(playlist_id=playlist_id)['items']
            if tracks:
                selected_track = random.choice(tracks)['track']
                song_details = {
                    'name': selected_track['name'],
                    'artist': selected_track['artists'][0]['name'],
                    'image_link': selected_track['album']['images'][2]['url'],
                    'preview_url': selected_track['preview_url']
                }
                return song_details
        return None


# Example usage:
if __name__ == '__main__':
    client_id = 'fd8268198c88420db0343ca9b067cc15'
    client_secret = '44fbe87c03bf483496089d56206da509'
    spotify_client = SpotifyClient(client_id, client_secret)
    recommended_song = spotify_client.get_recommended_song('happy')
    if recommended_song:
        print(recommended_song)
    else:
        print("No song found.")