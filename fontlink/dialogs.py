
from gettext import gettext as _
import os

from gi.repository import Gtk

from . import common
from . import app_info
from .settings import settings


def confirmation(parent, message, ok_text):
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        message_type=Gtk.MessageType.QUESTION,
        text=message,
        )
    dialog.add_buttons(
        _('_Cancel'), Gtk.ResponseType.CANCEL,
        ok_text, Gtk.ResponseType.OK,
        )
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def about(parent):
    dialog = Gtk.AboutDialog(
        program_name=app_info.TITLE,
        logo_icon_name=app_info.ICON,
        version=app_info.VERSION,
        comments=_('Install fonts temporarily'),
        website=app_info.WEBSITE,
        website_label=app_info.WEBSITE,
        copyright=app_info.COPYRIGHT,
        license=app_info.LICENSE,

        transient_for=parent,
        destroy_with_parent=True
        )

    dialog.run()
    dialog.destroy()


def open_fonts(parent):
    dialog = Gtk.FileChooserDialog(
        title=_('Choose fonts'),
        transient_for=parent,
        action=Gtk.FileChooserAction.OPEN,
        select_multiple=True,
        )
    dialog.add_buttons(
        _('_Cancel'), Gtk.ResponseType.CANCEL,
         _('_Open'), Gtk.ResponseType.OK,
        )

    font_filter = Gtk.FileFilter()
    font_filter.set_name(_('Fonts'))
    for pattern in common.FONT_SEARCH_PATTERNS:
        font_filter.add_pattern(pattern)
    dialog.add_filter(font_filter)

    path = settings.get('last_dir')
    if not isinstance(path, str):
        path = os.path.expanduser('~')
    dialog.set_current_folder(path)

    if dialog.run() == Gtk.ResponseType.OK:
        font_paths = dialog.get_filenames()
        settings['last_dir'] = dialog.get_current_folder()
    else:
        font_paths = []
    dialog.destroy()

    return font_paths
