
from collections import Counter
import os
import atexit


_refcounter = Counter()


def link(links):
    if _refcounter[links] == 0:
        for link in links:
            try:
                os.symlink(*link)
            except OSError:
                pass
    _refcounter[links] += 1


def unlink(links):
    if _refcounter[links] == 0:
        return

    _refcounter[links] -= 1
    if _refcounter[links] == 0:
        for link in links:
            link_path = link[1]
            if os.path.islink(link_path):
                try:
                    os.unlink(link_path)
                except OSError:
                    pass


@atexit.register
def _remove_links():
    for links, refcount in _refcounter.items():
        if refcount == 0:
            continue
        for link in links:
            link_path = link[1]
            if os.path.islink(link_path):
                try:
                    os.unlink(link_path)
                except OSError:
                    pass
