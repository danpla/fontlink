# FontLink

FontLink is a program for Unix-like systems that allows you to use
fonts without having to install them.


## Usage

The FontLink's interface consists of two lists. The left one contains
font sets; the right one shows fonts of the selected set.

To add fonts to the selected set, use the button below the font list,
the context menu, or drop them from your file manager anywhere on the
FontLink's window. You can add the same font in several sets. Disabling
or removing such a font from one set will not unlink it if it's still
enabled in others.

A font appearing as "inactive" (grayed out) means that either the
font with the same name is already installed on your system, or the
file doesn't exist, e.g. it has been moved since the last time you
used the program. Check the pop-up tooltip for more information.

It's recommended to set up your fonts before running a program that
will use them, because not all programs can update the list of fonts
at runtime.

If you want to add FontLink to autostart, add `--minimized` or `-m`
argument to start the program with the hidden window.
