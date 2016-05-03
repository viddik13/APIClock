# -*- coding: utf-8 -*-
import mpd
import socket
import podcastparser
import urllib



class PersistentMPDClient(mpd.MPDClient):
    def __init__(self, socket=None, host=None, port=None):


        super(PersistentMPDClient, self).__init__()
        self.socket = socket
        self.host = "127.0.0.1"
        self.port = 6600


        self.do_connect()
        # get list of available commands from client

        self.command_list = self.commands()
        # print self.command_list

        # commands not to intercept
        self.command_blacklist = ['ping']

        # wrap all valid MPDClient functions
        # in a ping-connection-retry wrapper
        print "Wrapping in ping-wrapper..."
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
                print "Attemping to ping..."
                self.ping()
            except (mpd.ConnectionError, OSError) as e:
                #                print("lost connection.")
                #                print("trying to reconnect.")
                self.do_connect()
            except socket.error as e:
                print "A socket error occured:", e
                self.do_connect()
            return cmd_fun(*pargs, **kwargs)

        return fun

    # needs a name that does not collide with parent connect() function
    def do_connect(self):
        try:
            try:
            #                print("Attempting to disconnect.")
                self.disconnect()
            # if it's a TCP connection, we'll get a socket error
            # if we try to disconnect when the connection is lost
            except mpd.ConnectionError as e:
                #                print("Disconnect failed, so what?")
                pass
            # if it's a socket connection, we'll get a BrokenPipeError
            # if we try to disconnect when the connection is lost
            # but we have to retry the disconnect, because we'll get
            # an "Already connected" error if we don't.
            # the second one should succeed.
            except socket.error as e:
                if e.errno == socket.errno.EPIPE:
                    # print "Broken pipe"
                    try:
                        # print("Retrying disconnect.")
                        self.disconnect()
                    except Exception as e:
                        # print("Second disconnect failed, yikes.")
                        print(e)
                        pass
                else:
                    # print "A socket error occured:", e
                    raise e
            if self.socket:
                print("Connecting to {}".format(self.socket))
                self.connect(self.socket, None)
            else:
                print("Connecting to {}:{}".format(self.host, self.port))
                self.connect(self.host, self.port)
        except socket.error as e:
            print("Connection refused.")

    def play_media(self,
        media="http://audio.scdn.arkena.com/11010/franceculture-midfi128.mp3"):
        """Start player with media(url) arg."""
        def function():
            self.clear()
            self.add(media)
            self.setvol(90)
            self.play()

        result = self.try_cmd(function())
        return result

    def next_play(self):
        def function():
            # load current user's actual playlit of current type media
            # play current item of list +1
            test = self.currentsong()['file']
            # get media type (http = stream), load and play next item of playlist
            if 'http' in test:
                print "media"
                print test
            else:
                print 'music'
            print test

        result = self.try_cmd(function())
        return result

    def prev_play(self):
        def function():
            # get current user's actual playlit of current type media
            pass

        result = self.try_cmd(function())
        return result

    def chrono(self,
               chrono,
               media="http://audio.scdn.arkena.com/11010/franceculture-midfi128.mp3"):
        def function():
            """Start player with media(url) arg."""
            self.clear()
            self.add(media)
            self.setvol(90)
            self.play()

        result = self.try_cmd(function())
        return result

    def podlist(self, media):
        def function():
            """Get podcast infos(parsed)."""
            parsed = podcastparser.parse(media, urllib.urlopen(media))
            return parsed

        result = self.try_cmd(function())
        return result

    def volup(self, n=5):
        def function():
            """Set player volume up."""
            status = self.status()
            nvol = int(status['volume']) + n
            if nvol > 100:
                nvol = 100
            self.setvol(nvol)
            # print int(status['volume'])
            # print "Volume : %d" % nvol

        result = self.try_cmd(function())
        return result

    def voldown(self, n=5):
        def function():
            """Set player volume down."""
            status = self.status()
            volume = status['volume']
            nvol = int(volume) - n
            if nvol < 0:
                nvol = 0
            self.setvol(nvol)
            # print int(status['volume'])
            # print "Volume : %d" % nvol

        result = self.try_cmd(function())
        return result

        def is_playing(self):
            def function():
                """get player status."""
                status_check = self.status()
                if status_check['state'] == 'stop':
                    return False
                else:
                    return True

            result = self.try_cmd(function())
            return result

