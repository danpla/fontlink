
import signal

from gi.repository import Gio, Gtk, GLib

from . import app_info
from .conf import _
from . import dialogs
from . import window
from . import tray
from .settings import settings


class FontLink(Gtk.Application):

    __actions = (
        'about',
        'quit',
    )

    def __init__(self):
        super().__init__(
            application_id='org.gtk.fontlink',
            flags=Gio.ApplicationFlags.FLAGS_NONE)
        GLib.set_application_name(app_info.TITLE)
        GLib.set_prgname(app_info.NAME)

        self.add_main_option_entries([
            self._make_option(
                'version', ord('v'),
                _('Show version number and exit')),
            self._make_option(
                'minimized', ord('m'),
                _('Start minimized to the notification area')),
            ])

        self.window = None
        self.minimized = False
        self.first_activation = True

        GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM, self.quit)

    def _make_option(self, long_name, short_name, description, flags=0,
                     arg=GLib.OptionArg.NONE, arg_data=None,
                     arg_description=None):
        opt = GLib.OptionEntry()
        opt.long_name = long_name
        opt.short_name = short_name
        opt.description = description
        opt.flags = flags
        opt.arg = arg
        opt.arg_data = arg_data
        opt.arg_description = arg_description
        return opt

    def do_handle_local_options(self, options):
        if options.contains('version'):
            print(app_info.TITLE, app_info.VERSION)
            return 0
        self.minimized = options.contains('minimized')

        return -1

    def do_startup(self):
        Gtk.Application.do_startup(self)
        settings.load()

        for name in self.__actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', getattr(self, '_{}_cb'.format(name)))
            self.add_action(action)

        Gtk.Window.set_default_icon_name(app_info.ICON)
        self.window = window.MainWindow(self)
        self.window.load_state()
        if not self.minimized:
            self.window.show()

        self.tray = tray.Tray(self.window)

    def do_activate(self):
        if not self.first_activation and self.window:
            self.window.present()
        self.first_activation = False

    def quit(self):
        self.window.save_state()
        settings.save()
        super().quit()

    # Action callbacks.

    def _about_cb(self, action, parameter):
        dialogs.about(self.window)

    def _quit_cb(self, action, parameter):
        self.quit()
