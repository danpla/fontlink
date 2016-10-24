
from gettext import gettext as _

from gi.repository import Gtk, Gdk, GLib

from .settings import settings
from . import app_info
from . import font_lib


class MainWindow(Gtk.ApplicationWindow):

    _DND_URI = 0
    _DND_LIST = [Gtk.TargetEntry.new('text/uri-list', 0, _DND_URI)]

    def __init__(self, app):
        super().__init__(
            application=app,
            title=app_info.TITLE,
            default_width=500,
            default_height=250
            )

        self._maximized = False

        self.drag_dest_set(
            Gtk.DestDefaults.ALL, self._DND_LIST, Gdk.DragAction.COPY)

        grid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)
        self.add(grid)

        grid.add(self._create_menubar())

        self._library = font_lib.FontLib()
        grid.add(self._library)

        grid.show_all()

    def _create_menubar(self):
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)

        menubar = Gtk.MenuBar()

        file_menu = Gtk.Menu()
        mi_file = Gtk.MenuItem(
            label=_('_File'),
            use_underline=True,
            submenu=file_menu
            )
        menubar.append(mi_file)

        mi_quit = Gtk.MenuItem(
            label=_('Quit'),
            action_name='app.quit')
        key, mod = Gtk.accelerator_parse('<Control>Q')
        mi_quit.add_accelerator(
            'activate', accel_group, key, mod, Gtk.AccelFlags.VISIBLE)
        file_menu.append(mi_quit)

        help_menu = Gtk.Menu()
        mi_help = Gtk.MenuItem(
            label=_('_Help'),
            use_underline=True,
            submenu=help_menu
            )
        menubar.append(mi_help)

        mi_about = Gtk.MenuItem(
            label=_('About'),
            action_name='app.about')
        help_menu.append(mi_about)

        return menubar

    def do_drag_data_received(self, context, x, y, selection, target, time):
        if target == self._DND_URI:
            self._library.add_fonts(
                (GLib.filename_from_uri(uri)[0] for uri in
                 selection.get_uris() if uri.startswith('file://')))
        context.finish(True, False, time)

    def do_window_state_event(self, event):
        if event.changed_mask & Gdk.WindowState.MAXIMIZED:
            self._maximized = bool(
                event.new_window_state & Gdk.WindowState.MAXIMIZED)
        return Gtk.ApplicationWindow.do_window_state_event(self, event)

    def do_delete_event(self, event):
        self.save_state()
        return Gdk.EVENT_PROPAGATE

    def save_state(self):
        self._library.save_state()

        settings['window_maximized'] = self._maximized
        settings['window_x'], settings['window_y'] = self.get_position()
        settings['window_width'], settings['window_height'] = self.get_size()

    def load_state(self):
        try:
            if settings['window_maximized']:
                self.maximize()
            else:
                self.move(settings['window_x'], settings['window_y'])
                self.resize(
                    settings['window_width'], settings['window_height'])
        except (KeyError, TypeError):
            pass

        self._library.load_state()
