
from collections import OrderedDict
import json
import os

from gi.repository import Gtk, Gdk, GObject, GLib

from .conf import _
from . import conf
from . import common
from . import dialogs
from . import linker
from . import utils


class FontSet(Gtk.ListStore):

    # COL_LINKS is a tuple containing pairs (file_path, link_path).
    # First pair is always present and describes main font.
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
        self.connect('row-deleted', self._on_row_deleted)

    @GObject.property
    def nactive(self):
        return self._nactive

    def _count_active(self):
        self._nactive = 0
        for row in self:
            if row[self.COL_ENABLED]:
                self._nactive += 1

    def _on_row_deleted(self, model, path):
        self._count_active()
        self.notify('nactive')

    def add_fonts(self, items):
        '''Add fonts in the set.

        items - list containing paths and/or pairs (state, path).
        '''
        for item in items:
            if isinstance(item, str):
                enabled = True
                path = item
            else:
                enabled, path = item

            font_dir, font_name = os.path.split(path)
            font_root_name, font_ext = os.path.splitext(font_name)
            if (not font_ext.lower().endswith(common.FONT_EXTENSIONS) or
                    not os.path.isfile(path) or
                    font_name in self._fonts):
                continue

            links = [(path, os.path.join(conf.FONTS_DIR, font_name)),]

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
                if font_ext.lower().endswith(common.FONT_EXTENSIONS_TYPE1):
                    for file_name in next(os.walk(font_dir))[2]:
                        file_root_name, file_ext = os.path.splitext(file_name)
                        if (file_root_name == font_root_name and
                                file_ext.lower() == '.afm'):
                            links.append(
                                (os.path.join(font_dir, file_name),
                                 os.path.join(conf.FONTS_DIR, file_name)))

            links = tuple(links)

            self.append((links, enabled, not installed, font_name, tooltip))
            self._fonts.add(font_name)

            if enabled:
                self._nactive += 1
                if not installed:
                    linker.link(links)

        self.notify('nactive')

    def remove_fonts(self, tree_paths=None):
        '''Remove fonts from the set.

        If tree_paths is None, all fonts will be removed.
        '''
        if not tree_paths:
            for row in self:
                if row[self.COL_ENABLED] and row[self.COL_LINKED]:
                    linker.unlink(row[self.COL_LINKS])
            self._fonts.clear()
            self.clear()
            return

        for tree_path in reversed(tree_paths):
            row = self[tree_path]
            if row[self.COL_ENABLED] and row[self.COL_LINKED]:
                linker.unlink(row[self.COL_LINKS])
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
            linker.link(row[self.COL_LINKS])
            self._nactive += 1
        else:
            linker.unlink(row[self.COL_LINKS])
            self._nactive -= 1

        self.notify('nactive')

    def set_state_all(self, state):
        '''Set the state for all fonts in the set.'''
        self._nactive = 0
        for row in self:
            if not row[self.COL_LINKED]:
                self._nactive += 1
                continue
            row[self.COL_ENABLED] = state
            if state:
                self._nactive += 1
                linker.link(row[self.COL_LINKS])
            else:
                linker.unlink(row[self.COL_LINKS])

        self.notify('nactive')


class SetStore(Gtk.ListStore):
    '''Set store contains font sets.

    Each entry holds number of currently active fonts in the set (to adjust
    state of checkbox), set name and FontSet itself.
    '''

    COL_NACTIVE = 0
    COL_NAME = 1
    COL_FONTSTORE = 2

    def __init__(self):
        super().__init__(
            int,
            str,
            object,
            )

    def _notify_nactive(self, font_set, gproperty):
        for row in self:
            if row[self.COL_FONTSTORE] == font_set:
                row[self.COL_NACTIVE] = row[self.COL_FONTSTORE].nactive

    def add_set(self, name=_('New set'), insert_after=None):
        all_names = [row[self.COL_NAME] for row in self]
        name = utils.unique_name(name, all_names)

        font_set = FontSet()
        font_set.connect('notify::nactive', self._notify_nactive)

        tree_iter = self.insert_after(insert_after, (0, name, font_set))
        return tree_iter


class FontList(Gtk.Box):
    '''FontList shows and manages currently selected FontSet.'''

    def __init__(self, set_list):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._create_ui()
        set_list.connect('set-selected', self._on_set_selected)

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
        self._col_name = col_name
        self._font_list.append_column(col_name)

        # Toolbar.

        toolbar = Gtk.Toolbar(icon_size=Gtk.IconSize.MENU)
        self.pack_start(toolbar, False, True, 0)

        btn_add = Gtk.ToolButton(
            label=_('Add fonts…'),
            icon_name='list-add')
        btn_add.set_tooltip_text(btn_add.get_label())
        btn_add.connect('clicked', self._on_add)
        toolbar.add(btn_add)

        btn_remove = Gtk.ToolButton(
            label=_('Remove selected fonts'),
            icon_name='list-remove')
        btn_remove.set_tooltip_text(btn_remove.get_label())
        btn_remove.connect('clicked', self._on_remove)
        self._selection.connect(
            'changed',
            lambda s: btn_remove.set_sensitive(bool(s.get_selected_rows()[1])))
        toolbar.add(btn_remove)

    def _on_add(self, button):
        model = self._font_list.get_model()
        if not model:
            return

        fonts = dialogs.open_fonts()
        if not fonts:
            return
        model.add_fonts(fonts)

    def _on_remove(self, button):
        model, paths = self._selection.get_selected_rows()
        if (not paths or
                not dialogs.yesno(
                    _('Remove selected fonts from the set?'),
                    self.get_toplevel())):
            return
        model.remove_fonts(paths)

    def _on_toggled(self, widget, path):
        model = self._font_list.get_model()
        model.toggle_state(path)

    def _on_row_activated(self, treeview, path, column):
        if column == self._col_name:
            model = treeview.get_model()
            Gtk.show_uri(
                None,
                GLib.filename_to_uri(model[path][FontSet.COL_LINKS][0][0]),
                Gdk.CURRENT_TIME)

    def _on_set_selected(self, gobject, font_set):
        self.font_set = font_set

    @property
    def font_set(self):
        '''Assigned FontSet.'''
        return self._font_list.get_model()

    @font_set.setter
    def font_set(self, font_set):
        self._font_list.set_model(font_set)
        self._font_list.set_search_column(FontSet.COL_NAME)


