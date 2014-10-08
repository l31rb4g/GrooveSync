#!/usr/bin/env python
#encoding: utf-8
import httplib
import StringIO
import hashlib
import uuid
import random
import string
import sys
import os
import gzip
import json
import re
import socket

_useragent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.56 Safari/536.5"
_token = None

URL = "grooveshark.com" #The base URL of Grooveshark
htmlclient = ('htmlshark', '20130520', 'nuggetsOfBaller', {"User-Agent":_useragent, "Content-Type":"application/json", "Accept-Encoding":"gzip"}) #Contains all the information posted with the htmlshark client
jsqueue = ['jsqueue', '20130520', 'chickenFingers']
jsqueue.append({"User-Agent":_useragent, "Referer": 'http://%s/JSQueue.swf?%s' % (URL, jsqueue[1]), "Accept-Encoding":"gzip", "Content-Type":"application/json"}) #Contains all the information specific to jsqueue

#Setting the static header (country, session and uuid)
h = {}
h["country"] = {}
h["country"]["CC1"] = 72057594037927940
h["country"]["CC2"] = 0
h["country"]["CC3"] = 0
h["country"]["CC4"] = 0
h["country"]["ID"] = 57
h["country"]["IPR"] = 0
h["privacy"] = 0
h["session"] = (''.join(random.choice(string.digits + string.letters[:6]) for x in range(32))).lower()
h["uuid"] = str.upper(str(uuid.uuid4()))


#Generate a token from the method and the secret string (which changes once in a while)
def prep_token(method, secret):
    rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
    return rnd + hashlib.sha1('%s:%s:%s:%s' % (method, _token, secret, rnd)).hexdigest()


#Fetch a queueID (right now we randomly generate it)
def getQueueID():
    return random.randint(10000000000000000000000, 99999999999999999999999) #For now this will do


#Get the static token issued by sharkAttack!
def getToken():
    global h, _token
    p = {}
    p["parameters"] = {}
    p["parameters"]["secretKey"] = hashlib.md5(h["session"]).hexdigest()
    p["method"] = "getCommunicationToken"
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    conn = httplib.HTTPSConnection(URL)
    conn.request("POST", "/more.php", json.JSONEncoder().encode(p), htmlclient[3])
    _token = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

#Process a search and return the result as a list.
def getResultsFromSearch(query, what="Songs"):
    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = what
    p["parameters"]["query"] = query
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prep_token("getResultsFromSearch", htmlclient[2])
    p["method"] = "getResultsFromSearch"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), htmlclient[3])
    j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
    try:
        return j["result"]["result"]["Songs"]
    except:
        return j["result"]["result"]

#Get all songs by a certain artist
def artistGetSongsEx(id, isVerified):
    p = {}
    p["parameters"] = {}
    p["parameters"]["artistID"] = id
    p["parameters"]["isVerifiedOrPopular"] = isVerified
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prep_token("artistGetSongsEx", htmlclient[2])
    p["method"] = "artistGetSongsEx"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), htmlclient[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())

#Get the streamKey used to download the songs off of the servers.
def getStreamKeyFromSongIDs(id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = 8
    p["parameters"]["mobile"] = False
    p["parameters"]["prefetch"] = False
    p["parameters"]["songIDs"] = [id]
    p["parameters"]["country"] = h["country"]
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prep_token("getStreamKeysFromSongIDs", jsqueue[2])
    p["method"] = "getStreamKeysFromSongIDs"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

#Add a song to the browser queue, used to imitate a browser
def addSongsToQueue(songObj, songQueueID, source = "user"):    
    queueObj = {}
    queueObj["songID"] = songObj["SongID"]
    queueObj["artistID"] = songObj["ArtistID"]
    queueObj["source"] = source
    queueObj["songQueueSongID"] = 1
    p = {}
    p["parameters"] = {}
    p["parameters"]["songIDsArtistIDs"] = [queueObj]
    p["parameters"]["songQueueID"] = songQueueID
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prep_token("addSongsToQueue", jsqueue[2])
    p["method"] = "addSongsToQueue"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]


#Remove a song from the browser queue, used to imitate a browser, in conjunction with the one above.
def removeSongsFromQueue(songQueueID, userRemoved = True):
    p = {}
    p["parameters"] = {}
    p["parameters"]["songQueueID"] = songQueueID
    p["parameters"]["userRemoved"] = True
    p["parameters"]["songQueueSongIDs"]=[1]
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prep_token("removeSongsFromQueue", jsqueue[2])
    p["method"] = "removeSongsFromQueue"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]


