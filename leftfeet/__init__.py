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

'''
This is the module that interacts with the Rhythmbox plugin API.
'''

from gi.repository import GObject, Gio, Gtk, RB, Peas
import random
import gettext
import anydbm
import time
import sys

import generator
__path__.insert(0, RB.user_data_dir())  # Allows user to override location
import lf_site

gettext.install('rhythmbox', RB.locale_dir())

class SongFactory(object):
    '''
    Provides the factory for :py:func:`generator.generate_songs`.

    :ivar dict songs: list of valid songs for each genre
    :ivar list missing: genres we were asked for but could not provide
    '''
    def __init__(self, shell):
        self.songs = {g: [] for g in lf_site.genres}
        self.missing = []

        lib = shell.props.library_source.props.base_query_model
        it = lib.get_iter_first()
        if it is not None:
            entry = lib.iter_to_entry(it)
            now = time.time() # Cache it for valid_song
            while entry:
                if lf_site.valid_song(entry, now):
                    genre = lf_site.get_genre(entry)
                    if genre is not None:
                        self.songs[genre].append(entry)
                entry = lib.get_next_from_entry(entry)

    def get(self, genre):
        if genre in self.songs and self.songs[genre]:
            entry = random.choice(self.songs[genre])
            # Avoid picking it again
            self.songs[genre].remove(entry)
            return entry
        else:
            self.missing.append(genre)
            return None

    def get_duration(self, entry):
        return entry.get_ulong(RB.RhythmDBPropType.DURATION)

    def get_genres(self, entry):
        return [lf_site.get_genre(entry)]

class ConfigDialog(Gtk.Dialog):
    '''
    Configuration dialog to control frequencies etc.

    :ivar Gtk.Adjustment duration_minutes: adjustment holding the length of time to generate over
    :ivar dict freqs: dictionary mapping :py:class:`leftfeet.genre.Genre` objects to GTK adjustments for relative frequencies
    :ivar settings: settings database
    '''
    def __init__(self, parent, settings):
        Gtk.Dialog.__init__(self,
            title = 'LeftFeet configuration',
            parent = parent,
            flags = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            buttons = [
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            ])

        self.settings = settings
        self.adjustments = {}
        self.duration_minutes = Gtk.Adjustment(240, 0, 720, 1, 10)

        vbox = Gtk.VBox()
        self.get_content_area().add(vbox)

        freq_frame = Gtk.Frame()
        freq_frame.set_label('Relative Frequency')
        vbox.pack_start(freq_frame, False, False, 5)

        table = Gtk.Table(len(lf_site.genres), 2)
        for (i, g) in enumerate(lf_site.genres):
            key = 'freq.' + g.name
            if self.settings.has_key(key):
                freq = float(self.settings[key])
            else:
                freq = g.default_freq

            table.attach(Gtk.Label(_(g.name)), 0, 1, i, i + 1, 0, xpadding = 5, ypadding = 5)
            adj = Gtk.Adjustment(freq, 0.0, 100.0, 1.0, 10.0)
            adj.connect('value-changed', self.freq_changed, g)
            scale = Gtk.HScale()
            scale.set_adjustment(adj)
            scale.set_value_pos(Gtk.PositionType.LEFT)
            table.attach(scale, 1, 2, i, i + 1,
                    Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL,
                    xpadding = 5, ypadding = 5)
            self.adjustments[g] = adj
        freq_frame.add(table)

        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 5)
        hbox.pack_start(Gtk.Label(_('Minutes')), False, False, 5)
        spinner = Gtk.SpinButton()
        spinner.set_adjustment(self.duration_minutes)
        spinner.set_digits(0)
        spinner.set_value(self.duration_minutes.get_value())
        hbox.pack_start(spinner, True, True, 5)

        self.set_default_size(500, -1)
        self.show_all()

    def freq_changed(self, adj, genre):
        '''
        Callback for a change in a frequency slider. This updates the
        configuration database.

        :param Gtk.Adjustment adj: Adjustment for the frequency
        :param genre: Genre that has been updated
        :type genre: :py:class:`leftfeet.genre.Genre`
        '''
        self.settings['freq.' + genre.name] = repr(adj.get_value())

class LeftFeetPlugin(GObject.Object, Peas.Activatable):
    '''
    Plugin class

    :var RB.Shell object: Reference to the Rhythmbox shell
    '''

    object = GObject.property(type = GObject.Object)

    def __init__(self):
        super(LeftFeetPlugin, self).__init__()

    def generate(self, freqs, duration):
        '''
        Generate the list of songs and enqueue them to the playlist.

        .. todo:: More intelligent random choice (consider star ratings etc)
        .. todo:: Avoid picking songs that have been played recently

        :param map freqs: map from genre to relation frequency
        :param int duration: duration to target (seconds)
        :return: `True` if generation was successful, `False` to redisplay the dialog
        '''
        shell = self.object
        factory = SongFactory(shell)
        try:
            songs = generator.generate_songs(freqs, lf_site.repel, duration, factory)
        except ValueError as e:
            message = Gtk.MessageDialog(
                    shell.props.window,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.OK,
                    str(e))
            message.connect('response', lambda w, response: w.destroy())
            message.run()
            return False

        missing_genres = set()
        for song in songs:
            shell.props.queue_source.add_entry(song, -1)
        if factory.missing:
            text = 'Could not find enough songs from the following genre(s):\n'
            for g in factory.missing:
                text += g.name + '\n'
            message = Gtk.MessageDialog(
                    shell.props.window,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
                    Gtk.MessageType.WARNING,
                    Gtk.ButtonsType.OK,
                    text)
            message.connect('response', lambda w, response: w.destroy())
            message.run()
        return True

    def generate_action(self, action, parameter, shell):
        '''
        Display the *Generate playlist* dialog and handle the response.
        '''
        shell = self.object
        dialog = ConfigDialog(shell.props.window, self.settings)

        done = False
        while not done:
            response = dialog.run()
            done = True
            if response == Gtk.ResponseType.OK:
                freqs = {g: dialog.adjustments[g].get_value() for g in lf_site.genres}
                duration = int(dialog.duration_minutes.get_value() * 60)
                if not self.generate(freqs, duration):
                    done = False
        dialog.destroy()

    def do_activate(self):
        '''
        Plugin activation
        '''
        shell = self.object
        app = shell.props.application

        action = Gio.SimpleAction.new("leftfeet-generate", None)
        action.connect('activate', self.generate_action, shell)
        app.add_action(action)

        app.add_plugin_menu_item('tools', 'leftfeet-generate',
                Gio.MenuItem.new(label = _("Generate playlist"), detailed_action = 'app.leftfeet-generate'))

        self.settings = anydbm.open(RB.find_user_data_file('leftfeet.db'), 'c')

    def do_deactivate(self):
        '''
        Plugin deactivation
        '''
        shell = self.object
        app = shell.props.application

        self.settings.close()
        app.remove_plugin_menu_item('tools', 'leftfeet-generate')
        app.remove_action('leftfeet-generate')
