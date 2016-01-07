
import os
import subprocess

from . import utils


FONT_EXTENSIONS = (
    '.ttf',
    '.ttc',
    '.otf',
    '.otc',
    '.woff',
    '.woff2',
    '.dfont',
    '.bin',
    '.pfa',
    '.pfb',
    '.ps',
    )

# MacBinary (supported by Scribus) may also contain PostScript fonts.
FONT_EXTENSIONS_PS = FONT_EXTENSIONS[FONT_EXTENSIONS.index('.bin'):]

FONT_SEARCH_PATTERNS = [
    '*{}'.format(utils.string_to_glob(ext)) for ext in FONT_EXTENSIONS]


def _get_installed_fonts():
    '''Create a mapping of installed fonts {font_name: font_dir}.'''
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
