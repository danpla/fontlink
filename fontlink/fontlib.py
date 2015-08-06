
from gettext import gettext as _
from functools import wraps
from collections import OrderedDict
import json
import os

from gi.repository import Gtk, Gdk, GObject, GLib

from . import conf
from . import common
from .settings import settings
from . import dialogs
from . import linker
from . import utils


def _watch_nactive(method):
    '''Automatically notify if FontSet.nactive was changed by method.'''
    @wraps(method)
    def wrapper(font_set, *args, **kwargs):
        nactive_before = font_set.nactive
        method(font_set, *args, **kwargs)
        if font_set.nactive != nactive_before:
            font_set.notify('nactive')
    return wrapper


class FontSet(Gtk.ListStore):

    # COL_LINKS is a tuple of linker.Link.
    # First pair is always present and describes the main font file.
    # Others (if any) are additional files, like .afm and so on.
    COL_LINKS = 0
    COL_ENABLED = 1

    # COL_LINKED indicates that font was linked by FontLink and will be False
    # if it was already installed in system. In such case, COL_ENABLED
    # will be always True (there is nothing complicated to 'hide' installed
    # fonts using fonts.conf, but FontLink is not for this).
    COL_LINKED = 2
    COL_NAME = 3
    COL_TOOLTIP = 4

    def __init__(self):
        super().__init__(
            object,
            bool,
            bool,
            str,
            str,
            )

        # Number of currently active fonts.
        self._nactive = 0
        # Cached font names for faster filtering of existing fonts.
        self._fonts = set()

        self.set_sort_column_id(self.COL_NAME, Gtk.SortType.ASCENDING)

    @GObject.property
    def nactive(self):
        '''Number of currently active (linked) fonts.'''
        return self._nactive

    @_watch_nactive
    def add_fonts(self, items):
        '''Add fonts to the set.

        items -- list containing paths and/or pairs (state, path).
        '''
        for item in items:
            if isinstance(item, str):
                enabled = True
                path = item
            else:
                enabled, path = item

            font_dir, font_name = os.path.split(path)
            font_root_name, font_ext = os.path.splitext(font_name)
            if (not font_ext.lower() in common.FONT_EXTENSIONS or
                    not os.path.isfile(path) or
                    font_name in self._fonts):
                continue

            links = [linker.Link(path, os.path.join(conf.FONTS_DIR, font_name)),]

            installed = font_name in conf.INSTALLED_FONTS
            if installed:
                enabled = True
                tooltip = '{}\n<b>{}</b>\n{}'.format(
                    path,
                    _('Already installed in:'),
                    conf.INSTALLED_FONTS[font_name])
            else:
                tooltip = path

                # Search for .afm .
                if font_ext.lower() in common.FONT_EXTENSIONS_PS:
                    for file_name in next(os.walk(font_dir))[2]:
                        file_root_name, file_ext = os.path.splitext(file_name)
                        if (file_root_name == font_root_name and
                                file_ext.lower() == '.afm'):
                            links.append(
                                linker.Link(
                                    os.path.join(font_dir, file_name),
                                    os.path.join(conf.FONTS_DIR, file_name)))

            links = tuple(links)

            self.append((links, enabled, not installed, font_name, tooltip))
            self._fonts.add(font_name)

            if enabled:
                self._nactive += 1
                if not installed:
                    linker.create_links(links)

    @_watch_nactive
    def remove_fonts(self, tree_paths=None):
        '''Remove fonts from the set.

        If tree_paths is None, all fonts will be removed.
        '''
        if not tree_paths:
            for row in self:
                if row[self.COL_LINKED] and row[self.COL_ENABLED]:
                    linker.remove_links(row[self.COL_LINKS])
            self._fonts.clear()
            self.clear()
            self._nactive = 0
            return

        for tree_path in reversed(tree_paths):
            row = self[tree_path]
            if row[self.COL_ENABLED] and row[self.COL_LINKED]:
                linker.remove_links(row[self.COL_LINKS])
                self._nactive -= 1
            self._fonts.remove(row[self.COL_NAME])
            self.remove(self.get_iter(tree_path))

    def toggle_state(self, tree_path):
        '''Toggle the state of certain font.'''
        row = self[tree_path]
        if not row[self.COL_LINKED]:
            return

        new_state = not row[self.COL_ENABLED]
        row[self.COL_ENABLED] = new_state
        if new_state:
            linker.create_links(row[self.COL_LINKS])
            self._nactive += 1
        else:
            linker.remove_links(row[self.COL_LINKS])
            self._nactive -= 1

        self.notify('nactive')

    @_watch_nactive
    def set_state_all(self, state):
        '''Set the state for all fonts in the set.'''
        for row in self:
            if not row[self.COL_LINKED]:
                continue

            if row[self.COL_ENABLED] != state:
                if state:
                    linker.create_links(row[self.COL_LINKS])
                    self._nactive += 1
                else:
                    linker.remove_links(row[self.COL_LINKS])
                    self._nactive -= 1
                row[self.COL_ENABLED] = state


