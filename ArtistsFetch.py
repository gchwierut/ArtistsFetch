import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Spotify API credentials and redirect URI
creds = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "your_redirect_uri",
    "scope": "playlist-modify-public"
}

# Initialize Spotipy client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(**creds))

# Prompt the user for an artist name
artist_name = input("Enter an artist name: ")

# Find similar artists
result = sp.search(artist_name, type="artist")
artist_uri = result["artists"]["items"][0]["uri"]
related_artists = sp.artist_related_artists(artist_uri)["artists"]

# Get all album IDs and release dates for inputted and similar artists
album_data = {}
for artist in [artist_uri] + [a["uri"] for a in related_artists]:
    offset = 0
    while True:
        albums = sp.artist_albums(artist, album_type="album", offset=offset)["items"]
        if len(albums) == 0:
            break
        for album in albums:
            album_data[album["id"]] = {"release_date": album["release_date"], "artist_name": album["artists"][0]["name"]}
        offset += len(albums)
        time.sleep(0.5)  # add a delay to avoid hitting the rate limit

# Sort album IDs based on release dates
sorted_album_ids = [k for k, v in sorted(album_data.items(), key=lambda item: item[1]["release_date"])]

# Get all track IDs for sorted albums
track_ids = []
for album_id in sorted_album_ids:
    tracks = sp.album_tracks(album_id)["items"]
    track_ids.extend([track["id"] for track in tracks])

# Create a playlist and add tracks to it in chunks of 100
playlist_name = f"{artist_name} and Similar Artists"
playlist = sp.user_playlist_create(sp.current_user()["id"], playlist_name, public=True)

for i in range(0, len(track_ids), 100):
    sp.playlist_add_items(playlist["id"], track_ids[i:i+100])
    time.sleep(1)
