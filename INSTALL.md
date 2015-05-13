# Installing FontLink

By the way, you can use Fontlink uninstalled: simply run `bin/fontlink`.
In this case, however, it will be available only in English.


## Installing from sources

### Dependencies

* Python 3.X
* PyGObject
* gir1.2-appindicator3

apt (Debian, Ubuntu etc.):

    $ sudo apt-get install python3 python3-gi gir1.2-appindicator3


### Compiling

    $ make

This will create localization (.mo) files and compile Python sources
to bytecode for faster program startup.


### Installing

As root:

    $ make install


### Uninstalling

As root:

    $ make uninstall

After uninstalling you may delete configuration directory:

    $ rm -rf ~/.config/fontlink


### Cleaning up

  To clean up source directory after `make`, run:

    $ make clean