class SetStore(Gtk.ListStore):
    '''Set store contains font sets.

    Each entry holds number of currently active fonts in the set (to adjust
    state of checkbox), set name and FontSet itself.
    '''

    COL_NACTIVE = 0
    COL_NAME = 1
    COL_FONTSET = 2

    def __init__(self):
        super().__init__(
            int,
            str,
            object,
            )

    def _notify_nactive(self, font_set, gproperty):
        for row in self:
            if row[self.COL_FONTSET] == font_set:
                row[self.COL_NACTIVE] = row[self.COL_FONTSET].nactive

    def add_set(self, name=_('New set'), insert_after=None):
        all_names = [row[self.COL_NAME] for row in self]
        name = utils.unique_name(name, all_names)

        font_set = FontSet()
        font_set.connect('notify::nactive', self._notify_nactive)

        tree_iter = self.insert_after(insert_after, (0, name, font_set))
        return tree_iter


class FontList(Gtk.Box):
    '''FontList shows and manages fonts of the selected FontSet.'''

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._create_ui()

    def _create_ui(self):
        self._font_list = Gtk.TreeView(
            headers_visible=False,
            rubber_banding=True,
            tooltip_column=FontSet.COL_TOOLTIP)
        self._font_list.connect('row-activated', self._on_row_activated)

        self._selection = self._font_list.get_selection()
        self._selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        scrolled = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.IN)
        scrolled.set_size_request(250, -1)
        scrolled.add(self._font_list)
        self.pack_start(scrolled, True, True, 0)

        # Columns.

        toggle = Gtk.CellRendererToggle()
        toggle.connect('toggled', self._on_toggled)
        col_toggle = Gtk.TreeViewColumn(
            '', toggle,
            active=FontSet.COL_ENABLED,
            activatable=FontSet.COL_LINKED)
        self._font_list.append_column(col_toggle)

        name = Gtk.CellRendererText()
        col_name = Gtk.TreeViewColumn(
            _('Fonts'), name, text=FontSet.COL_NAME)
        col_name.set_sort_column_id(FontSet.COL_NAME)
        self._font_list.append_column(col_name)

        # Toolbar.

        toolbar = Gtk.Toolbar(icon_size=Gtk.IconSize.SMALL_TOOLBAR)
        self.pack_start(toolbar, False, True, 0)

        btn_add = Gtk.ToolButton(
            label=_('Add…'),
            icon_name='list-add',
            tooltip_text=_('Add fonts…'))
        btn_add.connect('clicked', self._on_add)
        toolbar.add(btn_add)

        btn_remove = Gtk.ToolButton(
            label=_('Remove'),
            icon_name='list-remove',
            tooltip_text=_('Remove selected fonts'))
        btn_remove.connect('clicked', self._on_remove)
        self._selection.connect(
            'changed',
            lambda s: btn_remove.set_sensitive(s.count_selected_rows() > 0))
        toolbar.add(btn_remove)

        btn_clear = Gtk.ToolButton(
            label=_('Remove all'),
            icon_name='edit-clear',
            tooltip_text=_('Remove all fonts'),
            sensitive=False)
        btn_clear.connect('clicked', self._on_clear)
        self._btn_clear = btn_clear
        toolbar.add(btn_clear)

    def _on_add(self, button):
        font_set = self._font_list.get_model()
        if not font_set:
            return

        paths = dialogs.open_fonts(self.get_toplevel())
        if not paths:
            return
        font_set.add_fonts(paths)
        self._btn_clear.set_sensitive(len(font_set) > 0)

    def _on_remove(self, button):
        font_set, tree_paths = self._selection.get_selected_rows()
        if (font_set and tree_paths and
                dialogs.yesno(
                    _('Remove selected fonts from the set?'),
                    self.get_toplevel())):
            font_set.remove_fonts(tree_paths)
            self._btn_clear.set_sensitive(len(font_set) > 0)

    def _on_toggled(self, cell_toggle, path):
        font_set = self._font_list.get_model()
        font_set.toggle_state(path)

    def _on_clear(self, button):
        font_set = self._font_list.get_model()
        if (font_set and
                dialogs.yesno(
                    _('Remove all fonts from the set?'),
                    self.get_toplevel())):
            font_set.remove_fonts()
            button.set_sensitive(False)

    def _on_row_activated(self, font_list, path, column):
        if column == font_list.get_column(SetStore.COL_NAME):
            font_set = font_list.get_model()
            Gtk.show_uri(
                None,
                GLib.filename_to_uri(
                    font_set[path][FontSet.COL_LINKS][0].source),
                Gdk.CURRENT_TIME)

    @property
    def font_set(self):
        return self._font_list.get_model()

    @font_set.setter
    def font_set(self, font_set):
        self._font_list.set_model(font_set)
        if font_set:
            self._font_list.set_search_column(FontSet.COL_NAME)
            self._btn_clear.set_sensitive(len(font_set) > 0)


