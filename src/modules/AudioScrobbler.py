# -*- coding: utf-8 -*-
#
# Author: Ingelrest François (Francois.Ingelrest@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import modules, os.path, tools, traceback

from time      import time
from tools     import consts
from gettext   import gettext as _
from tools.log import logger

MOD_INFO = ('AudioScrobbler', 'AudioScrobbler', _('Keep your Last.fm profile up to date'), [], False, False)

CLI_ID         = 'dbl'
CLI_VER        = '0.4'
MOD_NAME       = MOD_INFO[modules.MODINFO_NAME]
PROTO_VER      = '1.2'
AS_SERVER      = 'post.audioscrobbler.com'
CACHE_FILE     = 'audioscrobbler-cache.txt'
MAX_SUBMISSION = 4


# Session
(
    SESSION_ID,
    NOW_PLAYING_URL,
    SUBMISSION_URL
) = range(3)


# Current track
(
    TRK_STARTED_TIMESTAMP,   # When the track has been started
    TRK_UNPAUSED_TIMESTAMP,  # When the track has been unpaused (if it ever happened)
    TRK_PLAY_TIME,           # The total play time of this track
    TRK_INFO                 # Information about the track
) = range(4)


class AudioScrobbler(modules.ThreadedModule):
    """ This module implements the Audioscrobbler protocol v1.2 (http://www.audioscrobbler.net/development/protocol/) """

    def __init__(self):
        """ Constructor """
        modules.ThreadedModule.__init__(self, (consts.MSG_EVT_NEW_TRACK,  consts.MSG_EVT_APP_QUIT, consts.MSG_EVT_MOD_UNLOADED,
                                               consts.MSG_EVT_MOD_LOADED, consts.MSG_EVT_PAUSED,   consts.MSG_EVT_UNPAUSED,
                                               consts.MSG_EVT_STOPPED,    consts.MSG_EVT_APP_STARTED))


    def init(self):
        """ Initialize this module """
        # Attributes
        self.login          = None
        self.passwd         = None
        self.paused         = False
        self.session        = [None, None, None]
        self.isBanned       = False
        self.currTrack      = None
        self.lastHandshake  = 0
        self.nbHardFailures = 0
        self.handshakeDelay = 0

        # Load cache from the disk
        try:
            input      = open(os.path.join(consts.dirCfg, CACHE_FILE))
            self.cache = [strippedTrack for strippedTrack in [track.strip() for track in input.readlines()] if len(strippedTrack) != 0]
            input.close()
        except:
            self.cache = []


    def saveCache(self):
        """ Save the cache to the disk """
        file   = os.path.join(consts.dirCfg, CACHE_FILE)
        output = open(file, 'w')
        output.writelines('\n'.join(self.cache))
        output.close()


    def addToCache(self):
        """ Add the current track to the cache, if any, and that all conditions are OK """
        if self.currTrack is None: return
        else:                      track = self.currTrack[TRK_INFO]

        if not (track.hasArtist() and track.hasTitle() and track.hasLength()):
            return

        if not (track.getLength() >= 30 and (self.currTrack[TRK_PLAY_TIME] >= 240 or self.currTrack[TRK_PLAY_TIME] >= track.getLength()/2)):
            return

        params = (
                    ( 'a[*]', tools.percentEncode(track.getSafeArtist()) ),
                    ( 't[*]', tools.percentEncode(track.getSafeTitle())  ),
                    ( 'i[*]', str(self.currTrack[TRK_STARTED_TIMESTAMP]) ),
                    ( 'o[*]', 'P'                                        ),
                    ( 'r[*]', ''                                         ),
                    ( 'l[*]', track.getSafeLength()                      ),
                    ( 'b[*]', tools.percentEncode(track.getSafeAlbum())  ),
                    ( 'n[*]', track.getSafeNumber()                      ),
                    ( 'm[*]', track.getSafeMBTrackId()                   )
                 )

        self.cache.append('&'.join(['%s=%s' % (key, val) for (key, val) in params]))


    def getFromCache(self, howMany):
        """ Return the oldest howMany tracks from the cache, replace the star with the correct index """
        if howMany > len(self.cache):
            howMany = len(self.cache)

        return [self.cache[i].replace('[*]', '[%d]' % i) for i in xrange(howMany)]


    def removeFromCache(self, howMany):
        """ Remove the oldest howMany tracks from the cache """
        self.cache[:] = self.cache[howMany:]


    def getCacheSize(self):
        """ Return the number cached tracks """
        return len(self.cache)


    def getAuthInfo(self):
        """ Retrieve the login/password of the user """
        from gui import authentication

        if self.login is None: auth = authentication.getAuthInfo('last.fm', _('your Last.fm account'))
        else:                  auth = authentication.getAuthInfo('last.fm', _('your Last.fm account'), self.login, True)

        if auth is None: self.login, self.passwd = None, None
        else:            self.login, self.passwd = auth


    def handshake(self):
        """ Authenticate the user to the submission servers, return True if OK """
        import hashlib, socket, urllib2

        socket.setdefaulttimeout(consts.socketTimeout)

        now             = int(time())
        self.session[:] = [None, None, None]

        # Postpone or cancel this handshake?
        if self.isBanned or (now - self.lastHandshake) < self.handshakeDelay:
            return False

        # Asking for login information must be done in the GTK main loop, because a dialog box might be displayed if needed
        self.gtkExecute(self.getAuthInfo)
        if self.passwd is None:
            return False

        # Compute the authentication token
        md5Pwd   = hashlib.md5()
        md5Token = hashlib.md5()

        md5Pwd.update(self.passwd)
        md5Token.update('%s%u' % (md5Pwd.hexdigest(), now))

        # Try to forget authentication info ASAP
        token              = md5Token.hexdigest()
        self.passwd        = None
        request            = 'http://%s/?hs=true&p=%s&c=%s&v=%s&u=%s&t=%d&a=%s' % (AS_SERVER, PROTO_VER, CLI_ID, CLI_VER, self.login, now, token)
        self.lastHandshake = now

        try:
            hardFailure = False
            reply       = urllib2.urlopen(request).read().strip().split('\n')

            if reply[0] == 'OK':
                self.session[:]     = reply[1:]
                self.handshakeDelay = 0
                self.nbHardFailures = 0
                logger.info('[%s] Logged into Audioscrobbler server' % MOD_NAME)

            elif reply[0] == 'BANNED':
                logger.error('[%s] This version of %s has been banned from the server' % (MOD_NAME, consts.appName))
                self.isBanned = True

            elif reply[0] == 'BADAUTH':
                logger.error('[%s] Bad authentication information' % MOD_NAME)
                return self.handshake()

            elif reply[0] == 'BADTIME':
                logger.error('[%s] Server reported that the current system time is not correct, please correct it' % MOD_NAME)
                self.isBanned = True

            else:
                hardFailure = True
                logger.error('[%s] Hard failure during handshake' % MOD_NAME)

        except:
            hardFailure = True
            logger.error('[%s] Unable to perform handshake\n\n%s' % (MOD_NAME, traceback.format_exc()))

        if hardFailure:
            if   self.handshakeDelay == 0:     self.handshakeDelay  = 1*60         # Start at 1mn
            elif self.handshakeDelay >= 64*60: self.handshakeDelay  = 120*60       # Max 120mn
            else:                              self.handshakeDelay *= 2            # Double the delay

        self.login = None

        return self.session[SESSION_ID] is not None


    def nowPlayingNotification(self, track, firstTry = True):
        """ The Now-Playing notification is a lightweight mechanism for notifying the Audioscrobbler server that a track has started playing """
        import urllib2

        if (self.session[SESSION_ID] is None and not self.handshake()) or not track.hasArtist() or not track.hasTitle():
            return

        params = (
                    ( 's', self.session[SESSION_ID]                   ),
                    ( 'a', tools.percentEncode(track.getSafeArtist()) ),
                    ( 't', tools.percentEncode(track.getSafeTitle())  ),
                    ( 'b', tools.percentEncode(track.getSafeAlbum())  ),
                    ( 'l', track.getSafeLength()                      ),
                    ( 'n', track.getSafeNumber()                      ),
                    ( 'm', track.getSafeMBTrackId()                   )
                 )

        try:
            data  = '&'.join(['%s=%s' % (key, val) for (key, val) in params])
            reply = urllib2.urlopen(self.session[NOW_PLAYING_URL], data).read().strip().split('\n')

            if reply[0] == 'BADSESSION' and firstTry:
                self.session[:] = [None, None, None]
                self.nowPlayingNotification(track, False)

        except:
            logger.error('[%s] Unable to perform now-playing notification\n\n%s' % (MOD_NAME, traceback.format_exc()))


    def submit(self, firstTry=True):
        """ Submit cached tracks, return True if OK """
        import urllib2

        if (self.session[SESSION_ID] is None and not self.handshake()) or len(self.cache) == 0:
            return False

        try:
            hardFailure  = False
            cachedTracks = self.getFromCache(MAX_SUBMISSION)
            data         = 's=%s&%s' % (self.session[SESSION_ID], '&'.join(cachedTracks))
            reply        = urllib2.urlopen(self.session[SUBMISSION_URL], data).read().strip().split('\n')

            if reply[0] == 'OK':
                self.removeFromCache(len(cachedTracks))
                return True

            elif reply[0] == 'BADSESSION' and firstTry:
                self.session[:] = [None, None, None]
                return self.submit(False)

            else:
                hardFailure = True

        except:
            hardFailure = True
            logger.error('[%s] Unable to perform submission\n\n%s' % (MOD_NAME, traceback.format_exc()))

        if hardFailure:
            if self.nbHardFailures < 2: self.nbHardFailures += 1
            else:                       self.handshake()
        else:
            self.nbHardFailures = 0

        return False


    def onTrackEnded(self, trySubmission):
        """ The playback of the current track has stopped """
        if self.currTrack is not None:
            self.currTrack[TRK_PLAY_TIME] += (int(time()) - self.currTrack[TRK_UNPAUSED_TIMESTAMP])
            self.addToCache()
            self.currTrack = None

            # Try to submit the whole cache?
            if trySubmission:
                submitOk = self.submit()
                while submitOk and len(self.cache) != 0:
                    submitOk = self.submit()


    def onNewTrack(self, track):
        """ A new track has started """
        timestamp = int(time())
        self.onTrackEnded(True)
        self.nowPlayingNotification(track)
        self.currTrack = [timestamp, timestamp, 0, track]


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if msg == consts.MSG_EVT_NEW_TRACK:
            self.onNewTrack(params['track'])

        elif msg == consts.MSG_EVT_STOPPED:
            if self.paused:
                self.currTrack[TRK_UNPAUSED_TIMESTAMP] = int(time())
            self.paused = False
            self.onTrackEnded(True)

        elif msg == consts.MSG_EVT_PAUSED:
            self.currTrack[TRK_PLAY_TIME] += (int(time()) - self.currTrack[TRK_UNPAUSED_TIMESTAMP])
            self.paused = True

        elif msg == consts.MSG_EVT_UNPAUSED:
            self.currTrack[TRK_UNPAUSED_TIMESTAMP] = int(time())
            self.paused = False

        elif msg == consts.MSG_EVT_APP_QUIT or msg == consts.MSG_EVT_MOD_UNLOADED:
            if self.paused:
                self.currTrack[TRK_UNPAUSED_TIMESTAMP] = int(time())
            self.paused = False
            self.onTrackEnded(False)
            self.saveCache()
            if self.getCacheSize() != 0:
                logger.info('[%s] %u track(s) left in cache' % (MOD_NAME, self.getCacheSize()))

        elif msg == consts.MSG_EVT_APP_STARTED or msg == consts.MSG_EVT_MOD_LOADED:
            self.init()
