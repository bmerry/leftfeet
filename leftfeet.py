from gi.repository import GObject, Gio, RB, Peas

import gettext
gettext.install('rhythmbox', RB.locale_dir())

class DancelistPlugin(GObject.Object, Peas.Activatable):
    object = GObject.property(type = GObject.Object)

    def __init__(self):
        super(DancelistPlugin, self).__init__()

    def generate(self, action, parameter, shell):
        lib = shell.props.library_source.props.base_query_model
        it = lib.get_iter_first()
        entry = lib.iter_to_entry(it)
        while entry:
            print entry.get_string(RB.RhythmDBPropType.TITLE)
            print dir(RB.RhythmDBPropType)
            entry = lib.get_next_from_entry(entry)

    def do_activate(self):
        shell = self.object
        app = shell.props.application

        action = Gio.SimpleAction.new("leftfeet-generate", None)
        action.connect('activate', self.generate, shell)
        app.add_action(action)

        app.add_plugin_menu_item('tools', 'leftfeet-generate',
                Gio.MenuItem.new(label = _("Generate playlist"), detailed_action = 'app.leftfeet-generate'))

    def do_deactivate(self):
        shell = self.object
        app = shell.props.application

        app.remove_plugin_menu_item('tools', 'leftfeet-generate')
        app.remove_action('leftfeet-generate')

