#!/usr/bin/env python

# LeftFeet: generates a Rhythmbox playlist for social dancing
# Copyright (C) 2014  Bruce Merry <bmerry@users.sourceforge.net>
#
# This file (and ONLY this file) is distributed under the following terms, in
# addition to the terms governing the software as a whole.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Contains site-local configuration of the available genres.

.. data:: genres

  The available genres

.. data:: repel

  A dictionary indexed by pairs of genres (for all pairs), with
  values being penalty scores for putting the genres close together

.. todo:: Resolve the following questions

  - Should Tango and Argentine Tango be classified separately?
  - Should Slow Fox be split out?
  - Should Viennese Waltz be classed as open?
  - Should Samba and Salsa be classed as similar
  - Should line dances be handled here at all?
  - Any other genres (Paso Doble?)
  - Are there special rules for the start (beginner-friendly?) and end (waltz?)
  - How should songs be picked within a genre (time since last use, star ratings)?
  - How should multi-genre songs be handled?
  - Should low-rated songs be picked randomly (but less often), or just not at all?
  - How many entries should be made? Specify a count or duration?
  - How should frequencies be set? Per genre or at a higher level?
  - What settings should be presented in the plugin? Should they pop up on use or just be plugin settings?
'''

OPEN = -1
BEGINNER = 0
INTERMEDIATE = 1
ADVANCED = 2

BALLROOM = 0
LATIN = 1
OTHER = 2

class Genre(object):
    '''
    Encapsulates a genre that the generator may produce.
    '''
    def __init__(self, name, level, group, energy = 0):
        self.name = name
        self.level = level
        self.group = group
        self.energy = energy
        self.default_freq = 20.0

    def __str__(self):
        return self.name

genres = [
    Genre('foxtrot', BEGINNER, BALLROOM),
    Genre('waltz', BEGINNER, BALLROOM),
    Genre('quickstep', INTERMEDIATE, BALLROOM, 1),
    Genre('tango', ADVANCED, BALLROOM),
    Genre('cha-cha', BEGINNER, LATIN),
    Genre('jive', BEGINNER, LATIN, 1),
    Genre('rumba', INTERMEDIATE, LATIN),
    Genre('samba', ADVANCED, LATIN),
    Genre('boogie', OPEN, OTHER),
    Genre('sokkie', OPEN, OTHER, 1),
    Genre('salsa', OPEN, LATIN),
    Genre('viennese waltz', OPEN, BALLROOM, 1)
]

genre_aliases = {
    'foxtrot, slow': 'foxtrot'
}

repel = {}

for i in genres:
    for j in genres:
        rep = 0
        if i == j:
            # Really don't want two of the same genre in a row
            rep += 20
        elif i.name.endswith(j.name) or j.name.endswith(i.name):
            # Tangos and Waltzes are also similar
            rep += 10

        # Avoid too many exhausting dances together
        rep += i.energy * j.energy
        # Avoid clumping all the advanced dances or all dances of one type together
        rep += 5 - abs(i.level - j.level)
        if i.group == j.group:
            rep += 1
        repel[(i, j)] = rep

def get_genre(entry):
    '''
    Map an entry to its genre object

    :returns: The matching genre, or `None` to skip the entry
    :rtype: :py:class:`Genre`
    '''
    from gi.repository import RB

    name = entry.get_string(RB.RhythmDBPropType.GENRE)
    name = genre_aliases.get(name, name)
    for genre in genres:
        if name == genre.name:
            return genre

def valid_song(entry, now):
    '''
    Determines whether this song should be a candidate. In theory
    this should rather be done by using a RhythmDB query (much faster,
    since it avoids reflecting everything back and forth through Python,
    and may even be indexed), but several hours of attempting to use
    the query interface produced nothing but frustration.
    '''
    from gi.repository import RB

    rating = entry.get_double(RB.RhythmDBPropType.RATING)
    if rating < 4:
        return False
    last_played = entry.get_ulong(RB.RhythmDBPropType.LAST_PLAYED)
    if last_played > now - 43200:   # Last 12 hours
        return False
    return True

__all__ = ['genres', 'repel', 'get_genre', 'valid_song']
