import random
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from requests import post, get
from dotenv import load_dotenv
import os
import base64
from datetime import datetime

class Song:
    def __init__(self, id=None, duration=None, name=None, artist=None, uri=None, album=None):
        self.spotify_id = id
        self.duration = duration
        self.name = name
        self.artist = artist
        self.uri = uri
        self.album = album

    def set_spotify_id(self, id):
        self.spotify_id = id

    def get_spotify_id(self):
        return self.spotify_id
    
    def set_duration(self, duration):
        self.duration = duration

    def get_duration(self):
        return self.duration
    
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name
    
    def set_artist(self, artist):
        self.artist = artist

    def get_artist(self):
        return self.artist
    
    def set_uri(self, uri):
        self.uri = uri

    def get_uri(self):
        return self.uri
    
    def set_album(self, album):
        self.album = album
    
    def get_album(self):
        return self.album


def connect_spotipy():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri="http://localhost/7777",
                                               scope="user-modify-playback-state playlist-read-private"))
    return sp

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded" 
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}




def get_album_tracks(token, albums):
    # FUNCTION: Given an album get all the songs off the album
    # PARAMETERS: a spotify auth token, an array of albums
    # RETURN: a list of spotify ids and a dictionary of those ids mapped to info about the song
    tracks = []
    for album in albums:
        id = album["id"]
        url = f"https://api.spotify.com/v1/albums/{id}/tracks?market=US"
        headers = get_auth_header(token)

        result = get(url, headers=headers)
        json_result = json.loads(result.content)["items"]
        for track in json_result:
            s = Song(id=track["id"], duration=track["duration_ms"], name=track["name"], artist=track["artists"][0]["name"], uri=track["uri"], album=album["name"])
            tracks.append(s)
    
    return tracks

def get_albums(token, artist_id):
    # returns albums by the artist_id
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?country=US"
    headers = get_auth_header(token)

    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]

    if len(json_result) == 0:
        print("No artists match your search")
        return None
    
    return json_result

def get_artist(token, artist):
    # FUNCTION: Given an artist name find their spotify id
    # PARAMETERS: A spotify access token and an artist string,
    # RETURNS: Spotify artist_id

    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    
    if len(json_result) == 0:
        print("No artists match your search")
        return None
    
    return json_result[0]

def get_playlists():
    # FUNCTION: Gets all of the users playlists
    # PARAMETERS: None
    # RETURNS: DICT of playlist names and spotify id of the playlist

    playlists = sp.current_user_playlists()["items"]
    playlist_songs = {}
    for playlist in playlists:
        playlist_songs[playlist["name"]] = playlist["id"]

    return playlist_songs

