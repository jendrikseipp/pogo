# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
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

import media, os.path


def isSupported(file):
    """ Return True if the file has a supported format """
    return file.lower()[-4:] == '.m3u'


def save(files, playlist):
    """ Create a playlist with the given files """
    output = open(playlist, 'w')
    output.writelines('\n'.join(files))
    output.close()


def load(playlist):
    """ Return the list of files loaded from the given playlist """
    if not os.path.isfile(playlist):
        return []

    input = open(playlist)
    files = [line for line in [line.strip() for line in input] if len(line) != 0 and line[0] != '#']
    input.close()

    path = os.path.dirname(playlist)
    for i, file in enumerate(files):
        if not os.path.isabs(file):
            files[i] = os.path.join(path, file.replace('\\', '/'))

    return [file for file in files if os.path.isfile(file) and media.isSupported(file)]
