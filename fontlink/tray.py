
from gi.repository import Gtk, AppIndicator3

from . import app_info
from . import conf
from .conf import _


class Tray:
    def __init__(self, window):
        self._indicator = AppIndicator3.Indicator.new(
            app_info.NAME, app_info.ICON,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS)

        if conf.ICON_DIR:
            self._indicator.set_icon_theme_path(conf.ICON_DIR)
        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()
        menu.attach_to_widget(window)

        mi_visibility = Gtk.CheckMenuItem(
            label=_('Show FontLink'),
            action_name='win.minimized')
        menu.append(mi_visibility)

        menu.append(Gtk.SeparatorMenuItem())

        mi_about = Gtk.MenuItem(
            label=_('About'),
            action_name='app.about')
        menu.append(mi_about)

        mi_quit = Gtk.MenuItem(
            label=_('Quit'),
            action_name='app.quit')
        menu.append(mi_quit)

        menu.show_all()

        self._indicator.set_menu(menu)
