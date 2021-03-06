
from collections import namedtuple, Counter
import os


Link = namedtuple('Link', 'source target')


_refcounter = Counter()


def create_links(link_group):
    """Create (link) group of linker.Link.

    link_group -- tuple of linker.Link
    """
    if _refcounter[link_group] == 0:
        for link in link_group:
            try:
                os.symlink(*link)
            except OSError:
                pass
    _refcounter[link_group] += 1


def _unlink_group(link_group):
    for link in link_group:
        if os.path.islink(link.target):
            try:
                os.unlink(link.target)
            except OSError:
                pass


def remove_links(link_group):
    """Remove (unlink) link group linked by create_links()."""
    if _refcounter[link_group] == 0:
        return

    _refcounter[link_group] -= 1
    if _refcounter[link_group] == 0:
        _unlink_group(link_group)


def remove_all_links():
    """Remove (unlink) all link groups liked by create_links()."""
    for link_group, refcount in _refcounter.items():
        if refcount == 0:
            continue
        _unlink_group(link_group)

    _refcounter.clear()
