# -*- coding: utf-8 -*-

# from mpd import MPDClient
import mpd
import time
import argparse
import podcastparser
import urllib
import pprint


class player():

    """
    Mpdclient object.
    reconnect wrapper for ovoiding MPD deco.
    method: clear, play, stop, volup, voldown, is_playing
    is_playing return mpd.status
    """

    def __init__(self):
        """Connection init."""
        self.client = mpd.MPDClient()
        self.client.timeout = 10
        self.client.idletimeout = None
        try:
            self.client.connect("localhost", 6600)
            self.client.update()
        except Exception:
            print "Can't Connect to MPD..."

    #  ============ TEST ============
    def __getattr__(self):
        """Catch and solve mpd.ConnectionError issue"""
        return self._call_with_reconnect(getattr(self.client))

    def _call_with_reconnect(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except mpd.ConnectionError:
                self.connect(self.host, self.port)
                return func(*args, **kwargs)
        return wrapper
    #  ============ FIN TEST ============
#
    def clear(self):
        """Clear player playlist."""
        self.client.clear()

    def play(self,
        media="http://audio.scdn.arkena.com/11010/franceculture-midfi128.mp3"):
        """Start player with media(url) arg."""
        self.client.clear()
        self.client.add(media)
        self.client.setvol(90)
        self.client.play()

    def chrono(self,
               chrono,
               media="http://audio.scdn.arkena.com/11010/franceculture-midfi128.mp3"):
        """Start player with media(url) arg."""
        self.client.clear()
        self.client.add(media)
        self.client.setvol(90)
        self.client.play()

    def podlist(self, media):
        """Get podcast infos(parsed)."""
        parsed = podcastparser.parse(media, urllib.urlopen(media))
        return parsed

    def stop(self):
        """Stop player."""
        self.client.stop()

    def volup(self, n=5):
        """Set player volume up."""
        status = self.client.status()
        nvol = int(status['volume']) + n
        if nvol > 100:
            nvol = 100
        self.client.setvol(nvol)
        print int(status['volume'])
        print "Volume : %d" % nvol

    def voldown(self, n=5):
        """Set player volume down."""
        status = self.client.status()
        volume = status['volume']
        nvol = int(volume) - n
        if nvol < 0:
            nvol = 0
        self.client.setvol(nvol)
        print int(status['volume'])
        print "Volume : %d" % nvol

    def status(self):
        """Get player status."""
        current_status = self.client.status()
        if (current_status):
            status = current_status

        monstatus = {}

        for key, value in status.items():
            monstatus[key] = value.encode('utf-8')

        maplaylist = self.client.playlistid()
        try:
            for key, value in maplaylist[0].items():
                monstatus[key] = value.decode('utf-8')
        except:
            pass

        return monstatus

    def is_playing(self):
        """Verify player playing and update globale MPDstatut."""

#        if self.client.status()['state'] == 'stop':
#            return False
#        else:
#            return True

        pass


def main():
    """Playing media."""
    parser = argparse.ArgumentParser(
        description="This script play a given media on the mpd (local) server")
    parser.add_argument("-c",
        choices=['play', 'stop', 'status', 'volup', 'voldown', 'pod'],
        required=True)
    parser.add_argument("-u", help="url to play")

    args = parser.parse_args()
    media = args.u
    command = args.c

    myplayer = player()
    if command == 'play':
        if media is not None:
            myplayer.play(media)
        else:
            print "You must enter a media url/path to play"
    elif command == 'stop':
        myplayer.stop()
    elif command == 'volup':
        myplayer.volup()
    elif command == 'voldown':
        myplayer.voldown()
    elif command == 'status':
        state = myplayer.status()
        for cle, val in state.items():
            print cle + " : " + val
    elif command == 'podlist':
        parsed = podcastparser.parse(media, urllib.urlopen(media))
        pprint.pprint(parsed)

if __name__ == "__main__":
    main()
