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

from gi.repository import GObject, Gio, Gtk, RB, Peas
import random
import gettext
import anydbm

import genres
import generator

gettext.install('rhythmbox', RB.locale_dir())

class LeftFeetPlugin(GObject.Object, Peas.Activatable):
    object = GObject.property(type = GObject.Object)

    def __init__(self):
        super(LeftFeetPlugin, self).__init__()

    def destroy_window(self):
        if self.window is not None:
            self.window.destroy()

    @staticmethod
    def get_genre(entry):
        name = entry.get_string(RB.RhythmDBPropType.GENRE)
        for genre in genres.genres:
            if name == genre.name:
                return genre

    def get_songs(self, shell):
        '''
        Returns a dictionary of lists, indexed by genre object.
        '''
        lib = shell.props.library_source.props.base_query_model
        by_genre = {}

        it = lib.get_iter_first()
        if it is None:
            return by_genre # Empty library
        entry = lib.iter_to_entry(it)
        for g in genres.genres:
            by_genre[g] = []
        while entry:
            genre = self.get_genre(entry)
            if genre is not None:
                by_genre[genre].append(entry)
            entry = lib.get_next_from_entry(entry)
        return by_genre

    def freq_changed(self, adj, genre):
        self.settings['freq.' + genre.name] = repr(adj.get_value())

    def generate(self):
        '''
        Generate the list of songs and enqueue them to the playlist.

        @todo More intelligent random choice (consider star ratings etc)
        @todo Avoid picking songs that have been played recently
        @todo Take a parameter for the number of songs to generate
        '''
        shell = self.object
        songs = self.get_songs(shell)
        freqs = {g: self.adjustments[g].get_value() for g in genres.genres}
        # TODO: make the number of songs a parameter
        sequence = generator.generate_sequence(50, freqs)
        for g in sequence:
            if g in songs and songs[g]:
                entry = random.choice(songs[g])
                shell.props.queue_source.add_entry(entry, -1)
                # Avoid picking it again
                songs[g].remove(entry)

    def generate_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            self.generate()
        self.adjustments = {}
        dialog.destroy()

    def generate_action(self, action, parameter, shell):
        self.window = Gtk.Dialog(
                title = 'LeftFeet configuration',
                parent = shell.props.window,
                flags = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                buttons = [
                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_OK, Gtk.ResponseType.OK
                ])
        table = Gtk.Table(len(genres.genres), 2)
        self.adjustments = {}
        for (i, g) in enumerate(genres.genres):
            key = 'freq.' + g.name
            if self.settings.has_key(key):
                freq = float(self.settings[key])
            else:
                freq = g.default_freq

            table.attach(Gtk.Label(_(g.name)), 0, 1, i, i + 1, 0)
            adj = Gtk.Adjustment(freq, 0.0, 100.0, 1.0, 10.0)
            adj.connect('value-changed', self.freq_changed, g)
            scale = Gtk.HScale()
            scale.set_adjustment(adj)
            scale.set_value_pos(Gtk.PositionType.LEFT)
            table.attach(scale, 1, 2, i, i + 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL)
            self.adjustments[g] = adj
        self.window.get_content_area().add(table)
        self.window.set_default_size(500, -1)
        self.window.show_all()
        self.window.connect('response', self.generate_response)
        self.window.run()

    def do_activate(self):
        shell = self.object
        app = shell.props.application

        action = Gio.SimpleAction.new("leftfeet-generate", None)
        action.connect('activate', self.generate_action, shell)
        app.add_action(action)

        app.add_plugin_menu_item('tools', 'leftfeet-generate',
                Gio.MenuItem.new(label = _("Generate playlist"), detailed_action = 'app.leftfeet-generate'))

        self.settings = anydbm.open(RB.find_user_data_file('leftfeet.db'), 'c')

    def do_deactivate(self):
        shell = self.object
        app = shell.props.application

        self.settings.close()
        app.remove_plugin_menu_item('tools', 'leftfeet-generate')
        app.remove_action('leftfeet-generate')
        self.destroy_window()