class SetList(Gtk.Box):
    '''SetList shows and manages SetStore.

    It will be associated with FontList that will show currently selected set.
    '''

    __gsignals__ = {
        # Tell FontList to change the set.
        'set-selected': (
            GObject.SIGNAL_RUN_FIRST, None, (FontSet,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._set_store = SetStore()
        self._create_ui()

    def _create_ui(self):
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
        self.pack_start(scrolled, True, True, 0)

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

        toolbar = Gtk.Toolbar(icon_size=Gtk.IconSize.MENU)
        self.pack_start(toolbar, False, True, 0)

        btn_new = Gtk.ToolButton(
            label=_('Create new set'),
            icon_name='document-new')
        btn_new.set_tooltip_text(btn_new.get_label())
        btn_new.connect('clicked', self._on_new)
        toolbar.add(btn_new)

        btn_delete = Gtk.ToolButton(
            label=_('Delete set'),
            icon_name='edit-delete')
        btn_delete.set_tooltip_text(btn_delete.get_label())
        btn_delete.connect('clicked', self._on_delete)
        toolbar.add(btn_delete)

    def _toggle_cell_data_func(self, column, cell, model, tree_iter, data):
        active_fonts = model[tree_iter][SetStore.COL_NACTIVE]

        if active_fonts == 0:
            cell.props.inconsistent = False
            cell.props.active = False
        elif active_fonts == len(model[tree_iter][SetStore.COL_FONTSTORE]):
            cell.props.inconsistent = False
            cell.props.active = True
        else:
            cell.props.inconsistent = True

    def _on_selection_changed(self, selection):
        model, tree_iter = selection.get_selected()
        if not tree_iter:
            return
        self.emit('set-selected', model[tree_iter][SetStore.COL_FONTSTORE])

    def _on_toggled(self, widget, path):
        row = self._set_store[path]
        row[SetStore.COL_FONTSTORE].set_state_all(
            row[SetStore.COL_NACTIVE] < len(row[SetStore.COL_FONTSTORE]))

    def _on_name_edited(self, widget, path, text):
        new_name = text.strip()
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
        model, tree_iter = self._selection.get_selected()
        tree_iter = self._set_store.add_set(insert_after=tree_iter)

        # Start edit name right now.
        path = self._set_store.get_path(tree_iter)
        column = self._set_list.get_column(SetStore.COL_NAME)
        self._set_list.set_cursor(path, column, True)

    def _on_delete(self, button):
        model, tree_iter = self._selection.get_selected()
        if not tree_iter:
            return

        fonts = model[tree_iter][SetStore.COL_FONTSTORE]
        if len(fonts) != 0:
            set_name = model[tree_iter][SetStore.COL_NAME]
            if not dialogs.yesno(_('Delete “{}”?').format(set_name),
                                 self.get_toplevel()):
                return
            fonts.remove_fonts()

        model.remove(tree_iter)
        if len(model) == 0:
            model.add_set()
            self.selected_set = 0

    @property
    def selected_set(self):
        '''Currently selected set.'''
        return self._set_list.get_cursor()[0][0]

    @selected_set.setter
    def selected_set(self, num):
        self._set_list.set_cursor(num)

    def save_sets(self):
        font_sets = []
        for set_row in self._set_store:
            font_set = OrderedDict()
            font_set['name'] = set_row[SetStore.COL_NAME]

            fonts = []
            for font_row in set_row[SetStore.COL_FONTSTORE]:
                font = {}
                font['enabled'] = font_row[FontSet.COL_ENABLED]
                font['path'] = font_row[FontSet.COL_LINKS][0][0]
                fonts.append(font)
            font_set['fonts'] = fonts

            font_sets.append(font_set)

        try:
            with open(conf.SETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(font_sets, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load_sets(self):
        try:
            with open(conf.SETS_FILE, 'r', encoding='utf-8') as f:
                user_sets = json.load(f)

            tree_iter = None
            for user_set in user_sets:
                tree_iter = self._set_store.add_set(user_set['name'], tree_iter)
                font_set = self._set_store[tree_iter][SetStore.COL_FONTSTORE]
                font_set.add_fonts(
                    ((f['enabled'], f['path']) for f in user_set['fonts']))
        except (KeyError, ValueError, OSError):
            pass

        if len(self._set_store) == 0:
            self._set_store.add_set()
