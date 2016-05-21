# FontLink

FontLink is a small program for Unix-like systems that allows you to use
fonts without having to install them.


## Usage

FontLink has a simple interface that mainly consists of two lists. The left
one contains font sets; the right one shows fonts of the selected set.
Each has a context menu and a toolbar for quick access to the most frequently
used actions.

You can create new sets or just use the default one. To quickly rename a set,
click twice on it. To change its position in the list, drag it with the `Shift`
key pressed.

In addition to using the context menu or the toolbar button, you can add fonts
by dropping them from your file manager anywhere on the FontLink's window.

The same font can be in multiple sets. In this case, disabling or removing
such a font from one set does not unlink it if it is still enabled in others.

If you add a font that is already installed somewhere on your system, it will
appear as “inactive” and its checkbox will always be enabled. Check its pop-up
tooltip to see where it is installed.

FontLink has an icon in the notification area, which you can click with the
middle mouse button to quickly hide/show the main window. If you want to add
FontLink to autostart, don't forget to add `--minimized` or `-m` argument
to start the program with the hidden window.

It is recommended to set up your fonts *before* running a program that will
use them, because not all programs can update a list of fonts at runtime.
For example, GIMP and LibreOffice can do this, but Inkscape and Scribus
cannot.

Remember that fonts added to FontLink are linked only while it is running.