#Mark the song as being played more then 30 seconds, used if the download of a songs takes a long time.
def markStreamKeyOver30Seconds(songID, songQueueID, streamServer, streamKey):
    p = {}
    p["parameters"] = {}
    p["parameters"]["songQueueID"] = songQueueID
    p["parameters"]["streamServerID"] = streamServer
    p["parameters"]["songID"] = songID
    p["parameters"]["streamKey"] = streamKey
    p["parameters"]["songQueueSongID"] = 1
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prep_token("markStreamKeyOver30Seconds", jsqueue[2])
    p["method"] = "markStreamKeyOver30Seconds"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]


#Mark the song as downloaded, hopefully stopping us from getting banned.
def markSongDownloadedEx(streamServer, songID, streamKey):
    p = {}
    p["parameters"] = {}
    p["parameters"]["streamServerID"] = streamServer
    p["parameters"]["songID"] = songID
    p["parameters"]["streamKey"] = streamKey
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prep_token("markSongDownloadedEx", jsqueue[2])
    p["method"] = "markSongDownloadedEx"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]


def getUserData(username):
    p = {}
    p["parameters"] = {}
    p["parameters"]["name"] = username
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prep_token("getItemByPageName", htmlclient[2])
    p["method"] = "getItemByPageName"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())['result']['user']


#Load user's collection list
def userGetSongsInLibrary(user_id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["page"] = '0'
    p["parameters"]["userID"] = str(user_id)
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prep_token("userGetSongsInLibrary", htmlclient[2])
    p["method"] = "userGetSongsInLibrary"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]['Songs']


def userGetPlaylists(user_id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["userID"] = user_id
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prep_token("userGetPlaylists", htmlclient[2])
    p["method"] = "userGetPlaylists"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())['result']['Playlists']


def playlistGetSongs(playlist_id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["playlistID"] = playlist_id
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prep_token("playlistGetSongs", htmlclient[2])
    p["method"] = "playlistGetSongs"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())['result']['Songs']


def download_song(currentSong, output_file):
    addSongsToQueue(currentSong, queueID) #Add the song to the queue
    stream = getStreamKeyFromSongIDs(currentSong["SongID"]) #Get the StreamKey for the selected song
    for k, v in stream.iteritems():
        stream = v
    if stream == []:
        print "Failed"
        exit()

    stats['downloaded'] += 1

    sock = socket.socket()
    sock.connect((stream["ip"], 80))

    headers = 'POST /stream.php HTTP/1.1\r\n'
    headers += 'Host: ' + stream["ip"] + '\r\n'
    headers += 'Connection: keep-alive\r\n'
    headers += 'Content-Type: application/x-www-form-urlencoded\r\n'
    headers += 'Content-Length: ' + str(10 + len(stream["streamKey"])) + '\r\n'

    headers += '\r\n'
    headers += 'streamKey=' + stream["streamKey"] + '\r\n'
    headers += '\r\n'

    sock.send(headers)

    f = open(output_file, 'wb')
    rh = sock.recv(4096)
    current_size = len(rh)
    total_size = int(re.sub('.* Content-Length: ([0-9]+) .*', r'\1', rh.replace('\r', '').replace('\n', ' ')))

    while True:
        r = sock.recv(4096)
        current_size += len(r)
        if r:
            f.write(r)
            print('\r'),
            print('Downloading file...'),
            print(str(int(current_size / float(total_size) * 100)) + '%'),
        else:
            break
    f.close()

    print('\r'),
    print('Done!'),
    print(' '*100)
    markSongDownloadedEx(stream["ip"], currentSong["SongID"], stream["streamKey"]) #This is the important part, hopefully this will stop grooveshark from banning us.




def clear_string(_str):
    #_str = _str.decode('utf-8', 'ignore')
    _str = _str.replace('/', '-')
    return _str


