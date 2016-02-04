# -*- coding: utf-8 -*-

import mpd
import time
import argparse
import podcastparser
import urllib
import pprint
import socket


class PersistentMPDClient(mpd.MPDClient):
    def __init__(self, socket=None, host=None, port=None):
        super(PersistentMPDClient, self).__init__()
        self.socket = socket
        self.host = "localhost"
        self.port = 6600
        # define as empty so intercepted calls prior to getting the actual list
        # don't fail
        # self.command_list = ['play_media', 'chrono', 'stop', 'volup',
        #                      'voldown', 'is_playing', 'podlist']
        self.command_list = []

        self.do_connect()
        # get list of available commands from client
        # self.command_list = self.commands()

        # commands not to intercept
        self.command_blacklist = ['ping']

        # wrap all valid MPDClient functions
        # in a ping-connection-retry wrapper
        for cmd in self.command_list:
            if cmd not in self.command_blacklist:
                if hasattr(super(PersistentMPDClient, self), cmd):
                    super_fun = super(PersistentMPDClient, self).__getattribute__(cmd)
                    new_fun = self.try_cmd(super_fun)
                    print("Setting interceptor for {}".format(cmd))
                    setattr(self, cmd, new_fun)
                else:
                    print("Attr {} not available!".format(cmd))

    # create a wrapper for a function (such as an MPDClient
    # member function) that will verify a connection (and
    # reconnect if necessary) before executing that function.
    # functions wrapped in this way should always succeed
    # (if the server is up)
    # we ping first because we don't want to retry the same
    # function if there's a failure, we want to use the noop
    # to check connectivity
    def try_cmd(self, cmd_fun):
        def fun(*pargs, **kwargs):
            try:
                # print("Attemping to ping...")
                self.ping()
            except (mpd.ConnectionError, OSError) as e:
                # print("lost connection.")
                # print("trying to reconnect.")
                self.do_connect()
            return cmd_fun(*pargs, **kwargs)
        return fun

    # needs a name that does not collide with parent connect() function
    def do_connect(self):
        try:
            try:
                # print("Attempting to disconnect.")
                self.disconnect()
            # if it's a TCP connection, we'll get a socket error
            # if we try to disconnect when the connection is lost
            except mpd.ConnectionError as e:
                # print("Disconnect failed, so what?")
                pass
            # if it's a socket connection, we'll get a BrokenPipeError
            # if we try to disconnect when the connection is lost
            # but we have to retry the disconnect, because we'll get
            # an "Already connected" error if we don't.
            # the second one should succeed.
            except BrokenPipeError as e:
                # print("Pipe closed, retrying disconnect.")
                try:
                    # print("Retrying disconnect.")
                    self.disconnect()
                except Exception as e:
                    print("Second disconnect failed, yikes.")
                    print(e)
                    pass
            if self.socket:
                # print("Connecting to {}".format(self.socket))
                self.connect(self.socket, None)
            else:
                #  print("Connecting to {}:{}".format(self.host, self.port))
                self.connect(self.host, self.port)
        except socket.error as e:
            print("Connection refused.")
            # print(e)

    def play_media(self,
        media="http://audio.scdn.arkena.com/11010/franceculture-midfi128.mp3"):
        """Start player with media(url) arg."""
        self.clear()
        self.add(media)
        self.setvol(90)
        self.play()

    def chrono(self,
               chrono,
               media="http://audio.scdn.arkena.com/11010/franceculture-midfi128.mp3"):
        """Start player with media(url) arg."""
        self.clear()
        self.add(media)
        self.setvol(90)
        self.play()

    def podlist(self, media):
        """Get podcast infos(parsed)."""
        parsed = podcastparser.parse(media, urllib.urlopen(media))
        return parsed

    def volup(self, n=5):
        """Set player volume up."""
        status = self.status()
        nvol = int(status['volume']) + n
        if nvol > 100:
            nvol = 100
        self.setvol(nvol)
        # print int(status['volume'])
        # print "Volume : %d" % nvol

    def voldown(self, n=5):
        """Set player volume down."""
        status = self.status()
        volume = status['volume']
        nvol = int(volume) - n
        if nvol < 0:
            nvol = 0
        self.setvol(nvol)
        # print int(status['volume'])
        # print "Volume : %d" % nvol

    def is_playing(self):
        """Verify player playing and update globale MPDstatut."""
        if self.status()['state'] == 'stop':
            return False
        else:
            return True


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
    myplayer = PersistentMPDClient()
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
