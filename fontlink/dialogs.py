
from gettext import gettext as _

from gi.repository import Gtk

from . import common
from . import app_info
from . import utils


def yesno(message, parent):
    dialog = Gtk.MessageDialog(
        parent, 0, Gtk.MessageType.QUESTION,
        Gtk.ButtonsType.YES_NO, message)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.YES


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

        parent=parent,
        transient_for=parent,
        destroy_with_parent=True
        )

    dialog.run()
    dialog.destroy()


_last_font_folder = None

def open_fonts(parent):
    global _last_font_folder

    font_filter = Gtk.FileFilter()
    font_filter.set_name(_('Fonts'))
    for ext in common.FONT_EXTENSIONS:
        font_filter.add_pattern(utils.ext_to_glob(ext))

    dialog = Gtk.FileChooserDialog(
        _('Choose fonts'),
        parent,
        Gtk.FileChooserAction.OPEN,
        (_('_Cancel'), Gtk.ResponseType.CANCEL,
         _('_Open'), Gtk.ResponseType.OK),
        select_multiple=True,
        )
    dialog.add_filter(font_filter)
    if _last_font_folder:
        dialog.set_current_folder(_last_font_folder)

    if dialog.run() == Gtk.ResponseType.OK:
        font_paths = dialog.get_filenames()
        _last_font_folder = dialog.get_current_folder()
    else:
        font_paths = []
        _last_font_folder = None
    dialog.destroy()

    return font_paths

