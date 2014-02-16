#!/usr/bin/env python
from __future__ import division
import random

'''
Questions:
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

OPEN = -1
BEGINNER = 0
INTERMEDIATE = 1
ADVANCED = 2

BALLROOM = 0
LATIN = 1
OTHER = 2

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

class Genre(object):
    def __init__(self, name, level, group, energy = 0):
        self.name = name
        self.level = level
        self.group = group
        self.energy = energy
        self.freq = 0

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
    Genre('viennese waltz', OPEN, BALLROOM, 1),
    Genre('argentine tango', OPEN, OTHER)
]
tfreq = 0.0
for g in genres:
    g.freq = random.uniform(0.8, 1.0)
    tfreq += g.freq
for g in genres:
    g.freq /= tfreq

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
            rep += 3
        repel[(i, j)] = rep

def score(sequence):
    ans = 0
    for i in range(1, len(sequence)):
        for j in range(max(0, i - WINDOW), i):
            dist2 = float(i - j)**2
            ans += repel[(sequence[j], sequence[i])] / dist2
    return ans

def next_genre(sequence):
    target = {}
    for g in genres:
        target[g] = (len(sequence) + 1) * -g.freq
    for s in sequence:
        target[s] += 1
    return pick_smallest(target.items())

sequence = []
for i in range(50):
    g = next_genre(sequence)
    scores = []
    for i in range(len(sequence) + 1):
        sequence.insert(i, g)
        scores.append((i, score(sequence)))
        assert sequence[i] == g
        del sequence[i]
    place = pick_smallest(scores)
    sequence.insert(place, g)

for g in sequence:
    print(g)
