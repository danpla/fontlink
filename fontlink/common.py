
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

# MacBinary (supported by Scribus) may also contain PostScript fonts.
FONT_EXTENSIONS_PS = FONT_EXTENSIONS[FONT_EXTENSIONS.index('.bin'):]
