# Installing FontLink


## Dependencies

To use FontLink, you will need the following dependencies.

* Python 3
* PyGObject
* gir1.2-gtk-3.0
* gir1.2-appindicator3

Make is also needed to install FontLink, or to translate the user
interface if you want to use the program without installation.


### Installing dependencies

apt (Debian, Ubuntu, and derivatives):

    sudo apt-get install make python3 python3-gi gir1.2-gtk-3.0 gir1.2-appindicator3-0.1


## Using without installation

You can use Fontlink uninstalled: simply run `bin/fontlink`.
If you need the translated interface, run `make` before this.


## Package

This is recommended way to install FontLink.

DEB package for Debian, Ubuntu, and derivatives is available on the
[download page](https://github.com/danpla/fontlink/releases). On
systems that use a different package format, you can install the DEB
using `alien`.


## Installing from sources

### Compiling

    make

This will create localization files and compile Python sources to
bytecode for faster program startup. At this point, you can use
FontLink without installation by executing `bin/fontlink`.


### Installing

    sudo make install


### Uninstalling

    sudo make uninstall

After uninstalling you may delete configuration directory:

    rm -rf ~/.config/fontlink


### Cleaning up

To clean up source directory after `make`, run:

    make clean
