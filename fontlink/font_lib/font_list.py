
from gettext import gettext as _, ngettext
import os

from gi.repository import Gtk, Gdk, GLib

from .. import dialogs
from .. import font_utils
from .models import FontSet


class FontList(Gtk.Grid):

    class _ViewColumn:
        TOGGLE = 0
        NAME = 1

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
            tooltip_text=_('Copy paths of the selected fonts to clipboard')
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
        if num_selected == 0:
            mi_remove.set_sensitive(False)
            mi_copy_path.set_sensitive(False)
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
        font_name = row[FontSet.COL_NAME]
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

    def _on_path_action(self, widget, path_action):
        selection = self._font_list.get_selection()
        font_set, tree_paths = selection.get_selected_rows()
        if font_set is None or not tree_paths:
            return

        if path_action == self._PathAction.COPY:
            paths = []
            for tree_path in tree_paths:
                paths.append(font_set[tree_path][FontSet.COL_LINKS][0].source)

            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text('\n'.join(paths), -1)
        else:
            path = font_set[tree_paths[0]][FontSet.COL_LINKS][0].source

            if path_action == self._PathAction.OPEN_DIR:
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
        if column == font_list.get_column(self._ViewColumn.NAME):
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
