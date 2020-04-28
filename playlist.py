import gmusicapi
import spotipy
import spotipy.util as util
import requests
import re
import os
import string
import json

#CONSTANTS
SCOPE = "user-library-read playlist-modify-public playlist-read-collaborative playlist-read-private playlist-modify-private"
URL_REGEX_PATTERN = "^(https://open.spotify.com/playlist/).+$"

#Fill these in!
SPOTIPY_CLIENT_ID = "XXXX"
SPOTIPY_CLIENT_SECRET = "XXXX"
SPOTIPY_REDIRECT_URI = "http://localhost/"
USERNAME = "user"
ANDROID_MAC_ADDRESS = "XXXX"

#Authenticates Spotify and Google Play Music
token = util.prompt_for_user_token(USERNAME, SCOPE, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)
api = gmusicapi.Mobileclient()

#Checks for existing Google Play credentials, using them if found or creating them otherwise
if not(os.path.exists("creds") and os.path.isfile("creds")):
    result = api.perform_oauth("creds", True)
else:
    result = api.oauth_login(oauth_credentials="creds", device_id=ANDROID_MAC_ADDRESS)

if not result:
    print("Google Play authentication error.")
    quit()

#FUNCTIONS

def extractSpotifyIDFromURL(url):
    return url.split("https://open.spotify.com/playlist/")[1]

#Checks for a matching (close enough) title between two strings - e.g. a track name
def matchTitle(string1, string2):
    #Try lowercase matching
    string1 = string1.lower()
    string2 = string2.lower()

    if string1 == string2:
        return True
    #Check for extended title
    if string1 in string2 or string2 in string1:
        return True

    #Try removing punctuation
    string1 = string1.translate(str.maketrans(dict.fromkeys(string.punctuation)))
    string2 = string2.translate(str.maketrans(dict.fromkeys(string.punctuation)))

    if string1 == string2:
        return True
    if string1 in string2 or string2 in string1:
        return True

    #Try removing whitespace
    string1 = ''.join(string1.split())
    string2 = ''.join(string2.split())

    if string1 == string2:
        return True
    if string1 in string2 or string2 in string1:
        return True

    return False #no match

#Checks for a matching track on Spotify, checking for variations in metadata
def findTrackOnSpotify(album, artist, track):
    albumName = album.lower()
    artistName = artist.lower()
    trackName = track.lower()

    #Basic lowercase search
    query = "album:" + albumName + " artist:" + artistName + " track:" + trackName

    #Query Spotify
    results = (spotify.search(query))["tracks"]["items"]
    if results: #If matches were found
        return results

    #Strips content in ()
    albumName = re.sub(r" ?\([^)]+\)", "", albumName)
    artistName = re.sub(r" ?\([^)]+\)", "", artistName)
    trackName = re.sub(r" ?\([^)]+\)", "", trackName)
    query = "album:" + albumName + " artist:" + artistName + " track:" + trackName

    results = (spotify.search(query))["tracks"]["items"]
    if results:
        return results

    #Strips content in []
    albumName = re.sub(r" ?\[[^\]]+\]", "", albumName)
    artistName = re.sub(r" ?\[[^\]]+\]", "", artistName)
    trackName = re.sub(r" ?\[[^\]]+\]", "", trackName)
    query = "album:" + albumName + " artist:" + artistName + " track:" + trackName

    results = (spotify.search(query))["tracks"]["items"]
    if results:
        return results

    #Strips content after : character
    albumName = re.sub(r" ?\:[^:]+", "", albumName)
    artistName = re.sub(r" ?\:[^:]+", "", artistName)
    trackName = re.sub(r" ?\:[^:]+", "", trackName)
    query = "album:" + albumName + " artist:" + artistName + " track:" + trackName

    results = (spotify.search(query))["tracks"]["items"]
    if results:
        return results

    #Removes punctuation
    albumName = albumName.translate(str.maketrans(dict.fromkeys(string.punctuation)))
    artistName = artistName.translate(str.maketrans(dict.fromkeys(string.punctuation)))
    trackName = trackName.translate(str.maketrans(dict.fromkeys(string.punctuation)))
    query = "album:" + albumName + " artist:" + artistName + " track:" + trackName

    results = (spotify.search(query))["tracks"]["items"]
    if results:
        return results

    #Check if only album and track match
    query = "album:" + album + " track:" + track

    results = (spotify.search(query))["tracks"]["items"]
    if results:
        return results

    #Check if only artist and track match
    query = "artist:" + artistName + " track:" + trackName

    results = (spotify.search(query))["tracks"]["items"]
    if results:
        return results

    #Check if only 1 track with that title exists
    query = "track:" + track

    results = (spotify.search(query))["tracks"]["items"]
    if len(results) == 1:
        return results

    return False #No match found

