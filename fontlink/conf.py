
import gettext
import os
import sys
import subprocess

from gi.repository import GLib

from . import app_info

# ICON_DIR will be initialized from the main script in case if FontLink will be
# launched uninstalled. Currently used to setup icon for AppIndicator.
ICON_DIR = ''

DATA_DIR = os.path.join(sys.prefix, 'share', app_info.NAME)
LOCALE_DIR = os.path.join(sys.prefix, 'share', 'locale')

CONFIG_DIR = os.path.join(GLib.get_user_config_dir(), app_info.NAME)
if not os.path.isdir(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

SETS_FILE = os.path.join(CONFIG_DIR, 'sets.json')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'settings.json')


FONTS_DIR = os.path.expanduser('~/.local/share/fonts')
if not os.path.isdir(FONTS_DIR):
    os.makedirs(FONTS_DIR)


def _get_installed_fonts():
    '''Creates mapping of installed fonts {font_name: font_dir}.'''
    fonts = {}
    try:
        for path in subprocess.check_output(
                ['fc-list', ':', 'file'],
                universal_newlines=True).split():
            font_dir, font_name = os.path.split(path.rstrip(':'))
            fonts[font_name] = font_dir
    except FileNotFoundError:
        pass
    return fonts

INSTALLED_FONTS = _get_installed_fonts()


gettext.bindtextdomain(app_info.NAME, LOCALE_DIR)
gettext.textdomain(app_info.NAME)

_ = gettext.gettext
ngettext = gettext.ngettext
