# 1.0.1 (2020-07-19)
* Fix accessing PIL version number.

1.0 "I get a little bit Genghis Khan" (18-07-11)
================================================
* Remove code for playing CDs.
* Use GitHub for issue tracking.
* Test for dead code with Vulture.


0.9.2 "Avant Gardener" (17-03-03)
=================================
* Fix adding tracks from left pane to playlist (resolves #1).


0.9.1 "Don't Let Love Go By" (17-02-26)
=======================================
* Add AppData file (lp:1321813).
* Fix two regressions (lp:1666667, lp:1659048).


0.9 "Who's got the keys to my car?" (17-02-16)
==============================================
* Port from GTK 2 to GTK 3.
* Port from Python 2 to Python 3.


0.8.7 "Brighter than Gold" (16-08-03)
=====================================
* Move code to github.
* Remove unused code.
* Make debian package's dependency on dh-python explicit.
* Include elementary-style icon in repo under pix/pogo-e-48.svg (thanks Felix).


0.8.6 "Ich bin zu jung" (15-09-19)
==================================
* Fix version number.
* Update translations.


0.8.5 "3. Stock" (15-09-18)
===========================
* Don't crash when 'find' or 'locate' are missing.
* Add pyflakes test. Run with "make test".


0.8.4 "Oma gib Handtasche" (15-05-14)
=====================================
* Skip non-existing files during exports.
* Don't crash when clearing the playlist.
* Log system info and library versions for easier debugging.


0.8.3 "Radioactive" (14-07-25)
==============================
* Display filename in notification if track title is unknown.
* Apply fix from decibel: Don't set VBR information for MP3 files (#1202195).
* Apply fix from decibel: Remove obsolete volume handling code.


0.8.2 "Please don't go, I love you so" (13-06-30)
=================================================
* Update the clickable buttons after the tracks have been rearranged (lp:1191891).
* Disable zeitgeist module since its DBus interface causes problems frequently.


0.8.1 "Like anything could happen" (13-01-20)
=============================================
* Support Pillow in addition to PIL.
* Disable zeitgeist module to avoid startup errors on Ubuntu 12.10.


0.8 "You thought you'd set the bar" (2012-09-05)
================================================
* Control pogo from the commandline. The commands play, pause, next, prev and stop are supported. (lp:986164)
* When pogo is started with tracks on the commandline, append the tracks to the old playlist.
* Start playback automatically at startup by calling "pogo play".
* Prevent automatic playback when tracks are given on the commandline with "pogo MyFile.mp3 pause".
* Delete corrupted cover file if a cover cannot be correctly resized.
* Do not try to update missing rows when a search is made quickly after startup.
* Do not change volume level (sets volume to max in Fedora).
* Highlight the parts of the query all at once to fix false highlighting.
* Update translations.


0.7 "It has a melody both happy and sad" (2012-04-27)
=====================================================
* Search in home folder if we haven't found anything in the music directories.
* Do not search in subdirectories if we already search in parent directory.
* Only show filename and at most one parent dir for each file in search results.
* Convert GUI from libglade to gtkbuilder.
* Update translations.


0.6 "I will be a bridge for you" (2012-03-26)
=============================================
* Show search results immediately after they're found for each music directory
* Search in playlist as well and highlight results
* Add Zeitgeist module that logs played albums
* Select last played track at restart (lp:684383)
* Append tracks to playlist asynchronously (lp:662308)
* Update translations


0.5 "Rolling in the deep" (2012-01-12)
======================================
* Export tracks in playlist into a directory (with subdirectories)
* Save playlist periodically to prevent losing it during a shutdown (LP:669132)
* Usability: Select new track when old selected is deleted
* Fix: Playback after pause should show the play icon, not the pause icon
* Fix: Never interrupt playing song when appending new ones (lp:735619)
* Cache music folders repeatedly to speedup searches
* Let user remove music folders that were deleted from the hard disk
* Do not add music folders that have been deleted
* Apply fix from decibel: Skipping track just before the end skips the following track
* Apply fix from decibel: Sort files case-independently
* Apply fix from decibel: Raise the window of the already running instance if there is one
* Apply fix from decibel: Create symbolic links to covers so that external apps can access them
* Log all messages to log file


0.4 "I'm a complicated guy" (2011-03-14)
========================================
* Support for WAV files (LP:684161)
* Export playlist to .m3u format (right-click playlist)
* Show "Open containing folder" in context menu also for seaches
* When caching the files in the music directories do not slow down application
* Save cover size between sessions
* Fix: adding files from command line by removing bash start script
* Fix: Compiz cover display problem
* Fix: Save maximized state
* Fix: Start playback automatically when tracks are appended, but not when inserted
* Fix: Unhighlight not selected tracks always
* Code: Assert copyright with date (LP:692792)
* Code: Use pogo.py as binary directly for installations
* Update translations


0.3.1 "You are a radar detector" (2010-12-26)
=============================================
* When a track is added from nautilus etc. start playback if not already playing
* Show info messages when no music directories have been added
* Stop old search when user clears search field or enters new search phrase
* Add search shortcut (Ctrl-F)
* Do not allow adding root or home directory to music directories
* Translations updated


0.3 "I go hard, I go home" (2010-12-01)
=======================================
* Search for tracks in the music folders (Directories below separator)
* Searching supports * and ? wildcards
* Let users add and hide directories in file browser
* Add "Open containing folder" context menu item
* Make trackslider bigger
* Fix Loading files from commandline (make paths absolute)
* Fix: Save playlist also when files have been added on the commandline
* Fix: With compiz the first cover is only shown after the window is redrawn
* Updated Translations


0.2 "I hold the candle while you dance upon the flame" (2010-10-21)
===================================================================
* Make startup even faster by saving the playlist with its formatting
* Make track drag'n'drop faster by caching the tracks
* MPRIS support: Send DBus messages about play events (code from decibel)
* Do some profiling to improve general speed
* Append files added on commandline (pogo mytrack.mp3 myalbum myothertrack.mp3)
* Append files added from nautilus right-click menu
* Correctly add multiply nested directories
* Activate the Covers and Notifications modules by default
* Hide volume button (Only duplicates functionality of the Sound Indicator)
* Updated Translations


0.1 "Businessmen drink my blood" (2010-10-05)
=============================================
* Initial release
* Fork decibel audio player
* Rebranding
* Restructure interface (use space more efficiently, simplify)
* Write new playlist widget which groups albums
* Show clickable cover in lower right corner
* Make preferences dialog more accessible
* Make track position slider clickable with left mouse clicks
* Highlight all parents when playing a track
* Automatically hide redundant information in track titles
* Remove menubar and statusbar
* Add preferences button
* Highlight dropped rows after drag'n'drop
* Collapse rows when dragging only dirs
* Let slider tooltip display elapsed seconds
* Keep original ratio when scaling covers
* Remove unnecessary code
* Much code refactoring