#Gets playlist (owned by the user) object from a Spotify URL
#def findOwnedSpotifyPlaylist(url):
    # targetPlaylist = None
    # playlistID = extractSpotifyIDFromURL(url)
    # print(playlistID)

    # #Gets all playlists for user
    # playlists = spotify.user_playlists(USERNAME)

    # #Iterate through all playlists to find one with matching ID
    # for playlist in playlists["items"]:
    #     if playlist["owner"]["id"] == USERNAME:
    #         if playlist["id"] == playlistID:
    #             targetPlaylist = playlist
    #             print(targetPlaylist["name"] + " - " + targetPlaylist["id"])

    # return targetPlaylist

#Gets playlist object from a Spotify URL
def findSpotifyPlaylist(url):
    targetPlaylist = None
    playlistID = extractSpotifyIDFromURL(url)

    #Authorises Spotify Web API (Python library doesn't support playlists not owned by user)
    auth = util.oauth2.SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
    token = auth.get_access_token()
    headers = {"Authorization": "Bearer "+token}

    #Get playlist object with the ID from the passed playlist
    response = requests.get("https://api.spotify.com/v1/playlists/"+playlistID, headers=headers)
    
    if response.status_code == 200: #success
        targetPlaylist = response.json() #extracts JSON object
        return targetPlaylist
    else:
        return None

#Gets playlist object from a Google Play Music playlist name
def findGooglePlaylist(playlistName):
    targetPlaylist = None

    #Gets contents of all playlists (library doesn't support getting specific playlist)
    allPlaylists = api.get_all_user_playlist_contents()
    for playlist in allPlaylists:
        #Find (first) playlist with matching name
        if playlist["name"] == playlistName:
            targetPlaylist = playlist
            break
    return targetPlaylist

#Request input for (Spotify) playlist URL and validate it
def acceptPlaylistURL():
    while True: #loop until valid (at which point simply return)
        playlistURL = input("Please enter the URL of the playlist: ")
        if re.match("^(https://open.spotify.com/playlist/).+$", playlistURL): #checks valid playlist URL
            return playlistURL
        else:
            print("Please input a valid Spotify playlist URL.")

#Extracts album, artist and track names for each item in a (Spotify) playlist
def getInfoFromSpotifyPlaylist(targetPlaylist):
    playlistItems = []

    #Get the tracks from the specified playlist
    tracks = spotify.user_playlist_tracks(USERNAME, playlist_id=targetPlaylist["id"])
    length = tracks["total"] #number of tracks
    for i in range(length):
        current = tracks["items"][i]["track"] #current track
        albumName = current["album"]["name"] #dict
        artistName = current["album"]["artists"][0]["name"] #list
        trackName = current["name"]

        #Save album, artist and track name for current track, and add to array of tracks
        playlistItem = [albumName, artistName, trackName]
        playlistItems.append(playlistItem)

    return playlistItems

#Extracts album, artist and track names for each item in a (Google) playlist
def getInfoFromGooglePlaylist(targetPlaylist):
    trackIDs = []
    #Extract IDs of each track in the playlist
    for track in targetPlaylist["tracks"]:
        trackIDs.append(track["trackId"])
    
    tracksInfo = []
    library = api.get_all_songs()
    #Looks for matching track in Google Play library
    for track in library:
        if track["id"] in trackIDs:
            #Add album, artist and track names to 2D array
            info = []
            info.append(track["album"])
            info.append(track["albumArtist"])
            info.append(track["title"])
            tracksInfo.append(info)

    return tracksInfo

#Adds a track (array with album, artist and track name) to a Google Play Music playlist with specified ID
def addSongsToGooglePlaylistFromInfo(playlist_id, track):
    #track should be array with 3 elements
    albumName = track[0]
    artistName = track[1]
    trackName = track[2]

    print(albumName + " - " + artistName + " - " + trackName)

    library = api.get_all_songs()
    track_ids = []

    #Looks for matching track in Google Play library
    for track in library:
        if matchTitle(track["album"], albumName) and matchTitle(track["albumArtist"], artistName) and matchTitle(track["title"], trackName):
            track_ids.append(track["id"]) #gets track ID
            api.add_songs_to_playlist(playlist_id, track_ids) #adds track to playlist
            return True
    return False #could not find track in library

