
from gettext import gettext as _, ngettext
from functools import wraps
from collections import OrderedDict
import json
import os

from gi.repository import Gtk, Gdk, GObject, GLib

from . import config
from .settings import settings
from . import dialogs
from . import linker
from . import font_utils
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
    # The first pair is always present and describes the main font file.
    # Others (if any) are additional files (.afm, etc.).
    COL_LINKS = 0
    COL_ENABLED = 1

    # COL_LINKABLE is True if font can be linked, i.e. it wasn't installed
    # in the system at the moment of FontLink launch.
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
        self._nactive = 0
        # Cached font names for faster filtering of existing fonts.
        self._fonts = set()

        self.set_sort_column_id(self.COL_NAME, Gtk.SortType.ASCENDING)

    @GObject.Property
    def nactive(self):
        '''Number of currently active (linked) fonts.'''
        return self._nactive

    @_watch_nactive
    def add_fonts(self, items):
        '''Add fonts to the set.

        items -- iterable of paths and/or pairs (path, state).
        '''
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
                    font_dir.startswith(config.FONTS_DIR) or
                    not os.path.isfile(path)):
                continue

            links = [
                linker.Link(path, os.path.join(config.FONTS_DIR, font_name))]

            installed = font_name in font_utils.INSTALLED_FONTS
            if installed:
                enabled = True
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

            self.append((links, enabled, not installed, font_name))
            self._fonts.add(font_name)

            if enabled:
                self._nactive += 1
                if not installed:
                    linker.create_links(links)

    @_watch_nactive
    def add_fonts_from(self, font_set):
        for row in font_set:
            font_name = row[font_set.COL_NAME]
            if font_name in self._fonts:
                continue

            self.append(row[:])
            self._fonts.add(font_name)

            if row[font_set.COL_ENABLED]:
                self._nactive += 1
                if row[font_set.COL_LINKABLE]:
                    linker.create_links(row[font_set.COL_LINKS])

    @_watch_nactive
    def remove_fonts(self, tree_paths=None):
        '''Remove fonts from the set.

        If tree_paths is None, all fonts will be removed.
        '''
        if tree_paths is None:
            for row in self:
                if row[self.COL_LINKABLE] and row[self.COL_ENABLED]:
                    linker.remove_links(row[self.COL_LINKS])
            self._fonts.clear()
            self.clear()
            self._nactive = 0
            return

        for tree_path in reversed(tree_paths):
            row = self[tree_path]
            if row[self.COL_ENABLED]:
                self._nactive -= 1
                if row[self.COL_LINKABLE]:
                    linker.remove_links(row[self.COL_LINKS])
            self._fonts.discard(row[self.COL_NAME])
            self.remove(self.get_iter(tree_path))

    def toggle_state(self, tree_path):
        row = self[tree_path]
        if not row[self.COL_LINKABLE]:
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
            if not row[self.COL_LINKABLE]:
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

    def add_set(self, name=_('New set'), insert_after=None):
        name = utils.unique_name(name, (row[self.COL_NAME] for row in self))

        font_set = FontSet()
        font_set.connect('notify::nactive', self._on_set_changed)

        return self.insert_after(insert_after, (name, font_set))

    def duplicate_set(self, tree_iter):
        name = utils.unique_name(
            self[tree_iter][self.COL_NAME],
            (row[self.COL_NAME] for row in self))

        font_set = FontSet()
        font_set.add_fonts_from(self[tree_iter][self.COL_FONTSET])
        font_set.connect('notify::nactive', self._on_set_changed)

        return self.insert_after(tree_iter, (name, font_set))

    @property
    def as_json(self):
        json_sets = []
        for set_row in self:
            fonts = []
            for font_set in set_row[self.COL_FONTSET]:
                fonts.append({
                    'enabled': font_set[FontSet.COL_ENABLED],
                    'path': font_set[FontSet.COL_LINKS][0].source
                    })
            json_sets.append(OrderedDict((
                ('name', set_row[self.COL_NAME]),
                ('fonts', fonts))))
        return json_sets

    @as_json.setter
    def as_json(self, json_sets):
        tree_iter = None
        for json_set in json_sets:
            tree_iter = self.add_set(json_set['name'], tree_iter)
            self[tree_iter][self.COL_FONTSET].add_fonts(
                ((f['path'], f['enabled']) for f in json_set['fonts']))