def get_playlist_tracks(id):
    # FUNCTION: Gets all songs off of a playlist
    # PARAMETERS: Spotify playlist id
    # RETURNS: LIST of spotify ids of tracks on playlist, DICT of track info mapped to those ids

    results = sp.playlist_tracks(id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    playlist_tracks = []

    for track in tracks:
        # Get album of the song!
        s = Song(id=track["track"]["id"], duration=track["track"]["duration_ms"], name=track["track"]["name"], artist=track["track"]["artists"][0]["name"], uri=track["track"]["uri"], album=track["track"]["album"]["name"])
        playlist_tracks.append(s)

    return playlist_tracks


def format_song(song):
    if " (" in song:
        i = song.index(" (")
        title = song[:i]
    elif " -" in song:
        i = song.index(" -")
        title = song[:i]
    else:
        title = song

    return title


def daily_challenge():
    albums = get_albums(token, "3Nrfpe0tUJi4K4DXYWgMUX")
    tracks = get_album_tracks(token, albums)
    guess_song = tracks[random.randrange(0,len(tracks))]
    run_freeplay(guess_song)

def freeplay_artist():
    # FUNCTION: Sets up game of freeplay artist 
    # PARAMETERS: None
    # RETURNS: Score of how many correct songs before a mistake
    artist_search = input("What artist would you like play with? ")
    artist = get_artist(token, artist_search)
    albums = get_albums(token, artist["id"])
    tracks = get_album_tracks(token, albums)
    print(len(tracks))
    guess_song = tracks[random.randrange(0,len(tracks))]

    score =  0

    while run_freeplay(guess_song):
        guess_song = tracks[random.randrange(0,len(tracks))]
        score += 1

    return score

def freeplay_playlist():
    playlists = get_playlists()
    for playlist in playlists:
        print(playlist)
    response = input("Which playlist would you like to play with? ")
    tracks = get_playlist_tracks(playlists[response])
    guess_song = tracks[random.randrange(0,len(tracks))]
    score = 0

    while run_freeplay(guess_song):
        guess_song = tracks[random.randrange(0,len(tracks))]
        score += 1

    return score

def run_freeplay(song):
    # FUNCTION: Runs song guessing game with limited listening time
    # PARAMETERS: None
    # RETURNS: BOOL of if the song guess was correct 
    start_pos = random.randint(0, song.duration-20000) 

    #Make first round just lyrics?
    for i in range(5):
        if i == 0:
            guess_time = 1
        elif i == 1:
            guess_time = 2
        elif i == 2:
            guess_time = 4
        elif i == 3:
            guess_time = 7
        elif i == 4:
            guess_time = 10
        else:
            guess_time = 15

        play_song(song, start_pos, guess_time)
        guess = input("Guess: ").lower()
        title = format_song(song.name)
        if guess == title.lower():
            print("Correct! The song was:", song.name.strip())
            return True
        elif guess == "quit".lower() or guess == "q".lower():
            return False
    
    print("Nice try! The song was:", song.name.strip())
    return False

def play_song(song, start_pos, guess_time):
    # FUNCTION: Starts and stops music playback
    # PARAMETERS: (int start_pos) starting position of trackin ms
    #             (int guess_time) amount of playback time in seconds
    # RETURNS: None

    #sp.volume(60)
    sp.start_playback(uris=[song.uri], position_ms=start_pos)

    # Stop the song
    time.sleep(guess_time)
    sp.pause_playback()

  

def print_menu():
    # FUNCTION: Print game menu
    # PARAMETERS: None
    # RETURNS: User input of response
    print()
    print("{:^30}".format("~ Guess The Song ~"))
    print("{:<10}".format("Enter 1 for the Daily Challenge"))
    print("{:^10}".format("Enter 2 for Challenge Mode with an artist"))
    print("{:^10}".format("Enter 3 for Challenge Mode with an playlist"))
    print("{:^10}".format("Enter 4 for timed with an artist"))
    print("{:^10}".format("Enter 5 for timed with an playlist"))
    print("{:^10}".format("Enter q to quit"))
    print()

    return input()

def print_score(score, max_score):
    print
    print("{:^30}".format("Your score was: " + str(score)))
    if score > max_score:
        print("{:^30}".format("New High Score!"))
        max_score = score
    else:
        print("{:^30}".format("Best Score: " + str(score)))

if __name__ == '__main__':
    # Connect and authorize spotify/spotipy
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token = get_token()
    sp = connect_spotipy()
    daily_completion_date = None

    # Get user gamemode and begin game
    freeplay_artist_max_score = 0
    freeplay_playlist_max_score = 0

    run = True
    while run:
        response = print_menu()
        if response == "1":
            # daily challenge
            if daily_completion_date != datetime.today().strftime('%Y-%m-%d'):
                daily_challenge() # get collectible
                daily_completion_date = datetime.today().strftime('%Y-%m-%d')
            else:
                print("{:^30}".format("Come back tomorrow for another challenge!"))
        elif response == "2":
            #freeplay artist
            score = freeplay_artist()
            print_score(score, freeplay_artist_max_score)
        elif response == "3":
            #freeplay playlist
            score = freeplay_playlist()
            print_score(score, freeplay_playlist_max_score)
        elif response == "4":
            #timed artist
            pass
        elif response == "5":
            #timed playlist
            pass
        elif response.lower() == "q":
            #shut down
            break
        else:
            print("Invalid Response")



        
    

    