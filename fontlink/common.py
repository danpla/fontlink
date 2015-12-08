
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