#Converts a Spotify playlist to a Google Play Music playlist
def spotifyToGoogle():
    #Gets Spotify playlist from inputted URL
    playlistURL = acceptPlaylistURL()
    targetPlaylist = findSpotifyPlaylist(playlistURL)

    if targetPlaylist == None:
        print("No matching playlist found.")
    else:
        print("Matching playlist found.")

        #Get playlist metadata
        playlistName = targetPlaylist["name"]
        try:
            playlistDescription = targetPlaylist["description"]
        except:
            playlistDescription = ""

        #Get information on tracks in playlist
        playlistItems = getInfoFromSpotifyPlaylist(targetPlaylist)

        #Create new Google Play playlist
        playlist_id = api.create_playlist(name=playlistName, description=playlistDescription)
        failures = [] #Stores the tracks that could not be found in Google Play library
        for i in playlistItems: #add each track to Google Play playlist
            if not addSongsToGooglePlaylistFromInfo(playlist_id, i): #could not find track
                failures.append(i)

        if failures: #output any tracks that could not be found
            print("Certain tracks could not be found in the Google Play library:")
            missing_tracks = []
            for failure in failures:
                track = failure[0] + " - " + failure[1] + " - " + failure[2]
                print(track)
                missing_tracks.append(track)

            new_description = playlistDescription + "\n" + playlistURL + "\nMissing from original playlist:\n" + "\n".join(missing_tracks)
            api.edit_playlist(playlist_id, new_description=new_description)


#Converts a Google Play Music playlist to a Spotify playlist
def googleToSpotify():
    print("Please enter the name of the Google Play Music playlist you would like to convert.")
    print("Note that if multiple playlists exist with the same name, the first one will be selected; rename the playlist to be unique to avoid this.")
    playlistName = input("| ") #Gets playlist name
    targetPlaylist = findGooglePlaylist(playlistName) #Finds playlist matching inputted name

    if targetPlaylist == None:
        print("No matching playlist found.")
    else:
        print("Matching playlist found.")

        #Get playlist description, if there is one
        try:
            playlistDescription = targetPlaylist["description"]
        except:
            playlistDescription = ""

        #Gets album, artist and track names for the contents of the playlist
        tracksInfo = getInfoFromGooglePlaylist(targetPlaylist)

        print("Would you like the Spotify playlist to be public? (y/n)")
        choice = input("| ")
        public = False
        if choice.lower() == "y":
            public = True

        #Create new Spotify playlist
        spotifyPlaylist = spotify.user_playlist_create(USERNAME, playlistName, public=public, description=playlistDescription)

        spotifyIDs = []
        failures = []

        #For every track from Google to be added
        for track in tracksInfo:
            #Check if track exists on Spotify, and get track object if so
            result = findTrackOnSpotify(track[0], track[1], track[2])
            if not result: #No matching track found
                failure = [track[0], track[1], track[2]]
                failures.append(failure)
            else:
                print(track[0] + " - " + track[1] + " - " + track[2])
                spotifyIDs.append(result[0]["id"]) #Add ID of first matching result
        

        if failures: #output any tracks that could not be found
            print("Certain tracks could not be found on Spotify (these tracks may be unavailable, or have metadata that does not match Google's):")
            missing_tracks = ["Missing from original playlist:"]
            for failure in failures:
                track = failure[0] + " - " + failure[1] + " - " + failure[2]
                print(track)
                missing_tracks.append(track)

            new_description = playlistDescription + " | ".join(missing_tracks)
            spotify.user_playlist_change_details(USERNAME, spotifyPlaylist["id"], description=new_description[:300]) # 300 character limit
        
        #Add tracks to Spotify playlist
        spotify.user_playlist_add_tracks(USERNAME, spotifyPlaylist["id"], spotifyIDs)
        print("Playlist converted: https://open.spotify.com/playlist/" + str(spotifyPlaylist["id"]))


#If Spotify successfully authenticated
if token:
    spotify = spotipy.Spotify(auth=token)

    #Menu loop
    con = True
    while con:
        print("What would you like to do?")
        print("(1) Convert Spotify playlist to Google Play Music")
        print("(2) Convert Google Play Music playlist to Spotify")
        print("(3) Exit")
        choice = input("| ")

        if choice == "3": #Exit
            con = False
        elif choice == "2":
            googleToSpotify()
        elif choice == "1":
            spotifyToGoogle()
        else:
            print("Invalid response, please enter 1, 2, or 3 to choose an option.")
    print("Exiting...")
else:
    print("Spotify authentication error.")
    quit()