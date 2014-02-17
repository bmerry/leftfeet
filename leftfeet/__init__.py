from gi.repository import GObject, Gio, Gtk, RB, Peas
import random
import gettext
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

    def generate(self):
        shell = self.object
        songs = self.get_songs(shell)
        freqs = {g: self.adjustments[g].get_value() for g in genres.genres}
        # TODO: make the number of songs a parameter
        sequence = generator.generate_sequence(50, freqs)
        for g in sequence:
            if g in songs and songs[g]:
                entry = random.choice(songs[g])
                shell.props.queue_source.add_entry(entry, -1)
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
            table.attach(Gtk.Label(_(g.name)), 0, 1, i, i + 1, 0)
            adj = Gtk.Adjustment(g.default_freq, 0.0, 100.0, 1.0, 10.0)
            scale = Gtk.HScale()
            scale.set_adjustment(adj)
            scale.set_value_pos(Gtk.PositionType.LEFT)
            table.attach(scale, 1, 2, i, i + 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL)
            self.adjustments[g] = adj
        self.window.get_content_area().add(table)
        self.window.set_default_size(500, 1)
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

    def do_deactivate(self):
        shell = self.object
        app = shell.props.application

        app.remove_plugin_menu_item('tools', 'leftfeet-generate')
        app.remove_action('leftfeet-generate')
        self.destroy_window()
