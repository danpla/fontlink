
import os

from gi.repository import GLib

from . import app_info

# ICON_DIR will be set from the main script if FontLink will be launched
# uninstalled.
ICON_DIR = ''

CONFIG_DIR = os.path.join(GLib.get_user_config_dir(), app_info.NAME)
if not os.path.isdir(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

FONTS_DIR = os.path.join(GLib.get_user_data_dir(), 'fonts')
if not os.path.isdir(FONTS_DIR):
    os.makedirs(FONTS_DIR)
