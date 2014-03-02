LeftFeet
========

LeftFeet is a Rhythmbox plugin that generates a playlist from the library. It
is designed specifically for a ballroom/Latin dancing society, but could be
adapted to other purposes.

Installation
------------
Simply copy the entire directory tree to the Rhythmbox plugins directory. For
a local user on a UNIX-like system, this is ~/.local/share/rhythmbox/plugins.

Configuration
-------------
The set of genres is hard-coded into
[leftfeet/lf_site.py](leftfeet/lf_site.py). To adapt LeftFeet to your music
library and requirements, copy this file to the user data directory (for example,
~/.local/share/rhythmbox) and edit it.

Usage
-----
After installing the plugin and activating it within Rhythmbox, an extra
*Generate playlist* item appears on the *Tools* menu. When you select it, a
window appears with a slider for each genre. Adjust the sliders to specify the
relative frequency of each genre, then click *OK* to generate the playlist.

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
