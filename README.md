# FontLink

FontLink is a small GTK+ utility to install fonts temporarily on Unix-like
systems.

As you might guess from the name, it uses mechanism of symbolic links
to perform fast "fake" installation without actual copying/deleting font files.

FontLink allows you to:
* Quickly install certain fonts only when you really need them, so you don't
  need to copy, symlink or delete fonts by hand anymore.
* Group fonts into sets (for example, one set per project).
* Enable and disable certain fonts or whole sets in a single click.
* Keep the list of installed fonts to be relatively small, without cluttering
  it with fonts that you will use only several times in your life.


## Usage

FontLink's interface is pretty simple: list of font sets on the left side and
font list of selected set on the right. Each list has toolbar to manipulate
it's items.

Sets can be renamed by double click and reordered by mouse drag with Shift
pressed. Toggling checkbox will change state of all fonts in the set.

Besides using toolbar button, fonts can be added by drag-and-drop. You can drop
fonts anywhere on FontLink window and they will be added in currently
selected set. Double click on font name will open font in associated
application (probably, font viewer).


## Tips and tricks

* It may be useful to add FontLink to autostart. In this case, add
  `--minimized` or `-m` argument to start FontLink minimized to the
  notification area.

* Fonts added to FontLink will be linked only while it's running.

* Same font can be added to multiple sets. In this case, disabling font in
  certain set does not unlink it if it still enabled in other set(s).

* If you will add fonts that was already installed on your system, their
  checkboxes will be unclickable (always enabled) and pop-up tooltip will
  additionally contain path where certain font is installed.

* Not all programs can update font list on the fly, so it's better to setup
  your fonts *before* running program that will use them. For example,
  GIMP and LibreOffise can rescan fonts, but Inkscape and Scribus are not.
