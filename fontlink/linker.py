
from collections import namedtuple, Counter
import os
import atexit


Link = namedtuple('Link', 'source target')


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
            if os.path.islink(link.target):
                try:
                    os.unlink(link.target)
                except OSError:
                    pass


@atexit.register
def _remove_links():
    for links, refcount in _refcounter.items():
        if refcount == 0:
            continue
        for link in links:
            if os.path.islink(link.target):
                try:
                    os.unlink(link.target)
                except OSError:
                    pass
