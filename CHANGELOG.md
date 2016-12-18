## 1.0.1 2016-12-18

* Added ability to copy multiple font paths
* Added a statistics column to the set list
* Fixed restoring window's geometry if the window was never maximized after
  installation


## 1.0.0 2016-01-24

* Added ability to duplicate sets
* Added ".otc" and ".woff2" extensions
* Improved metrics search mechanism
  * Uses fixed-case extensions (".afm", ".AFM", ".Afm") instead of iterating
    over all files in a font's directory
  * Searches for PFM if AFM is not found
  * If a metrics file is not found in a font's directory, searches in
  subdirectories with the same names as metrics extensions
* Fonts added from the user's font directory (`$XDG_DATA_HOME/fonts`,
  which is usually `$HOME/.local/share/fonts`) are now ignored
* UI fixes and improvements
  * Added pop-up menus for the lists
  * Better appearance of the toolbars with Graybird, Elementary, and other
    themes that provide "bottom-toolbar" style
  * The "remove fonts" confirmation dialog is now shows a name of a font,
    or a number of fonts if more than one font is selected
  * The set name column is now auto-sized
  * The set list is now scrolled to the last selected set after startup
  * Updated and improved translations
