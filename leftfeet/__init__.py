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

from gi.repository import GObject, GLib, Gio, Gtk, RB, Peas
import random
import gettext
import anydbm
import time
import sys

from . import generator
__path__.insert(0, RB.user_data_dir())  # Allows user to override location
from . import lf_site

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
        queue = shell.props.queue_source.props.base_query_model
        now = time.time() # Cache it for valid_entry

        for row in lib:
            entry = row[0]
            # Avoid anything in the play queue
            it = Gtk.TreeIter()
            if not queue.entry_to_iter(entry, it):
                if lf_site.valid_entry(entry, now):
                    genres = lf_site.get_genres(entry)
                    for g in genres:
                        self.songs[g].append(entry)

    def get(self, genre):
        if genre in self.songs and self.songs[genre]:
            entry = random.choice(self.songs[genre])
            # Avoid picking it again (TODO: use an index to speed this up)
            for g in self.get_genres(entry):
                self.songs[g].remove(entry)
            return entry
        else:
            self.missing.append(genre)
            return None

    def get_duration(self, entry):
        return entry.get_ulong(RB.RhythmDBPropType.DURATION)

    def get_genres(self, entry):
        return lf_site.get_genres(entry)

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
            transient_for = parent,
            modal = True,
            destroy_with_parent = True)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.settings = settings
        self.adjustments = {}
        self.duration_minutes = Gtk.Adjustment(
            value = 240, lower = 0, upper = 720, step_increment = 1, page_increment = 10)

        vbox = Gtk.VBox()
        self.get_content_area().add(vbox)

        freq_frame = Gtk.Frame()
        freq_frame.set_label('Relative Frequency')
        vbox.pack_start(freq_frame, False, False, 5)

        grid = Gtk.Grid()
        for (i, g) in enumerate(lf_site.genres):
            key = 'freq.' + g.name
            if key in self.settings:
                freq = float(self.settings[key])
            else:
                freq = g.default_freq

            grid.attach(Gtk.Label(label = _(g.name), margin = 5), 0, i, 1, 1)
            adj = Gtk.Adjustment(
                value = freq,
                lower = 0.0, upper = 100.0,
                step_increment = 1.0, page_increment = 10.0)
            adj.connect('value-changed', self.freq_changed, g)
            scale = Gtk.Scale(
                orientation = Gtk.Orientation.HORIZONTAL,
                value_pos = Gtk.PositionType.LEFT, margin = 5,
                hexpand = True, halign = Gtk.Align.FILL)
            scale.set_adjustment(adj)
            grid.attach(scale, 1, i, 1, 1)
            self.adjustments[g] = adj
        freq_frame.add(grid)

        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 5)
        hbox.pack_start(Gtk.Label(label = _('Minutes')), False, False, 5)
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
        queue = shell.props.queue_source.props.base_query_model
        prefix = [row[0] for row in queue]
        factory = SongFactory(shell)
        try:
            songs = generator.generate_songs(freqs, lf_site.repel, duration, factory, prefix)
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

    @classmethod
    def play_queue_data_func(cls, cell_layout, cell, model, it, data):
        entry = model.get_value(it, 0)

        title = entry.get_string(RB.RhythmDBPropType.TITLE)
        genre = entry.get_string(RB.RhythmDBPropType.GENRE)

        markup = '{title}\n<span size="smaller">{genre}</span>'.format(
            title = GLib.markup_escape_text(title),
            genre = GLib.markup_escape_text(genre))

        cell.props.markup = markup

    def replace_sidebar(self):
        shell = self.object
        queue = shell.props.queue_source
        view = queue.props.sidebar
        treeview = view.get_child()
        column = treeview.get_column(1)

        column.get_cells()[0].set_visible(False)

        # This is just translating what the Rhythmbox C code does
        renderer = Gtk.CellRendererText()
        column.pack_end(renderer, True)
        column.set_cell_data_func(renderer, self.play_queue_data_func)

    def restore_sidebar(self):
        shell = self.object
        queue = shell.props.queue_source
        view = queue.props.sidebar
        treeview = view.get_child()
        column = treeview.get_column(1)

        cells = column.get_cells()
        renderer = cells[1]
        column.clear_attributes(renderer)
        column.set_cell_data_func(renderer, None)
        renderer.set_visible(False)
        cells[0].set_visible(True)
        print(len(column.get_cells()))

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

        # self.replace_sidebar()

    def do_deactivate(self):
        '''
        Plugin deactivation
        '''
        shell = self.object
        app = shell.props.application

        self.settings.close()
        # self.restore_sidebar()
        app.remove_plugin_menu_item('tools', 'leftfeet-generate')
        app.remove_action('leftfeet-generate')
