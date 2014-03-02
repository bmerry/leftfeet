#!/usr/bin/env python

# LeftFeet: generates a Rhythmbox playlist for social dancing
# Copyright (C) 2014  Bruce Merry <bmerry@users.sourceforge.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, print_function

'''
Contains the logic to generate a list of genre choices, given the desired
frequency of each genre. It does not deal with choosing a song from each
genre. It is also completely independent of Rhythmbox, and can be used
from the command line.

The algorithm used is slightly odd. Rather than generating a list sequentially,
appending each new choice to the end, songs are inserted into the middle of the
list as it grows. In the description, however, we will refer to "songs" to
mean specific instances of a genre rather than the genre itself.

Firstly, there is scoring function for a sequence, based on the way electric
charges work. Each pair of songs has an associated energy, which depends on
their genres and is divided by the distance between them. To avoid too much
action at a distance (which also hurts performance), songs further than
WINDOW apart do not contribute to energy. Typically the forces are set up so
that songs of the same (or very similar) genres repel each other, causing them
to be evenly spread out rather than clumped together.

To generate the list, songs are generated one at a time and inserted. The next
song is the one that is further behind the expected number of plays based on
its desired frequency. The frequency goals are thus met exactly (to the extent
possibly with rounding) rather than arising stochastically. The new song is
then inserted into the position that minimises the energy of the resulting
playlist. When selecting a genre or a position, ties are broken randomly,
which gives the playlist some random variation.
'''

import random

WINDOW = 10

def pick_smallest(kv):
    '''
    In a list of key, value pairs, finds the one with the smallest value and
    returns the key. Ties are broken uniformly at random.
    '''
    nbest = 0
    best_key = None
    best_value = None
    for (key, value) in kv:
        if nbest == 0 or value < best_value:
            best_key = key
            best_value = value
            nbest = 1
        elif value == best_value:
            if random.randint(0, nbest) == 0:
                best_key = key
            nbest += 1
    return best_key

def score(sequence, repel):
    ans = 0
    for i in range(1, len(sequence)):
        for j in range(max(0, i - WINDOW), i):
            ans += repel[(sequence[j], sequence[i])] / (i - j)
    return ans

def next_genre(sequence, freqs):
    target = {}
    for g in freqs.keys():
        target[g] = (len(sequence) + 1) * -freqs[g]
    for s in sequence:
        target[s] += 1
    return pick_smallest(target.items())

def generate_songs(freqs, repel, duration, factory):
    '''
    Generate a sequence of a given length. Each element is one of the genres,
    and `freqs` gives the relative frequency of each genre. The frequencies
    must all be non-negative real numbers, and their sum must be positive.

    Durations are in arbitrary time units, but seconds are recommended.

    :param freqs: a map from all genres to the relative frequency
    :param repel: map from pairs of genres to a cost for placing them adjacent
    :param numeric duration: desired total time of the playlist
    :param factory: an object that implements the following methods

        .. py:function:: get(genre):

           Return a song of the given genre.

        .. py:function:: get_duration(song):

           Return the duration of a song previously returned by :py:func:`get`.

        .. py::function:: get_genres(song):

           Return the genres corresponding to a song returned by :py:func:`get`.

    :raise ValueError: if the sum of frequencies is not positive
    '''

    freqs = dict(freqs) # Make a copy to avoid modifying the caller's copy
    # Normalize the frequencies to sum to 1
    tfreq = sum(freqs.values())
    if tfreq <= 0.0:
        raise ValueError('Must have at least one non-zero frequency')
    for g in freqs.keys():
        freqs[g] /= tfreq

    sequence = []
    songs = []
    current_duration = 0
    while current_duration < duration:
        g = next_genre(sequence, freqs)
        song = factory.get(g)
        scores = []
        for i in range(len(sequence) + 1):
            sequence.insert(i, g)
            scores.append((i, score(sequence, repel)))
            assert sequence[i] == g
            del sequence[i]
        place = pick_smallest(scores)
        sequence.insert(place, g)
        songs.insert(place, song)
        current_duration += factory.get_duration(song)
    return songs

class TrivialSong(object):
    '''
    Trivial implementation of a song, which just stores its genre.
    '''

    def __init__(self, genre):
        self.genre = genre

class TrivialFactory(object):
    '''
    Trivial implementation of the factory concept for :py:func:`generate_songs`.
    It presents songs simple as a wrapper around the genre object
    '''

    def get(self, genre):
        return TrivialSong(genre)

    def get_duration(self, song):
        return 1

    def get_genres(self, song):
        return [song.genre]

if __name__ == '__main__':
    import lf_site

    freqs = {}
    for g in lf_site.genres:
        freqs[g] = random.uniform(0.8, 1.0)
    songs = generate_songs(freqs, lf_site.repel, 50, TrivialFactory())
    for g in songs:
        print(g.genre.name)
