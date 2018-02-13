
from gettext import gettext as _, ngettext
import json
import os

from gi.repository import Gtk, Gdk, Pango

from .. import config
from ..settings import settings
from .. import dialogs
from .. import utils
from .models import SetStore
from .font_list import FontList


class FontLib(Gtk.Paned):

    _FILE = os.path.join(config.CONFIG_DIR, 'sets.json')
    _DEFAULT_SET_NAME = _('New set')

    class _ViewColumn:
        TOGGLE = 0
        NAME = 1
        STATS = 2

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

        name = Gtk.CellRendererText(
            editable=True,
            ellipsize=Pango.EllipsizeMode.END
            )
        name.connect('edited', self._on_name_edited)
        col_name = Gtk.TreeViewColumn(
            _('Font sets'), name, text=SetStore.COL_NAME)
        col_name.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        col_name.set_expand(True)
        self._set_list.append_column(col_name)

        stats = Gtk.CellRendererText(xalign=1.0)
        col_stats = Gtk.TreeViewColumn('', stats)
        col_stats.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        col_stats.set_cell_data_func(stats, self._stats_cell_data_func)
        self._set_list.append_column(col_stats)

        # Toolbar

        toolbar = Gtk.Toolbar()
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
                         font_set.num_active).format(num=font_set.num_active))

        tooltip.set_text(text)
        tree_view.set_tooltip_row(tooltip, tree_path)
        return True

    def _toggle_cell_data_func(self, column, cell, set_store, tree_iter, data):
        font_set = set_store[tree_iter][SetStore.COL_FONTSET]

        if font_set.num_active == 0:
            cell.props.inconsistent = False
            cell.props.active = False
        elif font_set.num_active == len(font_set):
            cell.props.inconsistent = False
            cell.props.active = True
        else:
            cell.props.inconsistent = True

    def _stats_cell_data_func(self, column, cell, set_store, tree_iter, data):
        font_set = set_store[tree_iter][SetStore.COL_FONTSET]
        cell.props.text = '{}/{}'.format(font_set.num_active, len(font_set))

    def _on_selection_changed(self, selection):
        set_store, tree_iter = selection.get_selected()
        if tree_iter is None:
            return
        self._font_list.font_set = set_store[tree_iter][SetStore.COL_FONTSET]

    def _on_toggled(self, cell_toggle, tree_path):
        font_set = self._set_store[tree_path][SetStore.COL_FONTSET]
        font_set.set_state_all(font_set.num_active < len(font_set))

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

        tree_iter = set_store.add_set(self._DEFAULT_SET_NAME, tree_iter)

        tree_path = set_store.get_path(tree_iter)
        column = self._set_list.get_column(self._ViewColumn.NAME)
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
        column = self._set_list.get_column(self._ViewColumn.NAME)
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

        row[SetStore.COL_FONTSET].remove_all_fonts()
        set_store.remove(tree_iter)
        if len(set_store) == 0:
            set_store.add_set(self._DEFAULT_SET_NAME)
            self._set_list.set_cursor(0)

    def add_fonts(self, paths):
        """Add fonts to the currently selected set."""
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
            self._set_store.add_set(self._DEFAULT_SET_NAME)

        tree_path = max(0, settings.get('selected_set', 1) - 1)
        self._set_list.set_cursor(tree_path)
        self._set_list.scroll_to_cell(tree_path, None, False, 0, 0)
