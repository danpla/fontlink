
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


_AFM_EXTENSIONS = ('.afm', '.AFM', '.Afm')
_PFM_EXTENSIONS = ('.pfm', '.PFM', '.Pfm')


def find_metrics(font_dir, font_name):
    '''Find PS metrics (AFM or PFM).

    font_dir -- directory to search in.
    font_name -- font name without extension.

    Returns an empty string if nothing found.
    '''
    for ext in (_AFM_EXTENSIONS + _PFM_EXTENSIONS):
        path = os.path.join(font_dir, font_name + ext)
        if os.path.isfile(path):
            return path

    for extensions in (_AFM_EXTENSIONS, _PFM_EXTENSIONS):
        for subdir in (ext[1:] for ext in extensions):
            subpath = os.path.join(font_dir, subdir)
            if not os.path.isdir(subpath):
                continue

            for ext in extensions:
                path = os.path.join(subpath, font_name + ext)
                if os.path.isfile(path):
                    return path

    return ''
