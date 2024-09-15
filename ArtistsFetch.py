import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import requests

# Spotify API credentials and redirect URI
creds = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "your_redirect_uri",
    "scope": "playlist-modify-public"
}

# Initialize Spotipy client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(**creds))

# Function to handle rate-limited requests
def make_spotify_request(func, *args, **kwargs):
    while True:
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 1))
                print(f"Rate limit hit. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
            else:
                raise

# Prompt the user for an artist name
artist_name = input("Enter an artist name: ")

# Find artist
result = make_spotify_request(sp.search, artist_name, type="artist")
artist_uri = None
for artist in result["artists"]["items"]:
    if artist["name"].lower() == artist_name.lower():
        artist_uri = artist["uri"]
        break

if artist_uri is None:
    print(f"No artist found with the name '{artist_name}'.")
    exit()

# Get all album IDs and release dates for the inputted artist
album_data = {}
offset = 0
api_calls = 0
while True:
    albums = make_spotify_request(sp.artist_albums, artist_uri, offset=offset)["items"]
    if len(albums) == 0:
        break
    for album in albums:
        album_data[album["id"]] = {"release_date": album["release_date"], "artist_name": album["artists"][0]["name"]}
    offset += len(albums)
    api_calls += 1
    if api_calls >= 180:  # Ensure no more than 180 API calls per minute
        time.sleep(60)  # Wait for 1 minute
        api_calls = 0

# Sort album IDs based on release dates
sorted_album_ids = [k for k, v in sorted(album_data.items(), key=lambda item: item[1]["release_date"])]

# Get all track IDs for sorted albums
track_ids = []
for album_id in sorted_album_ids:
    album_artists = make_spotify_request(sp.album, album_id)["artists"]
    if len(album_artists) > 0 and album_artists[0]["name"].lower() == artist_name.lower():
        tracks = make_spotify_request(sp.album_tracks, album_id)["items"]
        track_ids.extend([track["id"] for track in tracks])
        api_calls += 1
        if api_calls >= 180:
            time.sleep(60)
            api_calls = 0

# Check if playlist already exists
playlist_name = f"{artist_name} Spotify Discography"
existing_playlists = make_spotify_request(sp.current_user_playlists)["items"]
playlist_id = None

for existing_playlist in existing_playlists:
    if existing_playlist["name"] == playlist_name:
        playlist_id = existing_playlist["id"]
        break

# If playlist does not exist, create a new one
if playlist_id is None:
    playlist = make_spotify_request(sp.user_playlist_create, sp.current_user()["id"], playlist_name, public=True)
    playlist_id = playlist["id"]

# Get existing track IDs in the playlist
existing_track_ids = []
existing_tracks = make_spotify_request(sp.playlist_tracks, playlist_id)["items"]
while True:
    for track in existing_tracks:
        existing_track_ids.append(track["track"]["id"])
    if len(existing_tracks) == 0:
        break
    existing_tracks = make_spotify_request(sp.playlist_tracks, playlist_id, offset=len(existing_track_ids))["items"]
    api_calls += 1
    if api_calls >= 180:
        time.sleep(60)
        api_calls = 0

# Add missing tracks in the right order
missing_track_ids = [track_id for track_id in track_ids if track_id not in existing_track_ids]
for i in range(0, len(missing_track_ids), 100):
    make_spotify_request(sp.playlist_add_items, playlist_id, missing_track_ids[i:i+100])
    time.sleep(1)