if __name__ == "__main__":

    infoline_size = 80
    print('=' * infoline_size)
    print(' Starting Grooveshark collection synchronization...')
    print('=' * infoline_size)
    print('')

    download_directory = ''
    username = None
    stats = {
        'total': 0,
        'downloaded': 0,
        'duplicated': 0,
        'skipped': 0
    }

    if '--reset' in sys.argv:
        os.remove('.info')

    if os.path.isfile('.info'):
        f = open('.info', 'r')
        info = f.read(4096).split('\n')
        f.close()
        download_directory = info[0]
        username = info[1]

    while not os.path.isdir(download_directory):
        print('Please type a directory to store the MP3 files:'),
        download_directory = raw_input()

    while not username:
        print('Please type your Grooveshark username:'),
        username = raw_input()
        print('')

    if not os.path.isfile('.info'):
        f = open('.info', 'w')
        f.write(download_directory + '\n' + username)
        f.close()

    getToken() #Get a static token
    queueID = getQueueID()

    user_data = getUserData(username)
    user_id = user_data['UserID'] #17396521
    fname = user_data['FName'].split(' ')[0]

    print('Hello, ' + fname + '!')
    print('')

    print('Loading the songs in your collection...')

    songs = userGetSongsInLibrary(user_id)
    i = 0
    duplicated = []
    stats['total'] += len(songs)

    #Collection
    if not os.path.isdir(download_directory + '/collection'):
        os.mkdir(download_directory + '/collection')

    if len(songs) > 0:
        print(str(len(songs)) + ' songs found. Synchronizing...')

        for currentSong in songs:
            i += 1
            artist_name = clear_string(currentSong["ArtistName"])
            song_name = clear_string(currentSong["Name"])
            output_file = download_directory + '/collection/' + artist_name + ' - ' + song_name + '.mp3'

            if output_file in duplicated:
                print('>>> Duplicated song: ' + output_file)
                stats['duplicated'] += 1
            else:
                duplicated.append(output_file)

            if not os.path.isfile(output_file):
                print('')
                msg = str(i) + ') New song found, downloading... ' + artist_name + ' - ' + song_name
                print(msg)

                download_song(currentSong, output_file)

            else:
                msg = str(i) + ') Song already downloaded, skipping file... (' + str(round(os.path.getsize(output_file) / 1024.0 / 1024.0, 1)) + ' MB) ' + output_file
                print(msg)
                stats['skipped'] += 1
    else:
        print('No songs were found. Nothing to do here.')

    print('')
    print('Loading playlists...')

    #Playlists
    playlists = userGetPlaylists(user_id)
    i = 0
    #duplicated = []
    #stats['total'] += len(songs)

    if not os.path.isdir(download_directory + '/playlists'):
        os.mkdir(download_directory + '/playlists')

    if len(playlists) > 0:
        print(str(len(playlists)) + ' playlists found.')

        for playlist in playlists:
            i += 1
            print('')
            print('Entering playlist #' + str(i) + ' - ' + playlist['Name'])

            if not os.path.isdir(download_directory + '/playlists/' + playlist['Name']):
                os.mkdir(download_directory + '/playlists/' + playlist['Name'])

            playlist_songs = playlistGetSongs(playlist['PlaylistID'])
            print(str(len(playlist_songs)) + ' songs found in the playlist.')
            print('')
            j = 0

            for song in playlist_songs:
                j += 1
                artist_name = clear_string(song["ArtistName"])
                song_name = clear_string(song["Name"])
                output_file = download_directory + '/playlists/' + playlist['Name'] + '/' + artist_name + ' - ' + song_name + '.mp3'

                if not os.path.isfile(output_file):
                    print('')
                    msg = str(j) + ') New song found, downloading... ' + artist_name + ' - ' + song_name
                    print(msg)

                    download_song(song, output_file)

                else:
                    msg = str(j) + ') Song already downloaded, skipping file... (' + str(round(os.path.getsize(output_file) / 1024.0 / 1024.0, 1)) + ' MB) ' + output_file
                    print(msg)
                    stats['skipped'] += 1

    else:
        print('OK, ' + str(len(playlists)) + ' playlists found. Nothing to do here.')

    print('=' * infoline_size)
    print(' Finish! Grooveshark collection synchronized.')
    print('')
    print(' Stats:')
    print('   Downloaded: ' + str(stats['downloaded']))
    print('   Skipped: ' + str(stats['skipped']))
    print('   Duplicated: ' + str(stats['duplicated']))
    print('   ---------------')
    print('   Total: ' + str(stats['total']))
    print('=' * infoline_size)