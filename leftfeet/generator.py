#!/usr/bin/env python
from __future__ import division
import random
import genres

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

def score(sequence):
    ans = 0
    for i in range(1, len(sequence)):
        for j in range(max(0, i - WINDOW), i):
            ans += genres.repel[(sequence[j], sequence[i])] / (i - j)
    return ans

def next_genre(sequence, freqs):
    target = {}
    for g in genres.genres:
        target[g] = (len(sequence) + 1) * -freqs[g]
    for s in sequence:
        target[s] += 1
    return pick_smallest(target.items())

def generate_sequence(freqs):
    tfreq = sum(freqs.values())
    for g in genres.genres:
        freqs[g] /= tfreq

    sequence = []
    for i in range(50):
        g = next_genre(sequence, freqs)
        scores = []
        for i in range(len(sequence) + 1):
            sequence.insert(i, g)
            scores.append((i, score(sequence)))
            assert sequence[i] == g
            del sequence[i]
        place = pick_smallest(scores)
        sequence.insert(place, g)
    return sequence

if __name__ == '__main__':
    freqs = {}
    for g in genres.genres:
        freqs[g] = random.uniform(0.8, 1.0)
    sequence = generate_sequence(freqs)
    for g in sequence:
        print(g)
