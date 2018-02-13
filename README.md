# FontLink

FontLink is a program for Unix-like systems that allows you to use fonts
without having to install them.


## Usage

The FontLink's interface consists of two lists. The left one contains font
sets; the right one shows fonts of the selected set.

To add fonts to a set, use the button below the font list, the context menu,
or drop them from your file manager anywhere on the FontLink's window. You can
add the same font in several sets. Disabling or removing such a font from one
set will not unlink it if it's still enabled in others.

If a font is already installed on your system, it will appear as “inactive”
and its checkbox will always be enabled. Check its pop-up tooltip to see
where it is installed.

It's recommended to set up your fonts *before* running a program that will
use them, because not all programs can update the list of fonts at runtime.

If you want to add FontLink to autostart, don't forget to add `--minimized`
or `-m` argument to start the program with the hidden window.
