# Installing FontLink

You can use Fontlink uninstalled: simply run `bin/fontlink`.
In this case, however, it will be available only in English.


## Package

This is recommended way to install FontLink.

DEB package for Debian, Ubuntu, and derivatives is available on
[download page](https://github.com/danpla/fontlink/releases).
On non-DEB systems, you can install it using `alien`.


## Installing from sources

### Dependencies

* Python 3.X
* PyGObject
* gir1.2-gtk-3.0
* gir1.2-appindicator3

apt (Debian, Ubuntu etc.):

    $ sudo apt-get install python3 python3-gi gir1.2-appindicator3-0.1


### Compiling

    $ make

This will create localization (.mo) files and compile Python sources
to bytecode for faster program startup.


### Installing

    $ sudo make install


### Uninstalling

    $ sudo make uninstall

After uninstalling you may delete configuration directory:

    $ rm -rf ~/.config/fontlink


### Cleaning up

  To clean up source directory after `make`, run:

    $ make clean
