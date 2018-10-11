
from functools import wraps
from collections import OrderedDict
import os

from gi.repository import Gtk, GObject

from .. import config
from .. import linker
from .. import font_utils
from .. import utils


def _watch_num_active(method):
    """Automatically notify if FontSet.num_active was changed by method."""
    @wraps(method)
    def wrapper(font_set, *args, **kwargs):
        num_active_before = font_set.num_active
        method(font_set, *args, **kwargs)
        if font_set.num_active != num_active_before:
            font_set.notify('num-active')
    return wrapper


class FontSet(Gtk.ListStore):

    # COL_LINKS is a tuple of linker.Link.
    # The first pair is always present and describes the main font file.
    # Others (if any) are additional files (.afm, .pfm, etc.).
    COL_LINKS = 0
    COL_ENABLED = 1

    # COL_LINKABLE is True if the file exists and the font with the
    # same filename wasn't installed in the system at the moment of
    # FontLink launch.
    COL_LINKABLE = 2
    COL_NAME = 3

    def __init__(self):
        super().__init__(
            object,
            bool,
            bool,
            str,
            )

        # Number of currently active fonts.
        self._num_active = 0
        # Cached font names for faster filtering of existing fonts.
        self._fonts = set()

        self.set_sort_column_id(self.COL_NAME, Gtk.SortType.ASCENDING)

    @GObject.Property
    def num_active(self):
        """Number of currently active (linked) fonts."""
        return self._num_active

    @_watch_num_active
    def add_fonts(self, items):
        """Add fonts to the set.

        items -- iterable of paths and/or pairs (path, state).
        """
        for item in items:
            if isinstance(item, str):
                path = item
                enabled = True
            else:
                path, enabled = item

            font_dir, font_name = os.path.split(path)
            font_root_name, font_ext = os.path.splitext(font_name)
            if (font_ext.lower() not in font_utils.FONT_EXTENSIONS or
                    font_name in self._fonts or
                    font_dir.startswith(config.FONTS_DIR)):
                continue

            links = [
                linker.Link(path, os.path.join(config.FONTS_DIR, font_name))]

            installed = font_name in font_utils.INSTALLED_FONTS
            file_exists = os.path.isfile(path)
            if installed:
                enabled = True
            elif not file_exists:
                enabled = False
            elif font_ext.lower() in font_utils.FONT_EXTENSIONS_PS:
                metrics_path = font_utils.find_metrics(
                    font_dir, font_root_name)
                if metrics_path:
                    links.append(
                        linker.Link(
                            metrics_path,
                            os.path.join(
                                config.FONTS_DIR,
                                os.path.basename(metrics_path))))

            links = tuple(links)

            self.append(
                (
                    links,
                    enabled,
                    file_exists and not installed,
                    font_name))
            self._fonts.add(font_name)

            if enabled:
                self._num_active += 1
                if not installed:
                    linker.create_links(links)

    @_watch_num_active
    def add_fonts_from(self, font_set):
        for row in font_set:
            font_name = row[font_set.COL_NAME]
            if font_name in self._fonts:
                continue

            self.append(row[:])
            self._fonts.add(font_name)

            if row[font_set.COL_ENABLED]:
                self._num_active += 1
                if row[font_set.COL_LINKABLE]:
                    linker.create_links(row[font_set.COL_LINKS])

    @_watch_num_active
    def remove_fonts(self, tree_paths):
        for tree_path in reversed(tree_paths):
            row = self[tree_path]
            if row[self.COL_ENABLED]:
                self._num_active -= 1
                if row[self.COL_LINKABLE]:
                    linker.remove_links(row[self.COL_LINKS])
            self._fonts.discard(row[self.COL_NAME])
            self.remove(self.get_iter(tree_path))

    @_watch_num_active
    def remove_all_fonts(self):
        for row in self:
            if row[self.COL_LINKABLE] and row[self.COL_ENABLED]:
                linker.remove_links(row[self.COL_LINKS])
        self._fonts.clear()
        self.clear()
        self._num_active = 0

    def toggle_state(self, tree_path):
        row = self[tree_path]
        if not row[self.COL_LINKABLE]:
            return

        new_state = not row[self.COL_ENABLED]
        row[self.COL_ENABLED] = new_state
        if new_state:
            linker.create_links(row[self.COL_LINKS])
            self._num_active += 1
        else:
            linker.remove_links(row[self.COL_LINKS])
            self._num_active -= 1

        self.notify('num-active')

    @_watch_num_active
    def set_state_all(self, state):
        """Set the state for all fonts in the set."""
        for row in self:
            if (not row[self.COL_LINKABLE]
                    or row[self.COL_ENABLED] == state):
                continue

            if state:
                linker.create_links(row[self.COL_LINKS])
                self._num_active += 1
            else:
                linker.remove_links(row[self.COL_LINKS])
                self._num_active -= 1
            row[self.COL_ENABLED] = state


class SetStore(Gtk.ListStore):

    COL_NAME = 0
    COL_FONTSET = 1

    def __init__(self):
        super().__init__(
            str,
            object,
            )

    def _on_set_changed(self, font_set, gproperty):
        for row in self:
            if row[self.COL_FONTSET] == font_set:
                self.row_changed(row.path, row.iter)
                break

    def add_set(self, name, insert_after=None):
        name = utils.unique_name(name, (row[self.COL_NAME] for row in self))

        font_set = FontSet()
        font_set.connect('notify::num-active', self._on_set_changed)

        return self.insert_after(insert_after, (name, font_set))

    def duplicate_set(self, tree_iter):
        name = utils.unique_name(
            self[tree_iter][self.COL_NAME],
            (row[self.COL_NAME] for row in self))

        font_set = FontSet()
        font_set.add_fonts_from(self[tree_iter][self.COL_FONTSET])
        font_set.connect('notify::num-active', self._on_set_changed)

        return self.insert_after(tree_iter, (name, font_set))

    @property
    def as_json(self):
        json_sets = []
        for row in self:
            fonts = []
            for font_set in row[self.COL_FONTSET]:
                fonts.append({
                    'enabled': font_set[FontSet.COL_ENABLED],
                    'path': font_set[FontSet.COL_LINKS][0].source
                    })
            json_sets.append(OrderedDict((
                ('name', row[self.COL_NAME]),
                ('fonts', fonts))))
        return json_sets

    @as_json.setter
    def as_json(self, json_sets):
        tree_iter = None
        for json_set in json_sets:
            tree_iter = self.add_set(json_set['name'], tree_iter)
            self[tree_iter][self.COL_FONTSET].add_fonts(
                ((f['path'], f['enabled']) for f in json_set['fonts']))
