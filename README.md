# FontLink

FontLink is a small GTK+ utility to install fonts temporarily on Unix-like
systems.

It allows you to quickly install certain fonts only when you really
need them without copying files or creating symlinks by hand.

FontLink has a very simple interface with which you can group fonts into sets
(for example, one set per project) and quickly enable or disable certain fonts
as well as entire sets in a single click.

As you might guess from the name, it uses mechanism of symbolic links
for fast “fake” installation without actual copying and deleting font files.


## Usage tips and tricks

* To rename a set, click twice on it. To change its position in the list,
  drag it with `Shift` pressed.

* You can use drag-and-drop to add fonts.

* Double click on font will open it in associated application (probably,
  font viewer).

* The same font can be added to multiple sets. In this case, disabling such
  font in certain set does not unlink it if it still enabled in other sets.

* Fonts added to FontLink will be linked only while it's running.

* It may be useful to add FontLink to autostart. In this case, add
  `--minimized` or `-m` argument to start FontLink minimized to the
  notification area.

* Not all programs can update font list on the fly, so it's better to set up
  your fonts *before* running a program that will use them. For example,
  GIMP and LibreOffice can rescan fonts, but Inkscape and Scribus are not.
