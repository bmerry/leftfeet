#!/usr/bin/env python

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
'''

OPEN = -1
BEGINNER = 0
INTERMEDIATE = 1
ADVANCED = 2

BALLROOM = 0
LATIN = 1
OTHER = 2

class Genre(object):
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
    Genre('viennese waltz', OPEN, BALLROOM, 1),
    Genre('argentine tango', OPEN, OTHER)
]

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