class FontList(Gtk.Grid):

    class _PathAction:
        OPEN = 0
        OPEN_DIR = 1
        COPY = 2

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._create_ui()

    def _create_ui(self):
        self._font_list = Gtk.TreeView(
            fixed_height_mode=True,
            headers_visible=False,
            rubber_banding=True,
            has_tooltip=True)
        self._font_list.connect('button-press-event', self._on_button_press)
        self._font_list.connect('query-tooltip', self._on_query_tooltip)
        self._font_list.connect('row-activated', self._on_row_activated)

        selection = self._font_list.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        scrolled = Gtk.ScrolledWindow(
            shadow_type=Gtk.ShadowType.IN,
            width_request=200,
            expand=True
            )
        scrolled.add(self._font_list)
        self.add(scrolled)

        # Columns

        toggle = Gtk.CellRendererToggle()
        toggle.connect('toggled', self._on_toggled)
        col_toggle = Gtk.TreeViewColumn(
            '', toggle,
            active=FontSet.COL_ENABLED,
            activatable=FontSet.COL_LINKABLE
            )
        col_toggle.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self._font_list.append_column(col_toggle)

        name = Gtk.CellRendererText()
        col_name = Gtk.TreeViewColumn(
            _('Fonts'), name,
            text=FontSet.COL_NAME,
            sensitive=FontSet.COL_LINKABLE
            )
        col_name.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col_name.set_sort_column_id(FontSet.COL_NAME)
        self._font_list.append_column(col_name)

        # Toolbar

        toolbar = Gtk.Toolbar(icon_size=Gtk.IconSize.SMALL_TOOLBAR)
        toolbar.get_style_context().add_class('bottom-toolbar')
        self.add(toolbar)

        btn_add = Gtk.ToolButton(
            label=_('Add…'),
            icon_name='list-add',
            tooltip_text=_('Add fonts'))
        btn_add.connect('clicked', self._on_add)
        toolbar.add(btn_add)

        btn_remove = Gtk.ToolButton(
            label=_('Remove'),
            icon_name='list-remove',
            tooltip_text=_('Remove selected fonts'))
        btn_remove.connect('clicked', self._on_remove)
        selection.connect(
            'changed',
            lambda s: btn_remove.set_sensitive(s.count_selected_rows() > 0))
        toolbar.add(btn_remove)

        btn_clear = Gtk.ToolButton(
            label=_('Remove All'),
            icon_name='edit-clear',
            tooltip_text=_('Remove all fonts'),
            sensitive=False)
        btn_clear.connect('clicked', self._on_clear)
        self._btn_clear = btn_clear
        toolbar.add(btn_clear)

    def _on_button_press(self, widget, event):
        if event.type != Gdk.EventType.BUTTON_PRESS:
            return Gdk.EVENT_PROPAGATE

        self._font_list.grab_focus()

        selection = self._font_list.get_selection()

        click_info = self._font_list.get_path_at_pos(
            int(event.x), int(event.y))
        if click_info is None:
            selection.unselect_all()
        elif event.button == Gdk.BUTTON_SECONDARY:
            tree_path, column, cell_x, cell_y = click_info
            if not selection.path_is_selected(tree_path):
                self._font_list.set_cursor(tree_path, column, False)

        if event.button != Gdk.BUTTON_SECONDARY:
            return Gdk.EVENT_PROPAGATE

        menu = Gtk.Menu(attach_widget=widget)

        mi_add = Gtk.MenuItem(
            label=_('_Add…'),
            use_underline=True,
            tooltip_text=_('Add fonts')
            )
        mi_add.connect('activate', self._on_add)
        menu.append(mi_add)

        menu.append(Gtk.SeparatorMenuItem())

        mi_open = Gtk.MenuItem(
            label=_('_Open'),
            use_underline=True,
            tooltip_text=_('Open font')
            )
        mi_open.connect(
            'activate', self._on_path_action, self._PathAction.OPEN)
        menu.append(mi_open)

        mi_open_dir = Gtk.MenuItem(
            label=_('Open _Folder'),
            use_underline=True,
            tooltip_text=_('Open font folder')
            )
        mi_open_dir.connect(
            'activate', self._on_path_action, self._PathAction.OPEN_DIR)
        menu.append(mi_open_dir)

        mi_copy_path = Gtk.MenuItem(
            label=_('Copy _Path'),
            use_underline=True,
            tooltip_text=_('Copy font path to clipboard')
            )
        mi_copy_path.connect(
            'activate', self._on_path_action, self._PathAction.COPY)
        menu.append(mi_copy_path)

        menu.append(Gtk.SeparatorMenuItem())

        mi_remove = Gtk.MenuItem(
            label=_('_Remove'),
            use_underline=True,
            tooltip_text=_('Remove selected fonts')
            )
        mi_remove.connect('activate', self._on_remove)
        menu.append(mi_remove)

        mi_clear = Gtk.MenuItem(
            label=_('R_emove All'),
            use_underline=True,
            tooltip_text=_('Remove all fonts')
            )
        mi_clear.connect('activate', self._on_clear)
        menu.append(mi_clear)

        num_selected = selection.count_selected_rows()
        if num_selected != 1:
            mi_open.set_sensitive(False)
            mi_open_dir.set_sensitive(False)
            mi_copy_path.set_sensitive(False)
        if num_selected == 0:
            mi_remove.set_sensitive(False)
        font_set = self._font_list.get_model()
        if font_set is None or len(font_set) == 0:
            mi_clear.set_sensitive(False)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

        return Gdk.EVENT_STOP

    def _on_query_tooltip(self, tree_view, x, y, keyboard_tip, tooltip):
        points_to_row, *context = tree_view.get_tooltip_context(
            x, y, keyboard_tip)
        if not points_to_row:
            return False

        font_set, tree_path, tree_iter = context[2:]
        row = font_set[tree_iter]

        font_path = row[FontSet.COL_LINKS][0].source
        font_dir, font_name = os.path.split(font_path)
        if font_name in font_utils.INSTALLED_FONTS:
            text = '{}\n<b>{}</b>\n{}'.format(
                font_path,
                _('Already installed in:'),
                font_utils.INSTALLED_FONTS[font_name])
        else:
            text = font_path

        tooltip.set_markup(text)
        tree_view.set_tooltip_row(tooltip, tree_path)
        return True

    def _on_add(self, widget):
        font_set = self._font_list.get_model()
        if font_set is None:
            return

        paths = dialogs.open_fonts(self.get_toplevel())
        if not paths:
            return
        font_set.add_fonts(paths)
        self._btn_clear.set_sensitive(len(font_set) > 0)

    def _on_path_action(self, widget, action):
        selection = self._font_list.get_selection()
        font_set, tree_paths = selection.get_selected_rows()
        if font_set is None or not tree_paths:
            return

        path = font_set[tree_paths[0]][FontSet.COL_LINKS][0].source

        if action == self._PathAction.COPY:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(path, -1)
        else:
            if action == self._PathAction.OPEN_DIR:
                path = os.path.dirname(path)
            Gtk.show_uri(None, GLib.filename_to_uri(path), Gdk.CURRENT_TIME)

    def _on_remove(self, widget):
        selection = self._font_list.get_selection()
        font_set, tree_paths = selection.get_selected_rows()
        if font_set is None or not tree_paths:
            return

        num_selected = len(tree_paths)
        if num_selected == 1:
            message = _('Remove “{font_name}” from the set?').format(
                font_name=font_set[tree_paths[0]][FontSet.COL_NAME])
        else:
            message = ngettext(
                'Remove {num} selected font from the set?',
                'Remove {num} selected fonts from the set?',
                num_selected).format(num=num_selected)

        if dialogs.confirmation(
                self.get_toplevel(),
                message,
                _('_Remove')):
            font_set.remove_fonts(tree_paths)
            self._btn_clear.set_sensitive(len(font_set) > 0)

    def _on_toggled(self, cell_toggle, tree_path):
        font_set = self._font_list.get_model()
        font_set.toggle_state(tree_path)

    def _on_clear(self, widget):
        font_set = self._font_list.get_model()
        if (font_set is not None and
                dialogs.confirmation(
                    self.get_toplevel(),
                    _('Remove all fonts from the set?'),
                    _('_Remove')
                    )):
            font_set.remove_fonts()
            self._btn_clear.set_sensitive(False)

    def _on_row_activated(self, font_list, tree_path, column):
        if column == font_list.get_column(1):
            font_set = font_list.get_model()
            Gtk.show_uri(
                None,
                GLib.filename_to_uri(
                    font_set[tree_path][FontSet.COL_LINKS][0].source),
                Gdk.CURRENT_TIME)

    @property
    def font_set(self):
        return self._font_list.get_model()

    @font_set.setter
    def font_set(self, font_set):
        self._font_list.set_model(font_set)
        if font_set is not None:
            self._font_list.set_search_column(FontSet.COL_NAME)
            self._btn_clear.set_sensitive(len(font_set) > 0)


