
FONT_EXTENSIONS = (
    '.ttf',
    '.ttc',
    '.otf',
    '.woff',
    '.dfont',
    '.bin',
    '.pfa',
    '.pfb',
    '.ps',
    )

# MacBinary (supported by Scribus) may also contain Type 1 fonts.
FONT_EXTENSIONS_TYPE1 = FONT_EXTENSIONS[FONT_EXTENSIONS.index('.bin'):]
