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


class GrooveSync:

    def __init__(self):
        _token = None
        _user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) \
            Chrome/19.0.1084.56 Safari/536.5"

        self.URL = "grooveshark.com"
        self.htmlclient = ('htmlshark', '20130520', 'nuggetsOfBaller', {
            "User-Agent": _user_agent,
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip"
        })
        self.jsqueue = ['jsqueue', '20130520', 'chickenFingers']
        self.jsqueue.append({
            "User-Agent": _user_agent,
            "Referer": 'http://%s/JSQueue.swf?%s' % (self.URL, self.jsqueue[1]),
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json"
        })
        self.h = {
            'country': {
                'CC1': 72057594037927940,
                'CC2': 0,
                'CC3': 0,
                'CC4': 0,
                'ID': 57,
                'IPR': 0,
            },
            'privacy': 0,
            'session': (''.join(random.choice(string.digits + string.letters[:6]) for x in range(32))).lower(),
            'uuid': str.upper(str(uuid.uuid4()))
        }

        self.stats = {
            'total': 0,
            'downloaded': 0,
            'duplicated': 0,
            'skipped': 0
        }

        self.download_directory = ''
        self.username = ''

        self.getToken()
        self.queueID = self.getQueueID()
        self.load_info()
        self.sync()

    def load_info(self):
        if os.path.isfile('.info'):
            if '--reset' in sys.argv:
                os.remove('.info')
            else:
                f = open('.info', 'r')
                info = f.read(4096).split('\n')
                f.close()
                self.download_directory = info[0]
                self.username = info[1]

    def save_info(self):
        if not os.path.isfile('.info'):
            f = open('.info', 'w')
            f.write(self.download_directory + '\n' + self.username)
            f.close()

    def sync(self):
        infoline_size = 80
        print('=' * infoline_size)
        print(' Starting Grooveshark collection synchronization...')
        print('=' * infoline_size)

        while not self.username:
            print('\nPlease type your Grooveshark username:'),
            self.username = raw_input()

        user_data = self.getUserData(self.username)
        if user_data:
            user_id = user_data['UserID']
            fname = user_data['FName'].split(' ')[0]
            print('\nHello, ' + fname + '!')
            print('')
        else:
            print('Error: user not found. Exiting...\n')
            return False

        while not os.path.isdir(self.download_directory):
            current_dir = os.path.abspath(os.path.curdir) + '/' + self.username
            print('Please type a directory to store the MP3 files [' + current_dir + ']:'),
            self.download_directory = raw_input()
            if not self.download_directory.strip():
                if not os.path.exists(current_dir):
                    os.mkdir(current_dir)
                self.download_directory = current_dir

        self.save_info()

        print('Loading the songs in your collection...')

        songs = self.userGetSongsInLibrary(user_id)
        i = 0
        duplicated = []
        self.stats['total'] += len(songs)

        #Collection
        if not os.path.isdir(self.download_directory + '/collection'):
            os.mkdir(self.download_directory + '/collection')

        if len(songs) > 0:
            print(str(len(songs)) + ' songs found. Synchronizing...\n')

            for currentSong in songs:
                i += 1
                artist_name = self.clear_string(currentSong["ArtistName"])
                song_name = self.clear_string(currentSong["Name"])
                output_file = self.download_directory + '/collection/' + artist_name + ' - ' + song_name + '.mp3'

                if output_file in duplicated:
                    print('>>> Duplicated song: ' + output_file)
                    self.stats['duplicated'] += 1
                else:
                    duplicated.append(output_file)

                if not os.path.isfile(output_file):
                    print('')
                    msg = str(i) + ') New song found, downloading... ' + artist_name + ' - ' + song_name
                    print(msg)

                    self.download_song(currentSong, output_file)

                else:
                    msg = str(i) + ') Song already downloaded, skipping file... (' + str(round(os.path.getsize(output_file) / 1024.0 / 1024.0, 1)) + ' MB) ' + output_file
                    print(msg)
                    self.stats['skipped'] += 1
        else:
            print('No songs were found. Nothing to do here.')

        print('')
        print('Loading playlists...')

        #Playlists
        playlists = self.userGetPlaylists(user_id)
        i = 0
        #duplicated = []
        #stats['total'] += len(songs)

        if not os.path.isdir(self.download_directory + '/playlists'):
            os.mkdir(self.download_directory + '/playlists')

        if len(playlists) > 0:
            print(str(len(playlists)) + ' playlists found.')

            for playlist in playlists:
                i += 1
                print('')
                print('Entering playlist #' + str(i) + ' - ' + playlist['Name'])

                if not os.path.isdir(self.download_directory + '/playlists/' + playlist['Name']):
                    os.mkdir(self.download_directory + '/playlists/' + playlist['Name'])

                playlist_songs = self.playlistGetSongs(playlist['PlaylistID'])
                print(str(len(playlist_songs)) + ' songs found in the playlist.')
                print('')
                j = 0

                for song in playlist_songs:
                    j += 1
                    artist_name = self.clear_string(song["ArtistName"])
                    song_name = self.clear_string(song["Name"])
                    output_file = self.download_directory + '/playlists/' + playlist['Name'] + '/' + artist_name + ' - ' + song_name + '.mp3'

                    if not os.path.isfile(output_file):
                        print('')
                        msg = str(j) + ') New song found, downloading... ' + artist_name + ' - ' + song_name
                        print(msg)

                        self.download_song(song, output_file)

                    else:
                        msg = str(j) + ') Song already downloaded, skipping file... (' + str(round(os.path.getsize(output_file) / 1024.0 / 1024.0, 1)) + ' MB) ' + output_file
                        print(msg)
                        self.stats['skipped'] += 1

        else:
            print('OK, ' + str(len(playlists)) + ' playlists found. Nothing to do here.')

        print('=' * infoline_size)
        print(' Finish! Grooveshark collection synchronized.')
        print('')
        print(' Stats:')
        print('   Downloaded: ' + str(self.stats['downloaded']))
        print('   Skipped: ' + str(self.stats['skipped']))
        print('   Duplicated: ' + str(self.stats['duplicated']))
        print('   ---------------')
        print('   Total: ' + str(self.stats['total']))
        print('=' * infoline_size)

    #Generate a token from the method and the secret string (which changes once in a while)
    def prep_token(self, method, secret):
        rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
        return rnd + hashlib.sha1('%s:%s:%s:%s' % (method, _token, secret, rnd)).hexdigest()

    #Fetch a queueID (right now we randomly generate it)
    def getQueueID(self):
        return random.randint(10000000000000000000000, 99999999999999999999999) #For now this will do

    #Get the static token issued by sharkAttack!
    def getToken(self):
        global h, _token
        p = {}
        p["parameters"] = {}
        p["parameters"]["secretKey"] = hashlib.md5(self.h["session"]).hexdigest()
        p["method"] = "getCommunicationToken"
        p["header"] = self.h
        p["header"]["client"] = self.htmlclient[0]
        p["header"]["clientRevision"] = self.htmlclient[1]
        conn = httplib.HTTPSConnection(self.URL)
        conn.request("POST", "/more.php", json.JSONEncoder().encode(p), self.htmlclient[3])
        _token = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

    #Process a search and return the result as a list.
    def getResultsFromSearch(self, query, what="Songs"):
        p = {}
        p["parameters"] = {}
        p["parameters"]["type"] = what
        p["parameters"]["query"] = query
        p["header"] = h
        p["header"]["client"] = self.htmlclient[0]
        p["header"]["clientRevision"] = self.htmlclient[1]
        p["header"]["token"] = self.prep_token("getResultsFromSearch", self.htmlclient[2])
        p["method"] = "getResultsFromSearch"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.htmlclient[3])
        j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
        try:
            return j["result"]["result"]["Songs"]
        except:
            return j["result"]["result"]

    #Get all songs by a certain artist
    def artistGetSongsEx(self, id, isVerified):
        p = {}
        p["parameters"] = {}
        p["parameters"]["artistID"] = id
        p["parameters"]["isVerifiedOrPopular"] = isVerified
        p["header"] = h
        p["header"]["client"] = self.htmlclient[0]
        p["header"]["clientRevision"] = self.htmlclient[1]
        p["header"]["token"] = self.prep_token("artistGetSongsEx", self.htmlclient[2])
        p["method"] = "artistGetSongsEx"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.htmlclient[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())

    #Get the streamKey used to download the songs off of the servers.
    def getStreamKeyFromSongIDs(self, id):
        p = {}
        p["parameters"] = {}
        p["parameters"]["type"] = 8
        p["parameters"]["mobile"] = False
        p["parameters"]["prefetch"] = False
        p["parameters"]["songIDs"] = [id]
        p["parameters"]["country"] = self.h["country"]
        p["header"] = self.h
        p["header"]["client"] = self.jsqueue[0]
        p["header"]["clientRevision"] = self.jsqueue[1]
        p["header"]["token"] = self.prep_token("getStreamKeysFromSongIDs", self.jsqueue[2])
        p["method"] = "getStreamKeysFromSongIDs"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

    #Add a song to the browser queue, used to imitate a browser
    def addSongsToQueue(self, songObj, songQueueID, source = "user"):
        queueObj = {}
        queueObj["songID"] = songObj["SongID"]
        queueObj["artistID"] = songObj["ArtistID"]
        queueObj["source"] = source
        queueObj["songQueueSongID"] = 1
        p = {}
        p["parameters"] = {}
        p["parameters"]["songIDsArtistIDs"] = [queueObj]
        p["parameters"]["songQueueID"] = songQueueID
        p["header"] = self.h
        p["header"]["client"] = self.jsqueue[0]
        p["header"]["clientRevision"] = self.jsqueue[1]
        p["header"]["token"] = self.prep_token("addSongsToQueue", self.jsqueue[2])
        p["method"] = "addSongsToQueue"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]


    #Remove a song from the browser queue, used to imitate a browser, in conjunction with the one above.
    def removeSongsFromQueue(self, songQueueID, userRemoved = True):
        p = {}
        p["parameters"] = {}
        p["parameters"]["songQueueID"] = songQueueID
        p["parameters"]["userRemoved"] = True
        p["parameters"]["songQueueSongIDs"]=[1]
        p["header"] = h
        p["header"]["client"] = self.jsqueue[0]
        p["header"]["clientRevision"] = self.jsqueue[1]
        p["header"]["token"] = self.prep_token("removeSongsFromQueue", self.jsqueue[2])
        p["method"] = "removeSongsFromQueue"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]


    #Mark the song as being played more then 30 seconds, used if the download of a songs takes a long time.
    def markStreamKeyOver30Seconds(self, songID, songQueueID, streamServer, streamKey):
        p = {}
        p["parameters"] = {}
        p["parameters"]["songQueueID"] = songQueueID
        p["parameters"]["streamServerID"] = streamServer
        p["parameters"]["songID"] = songID
        p["parameters"]["streamKey"] = streamKey
        p["parameters"]["songQueueSongID"] = 1
        p["header"] = h
        p["header"]["client"] = self.jsqueue[0]
        p["header"]["clientRevision"] = self.jsqueue[1]
        p["header"]["token"] = self.prep_token("markStreamKeyOver30Seconds", self.jsqueue[2])
        p["method"] = "markStreamKeyOver30Seconds"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

    #Mark the song as downloaded, hopefully stopping us from getting banned.
    def markSongDownloadedEx(self, streamServer, songID, streamKey):
        p = {}
        p["parameters"] = {}
        p["parameters"]["streamServerID"] = streamServer
        p["parameters"]["songID"] = songID
        p["parameters"]["streamKey"] = streamKey
        p["header"] = self.h
        p["header"]["client"] = self.jsqueue[0]
        p["header"]["clientRevision"] = self.jsqueue[1]
        p["header"]["token"] = self.prep_token("markSongDownloadedEx", self.jsqueue[2])
        p["method"] = "markSongDownloadedEx"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

    def getUserData(self, username):
        p = {}
        p["parameters"] = {}
        p["parameters"]["name"] = username
        p["header"] = self.h
        p["header"]["client"] = self.htmlclient[0]
        p["header"]["clientRevision"] = self.htmlclient[1]
        p["header"]["token"] = self.prep_token("getItemByPageName", self.htmlclient[2])
        p["method"] = "getItemByPageName"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        decoded = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())['result']

        if 'user' in decoded:
            return decoded['user']
        return False

    #Load user's collection list
    def userGetSongsInLibrary(self, user_id):
        p = {}
        p["parameters"] = {}
        p["parameters"]["page"] = '0'
        p["parameters"]["userID"] = str(user_id)
        p["header"] = self.h
        p["header"]["client"] = self.htmlclient[0]
        p["header"]["clientRevision"] = self.htmlclient[1]
        p["header"]["token"] = self.prep_token("userGetSongsInLibrary", self.htmlclient[2])
        p["method"] = "userGetSongsInLibrary"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]['Songs']

    def userGetPlaylists(self, user_id):
        p = {}
        p["parameters"] = {}
        p["parameters"]["userID"] = user_id
        p["header"] = self.h
        p["header"]["client"] = self.htmlclient[0]
        p["header"]["clientRevision"] = self.htmlclient[1]
        p["header"]["token"] = self.prep_token("userGetPlaylists", self.htmlclient[2])
        p["method"] = "userGetPlaylists"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())['result']['Playlists']

    def playlistGetSongs(self, playlist_id):
        p = {}
        p["parameters"] = {}
        p["parameters"]["playlistID"] = playlist_id
        p["header"] = self.h
        p["header"]["client"] = self.htmlclient[0]
        p["header"]["clientRevision"] = self.htmlclient[1]
        p["header"]["token"] = self.prep_token("playlistGetSongs", self.htmlclient[2])
        p["method"] = "playlistGetSongs"
        conn = httplib.HTTPConnection(self.URL)
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), self.jsqueue[3])
        return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())['result']['Songs']

    def download_song(self, currentSong, output_file):
        self.addSongsToQueue(currentSong, self.queueID) #Add the song to the queue
        stream = self.getStreamKeyFromSongIDs(currentSong["SongID"]) #Get the StreamKey for the selected song
        for k, v in stream.iteritems():
            stream = v
        if stream == []:
            print "Failed"
            exit()

        self.stats['downloaded'] += 1

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
                print('\rDownloading file...'),
                print(str(int(current_size / float(total_size) * 100)) + '%'),
            else:
                break
        f.close()

        print('- Done!'),
        print(' '*100)
        self.markSongDownloadedEx(stream["ip"], currentSong["SongID"], stream["streamKey"]) #This is the important part, hopefully this will stop grooveshark from banning us.

    def clear_string(self, _str):
        #_str = _str.decode('utf-8', 'ignore')
        _str = _str.replace('/', '-')
        return _str


if __name__ == "__main__":

    GrooveSync()

    if 'uname' not in dir(os):
        print('Type ENTER to exit')
        raw_input()