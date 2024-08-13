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
            'sad': ['37i9dQZF1DWV3IJ2kse1M3'],
            'calm': ['37i9dQZF1DX8gS5vh05dnc'], # recommend chill, acoustics or instrumental songs
            'happy': ['37i9dQZF1DXdPec7aLTmlC'],
            'angry': ['37i9dQZF1DXdPec7aLTmlC'],
            'neutral': ['37i9dQZF1DX7K31D69s4M1']# if neutral, recommend calm or happy songs
        }

        # Define messages for each emotion
        messages = {
            'sad': [
                "Listen to this song from Playlist 1 to reflect on your emotions.",
                "This song from Playlist 2 might help you through a tough time."
            ],
            'calm': [
                "Relax and unwind with this calming tune from Playlist 1.",
                "Let this song from Playlist 2 bring peace to your mind."
            ],
            'happy': [
                "Get ready to dance with this upbeat track from Playlist 1!",
                "This song from Playlist 2 is sure to lift your spirits."
            ],
            'angry': [
                "Feeling furious? Blast this song from Playlist 1 to let it out!",
                "Let this high-energy track from Playlist 2 match your intensity."
            ],
            'neutral': [
                "In a neutral mood? Enjoy this easygoing song from Playlist 1.",
                "Let this song from Playlist 2 add a touch of brightness to your day."
            ]
        }

        playlist_ids = playlists.get(emotion)
        if playlist_ids:
            chosen_playlist_id = random.choice(playlist_ids)
            playlist_index = playlists[emotion].index(chosen_playlist_id)
            tracks = self.sp.playlist_tracks(playlist_id=chosen_playlist_id)['items']
            if tracks:
                selected_track = random.choice(tracks)['track']
                song_details = {
                    'name': selected_track['name'],
                    'artist': selected_track['artists'][0]['name'],
                    'image_link': selected_track['album']['images'][1]['url'],
                    'spotify_uri': selected_track['uri'],
                    'preview_url': selected_track['preview_url']
                }

                message = messages[emotion][playlist_index]

                return song_details, message
        return None, None


# Example usage:
if __name__ == '__main__':
    # Put own ID and SECRET
    client_id = 'OWN ID'
    client_secret = 'OWN SECRET' 
    spotify_client = SpotifyClient(client_id, client_secret)
    recommended_song, message = spotify_client.get_recommended_song('sad')
    if recommended_song:
        song_link = f"https://open.spotify.com/track/{recommended_song['spotify_uri'].split(':')[-1]}"
        print("Recommended Song:", recommended_song)
        print("Song Link:", song_link)
        print("Message:", message)
    else:
        print("No song found.")