class FontLib(Gtk.Paned):

    def __init__(self):
        super().__init__()
        self.set_size_request(500, 250)

        self._set_store = SetStore()
        self._font_list = FontList()
        self._create_ui()

    def _create_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self._set_list = Gtk.TreeView(
            model=self._set_store,
            headers_visible=False,
            reorderable=True,
            search_column=SetStore.COL_NAME)

        self._selection = self._set_list.get_selection()
        self._selection.set_mode(Gtk.SelectionMode.BROWSE)
        self._selection.connect('changed', self._on_selection_changed)

        scrolled = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.IN)
        scrolled.set_size_request(150, -1)
        scrolled.add(self._set_list)
        box.pack_start(scrolled, True, True, 0)

        # Columns.

        toggle = Gtk.CellRendererToggle()
        toggle.connect('toggled', self._on_toggled)
        col_toggle = Gtk.TreeViewColumn(
            '', toggle, active=SetStore.COL_NACTIVE)
        col_toggle.set_cell_data_func(toggle, self._toggle_cell_data_func)
        self._set_list.append_column(col_toggle)

        name = Gtk.CellRendererText(editable=True)
        name.connect('edited', self._on_name_edited)
        col_name = Gtk.TreeViewColumn(
            _('Font sets'), name, text=SetStore.COL_NAME)
        self._set_list.append_column(col_name)

        # Toolbar.

        toolbar = Gtk.Toolbar(icon_size=Gtk.IconSize.SMALL_TOOLBAR)
        box.pack_start(toolbar, False, True, 0)

        btn_new = Gtk.ToolButton(
            label=_('Create'),
            icon_name='document-new',
            tooltip_text=_('Create new set'))
        btn_new.connect('clicked', self._on_new)
        toolbar.add(btn_new)

        btn_delete = Gtk.ToolButton(
            label=_('Delete'),
            icon_name='edit-delete',
            tooltip_text=_('Delete set'))
        btn_delete.connect('clicked', self._on_delete)
        toolbar.add(btn_delete)

        self.pack1(box, False, False)
        self.pack2(self._font_list, True, False)

    def _toggle_cell_data_func(self, column, cell, set_store, tree_iter, data):
        active_fonts = set_store[tree_iter][SetStore.COL_NACTIVE]

        if active_fonts == 0:
            cell.props.inconsistent = False
            cell.props.active = False
        elif active_fonts == len(set_store[tree_iter][SetStore.COL_FONTSET]):
            cell.props.inconsistent = False
            cell.props.active = True
        else:
            cell.props.inconsistent = True

    def _on_selection_changed(self, selection):
        set_store, tree_iter = selection.get_selected()
        if not tree_iter:
            return
        self._font_list.font_set = set_store[tree_iter][SetStore.COL_FONTSET]

    def _on_toggled(self, cell_toggle, path):
        font_set = self._set_store[path][SetStore.COL_FONTSET]
        font_set.set_state_all(font_set.nactive < len(font_set))

    def _on_name_edited(self, cell_text, path, new_text):
        new_name = new_text.strip()
        if not new_name:
            return

        old_name = self._set_store[path][SetStore.COL_NAME]
        if new_name == old_name:
            return

        all_names = [row[SetStore.COL_NAME] for row in self._set_store]
        all_names.remove(old_name)
        new_name = utils.unique_name(new_name, all_names)
        self._set_store[path][SetStore.COL_NAME] = new_name

    def _on_new(self, button):
        set_store, tree_iter = self._selection.get_selected()
        tree_iter = set_store.add_set(insert_after=tree_iter)

        # Start edit name right now.
        path = set_store.get_path(tree_iter)
        column = self._set_list.get_column(SetStore.COL_NAME)
        self._set_list.set_cursor(path, column, True)

    def _on_delete(self, button):
        set_store, tree_iter = self._selection.get_selected()
        if not tree_iter:
            return

        font_set = set_store[tree_iter][SetStore.COL_FONTSET]
        if len(font_set) != 0:
            set_name = set_store[tree_iter][SetStore.COL_NAME]
            if not dialogs.yesno(_('Delete “{}”?').format(set_name),
                                 self.get_toplevel()):
                return
            font_set.remove_fonts()

        set_store.remove(tree_iter)
        if len(set_store) == 0:
            set_store.add_set()
            self._set_list.set_cursor(0)

    def _save_sets(self):
        font_sets = []
        for set_row in self._set_store:
            font_set = OrderedDict()
            font_set['name'] = set_row[SetStore.COL_NAME]

            fonts = []
            for font_row in set_row[SetStore.COL_FONTSET]:
                font = {}
                font['enabled'] = font_row[FontSet.COL_ENABLED]
                font['path'] = font_row[FontSet.COL_LINKS][0].source
                fonts.append(font)
            font_set['fonts'] = fonts

            font_sets.append(font_set)

        try:
            with open(conf.SETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(font_sets, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _load_sets(self):
        try:
            with open(conf.SETS_FILE, 'r', encoding='utf-8') as f:
                user_sets = json.load(f)

            tree_iter = None
            for user_set in user_sets:
                tree_iter = self._set_store.add_set(user_set['name'], tree_iter)
                font_set = self._set_store[tree_iter][SetStore.COL_FONTSET]
                font_set.add_fonts(
                    ((f['enabled'], f['path']) for f in user_set['fonts']))
        except (KeyError, ValueError, OSError):
            pass

        if len(self._set_store) == 0:
            self._set_store.add_set()

    def add_fonts(self, paths):
        '''Add fonts to the currently selected set.'''
        font_set = self._font_list.font_set
        if not font_set:
            return
        font_set.add_fonts(paths)

    def save_state(self):
        settings['splitter_position'] = self.get_position()

        settings['selected_set'] = self._set_list.get_cursor()[0][0] + 1
        self._save_sets()

    def load_state(self):
        self.set_position(
            settings.get('splitter_position', self.get_position()))

        self._load_sets()
        self._set_list.set_cursor(max(0, settings.get('selected_set', 1) - 1))