class FontLib(Gtk.Paned):

    _FILE = os.path.join(config.CONFIG_DIR, 'sets.json')

    def __init__(self):
        super().__init__()
        self._set_store = SetStore()
        self._font_list = FontList()
        self._create_ui()

    def _create_ui(self):
        grid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)

        self._set_list = Gtk.TreeView(
            model=self._set_store,
            headers_visible=False,
            reorderable=True,
            search_column=SetStore.COL_NAME,
            has_tooltip=True)
        self._set_list.connect('button-press-event', self._on_button_press)
        self._set_list.connect('query-tooltip', self._on_query_tooltip)

        selection = self._set_list.get_selection()
        selection.set_mode(Gtk.SelectionMode.BROWSE)
        selection.connect('changed', self._on_selection_changed)

        scrolled = Gtk.ScrolledWindow(
            shadow_type=Gtk.ShadowType.IN,
            width_request=150,
            expand=True
            )
        scrolled.add(self._set_list)
        grid.add(scrolled)

        # Columns

        toggle = Gtk.CellRendererToggle()
        toggle.connect('toggled', self._on_toggled)
        col_toggle = Gtk.TreeViewColumn('', toggle)
        col_toggle.set_cell_data_func(toggle, self._toggle_cell_data_func)
        self._set_list.append_column(col_toggle)

        name = Gtk.CellRendererText(editable=True)
        name.connect('edited', self._on_name_edited)
        col_name = Gtk.TreeViewColumn(
            _('Font sets'), name, text=SetStore.COL_NAME)
        col_name.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self._set_list.append_column(col_name)

        # Toolbar

        toolbar = Gtk.Toolbar(icon_size=Gtk.IconSize.SMALL_TOOLBAR)
        toolbar.get_style_context().add_class('bottom-toolbar')
        grid.add(toolbar)

        btn_new = Gtk.ToolButton(
            label=_('New'),
            icon_name='document-new',
            tooltip_text=_('Create a new set'))
        btn_new.connect('clicked', self._on_new)
        toolbar.add(btn_new)

        btn_delete = Gtk.ToolButton(
            label=_('Delete'),
            icon_name='edit-delete',
            tooltip_text=_('Delete the set'))
        btn_delete.connect('clicked', self._on_delete)
        toolbar.add(btn_delete)

        self.pack1(grid, False, False)
        self.pack2(self._font_list, True, False)

    def _on_button_press(self, widget, event):
        if not (event.type == Gdk.EventType.BUTTON_PRESS and
                event.button == Gdk.BUTTON_SECONDARY):
            return Gdk.EVENT_PROPAGATE

        self._set_list.grab_focus()

        click_info = self._set_list.get_path_at_pos(int(event.x), int(event.y))
        if click_info is not None:
            tree_path, column, cell_x, cell_y = click_info
            self._set_list.set_cursor(tree_path, column, False)

        menu = Gtk.Menu(attach_widget=widget)

        mi_new = Gtk.MenuItem(
            label=_('_New'),
            use_underline=True,
            tooltip_text=_('Create a new set')
            )
        mi_new.connect('activate', self._on_new)
        menu.append(mi_new)

        menu.append(Gtk.SeparatorMenuItem())

        mi_duplicate = Gtk.MenuItem(
            label=_('D_uplicate'),
            use_underline=True,
            tooltip_text=_('Duplicate the set')
            )
        mi_duplicate.connect('activate', self._on_duplicate)
        menu.append(mi_duplicate)

        mi_rename = Gtk.MenuItem(
            label=_('_Rename…'),
            use_underline=True,
            tooltip_text=_('Rename the set')
            )
        mi_rename.connect('activate', self._on_rename)
        menu.append(mi_rename)

        menu.append(Gtk.SeparatorMenuItem())

        mi_delete = Gtk.MenuItem(
            label=_('_Delete'),
            use_underline=True,
            tooltip_text=_('Delete the set')
            )
        mi_delete.connect('activate', self._on_delete)
        menu.append(mi_delete)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

        return Gdk.EVENT_STOP

    def _on_query_tooltip(self, tree_view, x, y, keyboard_tip, tooltip):
        points_to_row, *context = tree_view.get_tooltip_context(
            x, y, keyboard_tip)
        if not points_to_row:
            return False

        set_store, tree_path, tree_iter = context[2:]
        font_set = set_store[tree_iter][SetStore.COL_FONTSET]
        num_fonts = len(font_set)

        text = ngettext('{num} font', '{num} fonts', num_fonts).format(
            num=num_fonts)
        if num_fonts > 0:
            text = '{}\n{}'.format(
                text,
                # Translators: Number of active fonts
                ngettext('{num} active', '{num} active',
                         font_set.nactive).format(num=font_set.nactive))

        tooltip.set_text(text)
        tree_view.set_tooltip_row(tooltip, tree_path)
        return True

    def _toggle_cell_data_func(self, column, cell, set_store, tree_iter, data):
        font_set = set_store[tree_iter][SetStore.COL_FONTSET]

        if font_set.nactive == 0:
            cell.props.inconsistent = False
            cell.props.active = False
        elif font_set.nactive == len(font_set):
            cell.props.inconsistent = False
            cell.props.active = True
        else:
            cell.props.inconsistent = True

    def _on_selection_changed(self, selection):
        set_store, tree_iter = selection.get_selected()
        if tree_iter is None:
            return
        self._font_list.font_set = set_store[tree_iter][SetStore.COL_FONTSET]

    def _on_toggled(self, cell_toggle, tree_path):
        font_set = self._set_store[tree_path][SetStore.COL_FONTSET]
        font_set.set_state_all(font_set.nactive < len(font_set))

    def _on_name_edited(self, cell_text, tree_path, new_name):
        new_name = new_name.strip()
        if not new_name:
            return

        old_name = self._set_store[tree_path][SetStore.COL_NAME]
        if new_name == old_name:
            return

        all_names = set(row[SetStore.COL_NAME] for row in self._set_store)
        all_names.discard(old_name)
        new_name = utils.unique_name(new_name, all_names)
        self._set_store[tree_path][SetStore.COL_NAME] = new_name

    def _on_new(self, widget):
        selection = self._set_list.get_selection()
        set_store, tree_iter = selection.get_selected()

        tree_iter = set_store.add_set(insert_after=tree_iter)

        tree_path = set_store.get_path(tree_iter)
        column = self._set_list.get_column(1)
        self._set_list.set_cursor(tree_path, column, True)

    def _on_duplicate(self, widget):
        selection = self._set_list.get_selection()
        set_store, tree_iter = selection.get_selected()
        if tree_iter is None:
            return

        tree_iter = set_store.duplicate_set(tree_iter)

        tree_path = set_store.get_path(tree_iter)
        self._set_list.set_cursor(tree_path, None, False)

    def _on_rename(self, widget):
        selection = self._set_list.get_selection()
        set_store, tree_iter = selection.get_selected()
        if tree_iter is None:
            return

        tree_path = set_store.get_path(tree_iter)
        column = self._set_list.get_column(1)
        self._set_list.set_cursor(tree_path, column, True)

    def _on_delete(self, widget):
        selection = self._set_list.get_selection()
        set_store, tree_iter = selection.get_selected()
        if tree_iter is None:
            return

        row = set_store[tree_iter]
        if not dialogs.confirmation(
                self.get_toplevel(),
                _('Delete “{set_name}”?').format(
                    set_name=row[SetStore.COL_NAME]),
                _('_Delete')):
            return

        row[SetStore.COL_FONTSET].remove_fonts()
        set_store.remove(tree_iter)
        if len(set_store) == 0:
            set_store.add_set()
            self._set_list.set_cursor(0)

    def add_fonts(self, paths):
        '''Add fonts to the currently selected set.'''
        font_set = self._font_list.font_set
        if font_set is not None:
            font_set.add_fonts(paths)

    def save_state(self):
        settings['splitter_position'] = self.get_position()

        settings['selected_set'] = self._set_list.get_cursor()[0][0] + 1
        try:
            with open(self._FILE, 'w', encoding='utf-8') as f:
                json.dump(
                    self._set_store.as_json, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load_state(self):
        self.set_position(
            settings.get('splitter_position', self.get_position()))

        try:
            with open(self._FILE, 'r', encoding='utf-8') as f:
                self._set_store.as_json = json.load(f)
        except (KeyError, ValueError, OSError):
            pass

        if len(self._set_store) == 0:
            self._set_store.add_set()

        tree_path = max(0, settings.get('selected_set', 1) - 1)
        self._set_list.set_cursor(tree_path)
        self._set_list.scroll_to_cell(tree_path, None, False, 0, 0)
