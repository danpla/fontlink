
from gettext import gettext as _

from gi.repository import Gtk

from . import common
from . import app_info
from . import utils


def yesno(message, parent=None):
    dialog = Gtk.MessageDialog(
        parent, 0, Gtk.MessageType.QUESTION,
        Gtk.ButtonsType.YES_NO, message)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.YES


def about(parent=None):
    dialog = Gtk.AboutDialog(
        parent=parent,
        program_name=app_info.TITLE,
        logo_icon_name=app_info.ICON,
        version=app_info.VERSION,
        comments=_('Install fonts temporarily'),
        website=app_info.WEBSITE,
        website_label=app_info.WEBSITE,
        copyright=app_info.COPYRIGHT,
        license=app_info.LICENSE,
        )

    dialog.set_transient_for(parent)
    dialog.set_destroy_with_parent(True)
    dialog.run()
    dialog.destroy()


def _open_file_base(title, multiple=False, filters=None, last_folder=None):
    dialog = Gtk.FileChooserDialog(
        title, None, Gtk.FileChooserAction.OPEN,
        (_('_Cancel'), Gtk.ResponseType.CANCEL,
         _('_Open'), Gtk.ResponseType.OK))

    if filters:
        for f in filters:
            dialog.add_filter(f)
    if multiple:
        dialog.set_select_multiple(True)
    if last_folder:
        dialog.set_current_folder(last_folder)

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        filenames = dialog.get_filenames()
        last_folder = dialog.get_current_folder()
    else:
        filenames = []
        last_folder = None
    dialog.destroy()

    return filenames, last_folder


_last_font_folder = None

def open_fonts():
    global _last_font_folder

    font_filter = Gtk.FileFilter()
    font_filter.set_name(_('Fonts'))
    for ext in common.FONT_EXTENSIONS:
        font_filter.add_pattern(utils.ext_to_glob(ext))

    filenames, _last_font_folder = _open_file_base(
        _('Choose fonts'), True, (font_filter,), _last_font_folder)
    return filenames

