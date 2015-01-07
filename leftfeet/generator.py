#!/usr/bin/env python

# LeftFeet: generates a Rhythmbox play queue for social dancing
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
list as it grows.

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
list. When selecting a genre or a position, ties are broken randomly,
which gives the list some random variation.

Songs may also be classified as having multiple genres. When picking the next
song, a single genre is chosen, and this single genre is used in evaluating
frequency targets. However, the scoring function takes the maximum energy over
all pairings.
'''

import random

WINDOW = 10
# Scaling weights: inverses, but integral to avoid floating-point issues
weights = [0] + [2520 // i for i in range(1, WINDOW + 1)]

def pick_smallest(kv):
    '''
    In a list of key, value pairs, finds the one with the smallest value and
    returns the key. Ties are broken uniformly at random. If `kv` is empty,
    returns `None`.
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

def repulsion(songs1, songs2, repel):
    '''
    Measures un-weighted repulsion force between two items.
    :param list songs1: genres for first song
    :param list songs2: genres for second song
    :param dict repel: table of repulsion forces
    '''
    ans = 0
    for g1 in songs1:
        for g2 in songs2:
            ans = max(ans, repel[(g1, g2)])
    return ans

def score_single(sequence, repel, pos):
    '''
    Computes the portion of the heuristic due to a single item.

    :param list sequence: list of genres for each song in list
    :param dict repel: table of repulsion forces
    :param int pos: position of item to evaluate
    '''
    ans = 0
    for i in range(max(0, pos - WINDOW), pos):
        ans += repulsion(sequence[i], sequence[pos], repel) * weights[pos - i]
    for i in range(pos + 1, min(pos + WINDOW + 1, len(sequence))):
        ans += repulsion(sequence[pos], sequence[i], repel) * weights[i - pos]
    return ans

def score_pair(sequence, repel, pos):
    '''
    Computes the portion of the heuristic due to two adjacent elements.
    '''
    ans = -(repulsion(sequence[pos], sequence[pos + 1], repel) * weights[1]) # Inclusion-exclusion
    ans += score_single(sequence, repel, pos)
    ans += score_single(sequence, repel, pos + 1)
    return ans

def score(sequence, repel):
    '''
    Computes score for the entire sequence. It is not used, but is retained
    for debugging purposes.
    '''
    ans = 0
    for i in range(1, len(sequence)):
        for j in range(max(0, i - WINDOW), i):
            ans += repulsion(sequence[j], sequence[i], repel) * weights[i - j]
    return ans

def next_genre(N, seen, freqs):
    target = {}
    for g in freqs:
        target[g] = seen.get(g, 0) - (N + 1) * freqs[g]
    return pick_smallest(target.items())

def generate_songs(freqs, repel, duration, factory, prefix = []):
    '''
    Generate a sequence of a given length. Each element is one of the genres,
    and `freqs` gives the relative frequency of each genre. The frequencies
    must all be non-negative real numbers, and their sum must be positive.

    Durations are in arbitrary time units, but seconds are recommended.

    :param freqs: a map from all genres to the relative frequency
    :param repel: map from pairs of genres to a cost for placing them adjacent
    :param numeric duration: desired total time of the list
    :param factory: an object that implements the following methods

        .. py:function:: get(genre):

           Return a song of the given genre. It may return `None` if there are
           no more songs of that genre.

        .. py:function:: get_duration(song):

           Return the duration of a song previously returned by :py:func:`get`.

        .. py::function:: get_genres(song):

           Return the genres corresponding to a song returned by :py:func:`get`.

    :param prefix: sequence of songs already in the play queue

    :raise ValueError: if the sum of frequencies is not positive
    '''

    freqs = dict(freqs) # Make a copy to avoid modifying the caller's copy
    # Normalize the frequencies to sum to 1
    tfreq = sum(freqs.values())
    if tfreq <= 0.0:
        raise ValueError('Must have at least one non-zero frequency')
    for g in freqs.keys():
        freqs[g] /= tfreq
    seen = {g: 0 for g in freqs}

    sequence = [factory.get_genres(x) for x in prefix]
    prefix_len = len(sequence)
    songs = []
    current_duration = 0
    while current_duration < duration and freqs:
        g = next_genre(len(sequence), seen, freqs)
        song = factory.get(g)
        if song is None:
            # Exhausted that genre
            del freqs[g]
            continue
        seen[g] += 1

        # g is a list from here on
        g = factory.get_genres(song)
        sequence.insert(prefix_len, g) # Insert right after the prefix
        cur_score = 0   # Was score(sequence, repel), but only deltas matter
        scores = [cur_score]
        for i in range(prefix_len, len(sequence) - 1):
            # Subtract old relative values
            cur_score -= score_pair(sequence, repel, i)
            # Swap new item along one
            sequence[i], sequence[i + 1] = sequence[i + 1], sequence[i]
            # Add new relative values
            cur_score += score_pair(sequence, repel, i)
            scores.append(cur_score)
        sequence.pop() # Remove the temporarily added new genre

        place = pick_smallest(enumerate(scores))
        sequence.insert(place + prefix_len, g)
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
    It presents songs simply as a wrapper around the genre object.
    '''

    def get(self, genre):
        return TrivialSong(genre)

    def get_duration(self, song):
        return 1

    def get_genres(self, song):
        return [song.genre]

if __name__ == '__main__':
    import lf_site
    import argparse
    from collections import Counter

    parser = argparse.ArgumentParser()
    parser.add_argument('-N', type=int, default=40, help='number of songs to generate')
    parser.add_argument('--stats', action='store_true', help='report stats instead of play queue')
    args = parser.parse_args()

    freqs = {}
    rs = random.Random()
    rs.seed(1)
    for g in lf_site.genres:
        freqs[g] = rs.uniform(0.1, 1.0)
    songs = generate_songs(freqs, lf_site.repel, args.N, TrivialFactory())
    if args.stats:
        actual = Counter()
        freq_total = sum(freqs.values())
        for g in songs:
            actual[g.genre] += 1
        for g in lf_site.genres:
            expected = args.N * freqs[g] / freq_total
            print("{}: {} / {:.2f}".format(g, actual[g], expected))
    else:
        for g in songs:
            print(g.genre.name)

__all__ = ['generate_songs']
