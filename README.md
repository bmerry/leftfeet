LeftFeet
========

LeftFeet is a Rhythmbox plugin that generates a play queue from the library. It
is designed specifically for a ballroom/Latin dancing society, but could be
adapted to other purposes. Unlike a simple random generator, it tries to spread
out genres that are in some way similar according to site-specific criteria.

Installation
------------
Simply copy the entire directory tree to a subdirectory within the Rhythmbox
plugins directory. For a local user on a UNIX-like system, this is
~/.local/share/rhythmbox/plugins. One can of course also git clone the
repository directly to where it will be used.

If you are using Rhythmbox 2, you must edit
[leftfeet.plugin](leftfeet.plugin) to change the line `Loader=python3` to
`Loader=python`.

Configuration
-------------
The set of genres is hard-coded into
[leftfeet/lf_site.py](leftfeet/lf_site.py). To adapt LeftFeet to your music
library and requirements, copy this file to the user data directory (for example,
~/.local/share/rhythmbox) and edit it.

Usage
-----
After installing the plugin and activating it within Rhythmbox, an extra
*Generate play queue* item appears on the *Tools* menu. When you select it, a
window appears with a slider for each genre. Adjust the sliders to specify the
relative frequency of each genre, then click *OK* to generate the play queue.
You can also change the length of time for the generated queue.

## Tips ##
- The existing queue is not replaced. Instead, new songs are appended to the
  queue. If you want to replace the queue, clear it first.
- Any existing songs in the play queue are taken into account when deciding the
  order of new songs. Thus, one can hand-pick a few songs to start with before
  adding more with this plugin, and the first generated songs will fit in. This
  should give better results than first generating a queue and then adding
  songs at the front.
- For best results, don't set the duration too low, as then the ratios won't be
  matched. For example, if you select a mix with 5% Tango but generate only 10
  songs, there will be no Tango at all, not matter how often you add another 10
  songs.

License
-------
Copyright © 2014 Bruce Merry

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Additionally, [leftfeet/lf_site.py](leftfeet/lf_site.py) is made available
under an MIT-style license. Refer to the file itself for the details.
