
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

        self._window = window

        menu = Gtk.Menu()
        self._indicator.set_menu(menu)
        menu.attach_to_widget(self._window)

        mi_visible = Gtk.CheckMenuItem(
            label=_('Show FontLink'))
        mi_visible.set_active(self._window.get_visible())
        self._window.connect(
            'hide', lambda w: mi_visible.set_active(False))
        self._window.connect(
            'show', lambda w: mi_visible.set_active(True))
        mi_visible.connect('toggled', self._on_toggle_visibility)
        menu.append(mi_visible)

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

    def _on_toggle_visibility(self, menu_item):
        if menu_item.get_active():
            self._window.deiconify()
            self._window.present()
        else:
            self._window.hide()
