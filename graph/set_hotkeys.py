from PyQt5 import QtGui, QtWidgets, QtCore
import sys, os, json, shutil

from graph.db_node_support import NodeCreationDialog
from graph.transform_json_to_sql import transform_json, make_modinfo
from schema_generator import check_valid_sql_against_db
from graph.db_spec_singleton import db_spec

# This file exists because the convenience method for doing hotkeys dies in packaged executables


def set_hotkeys(window, menubar):
    context_menu = window.graph.get_context_menu('graph')
    rsc_path = os.path.join(getattr(sys, "_MEIPASS", os.path.abspath(".")), "resources/hotkeys.json")
    with open(rsc_path, "r") as f:
        hotkeys_list = json.load(f)
    for item in hotkeys_list:
        if item["type"] == "menu":
            hotkey_menu = context_menu.add_menu(item["label"])
            menu_bar_category = menubar.addMenu(item["label"])
            for command_info in item.get('items', []):
                if command_info["type"] == "command":
                    insert_command(command_info, hotkey_menu, menu_bar_category, window=window)

        if item["type"] == "command":
            insert_command(item, context_menu)


def insert_command(command_dict, menu=None, menu_bar_folder=None, window=None):
    func_name = command_dict.get("function_name", None)
    if func_name is not None:
        hk_func = globals().get(func_name, False)
        if not hk_func:
            raise Exception(f"When importing hotkeys,"
                            f"Function {command_dict['function_name']} on command {command_dict.get('label', '')} did not exist.")
        shtcut = command_dict.get("shortcut", None)
        menu.add_command(name=command_dict["label"], func=hk_func, shortcut=shtcut)
        if menu_bar_folder is not None:
            action_ = GraphMenuAction(command_dict["label"], window.graph, window)
            action_.executed.connect(hk_func)
            menu_bar_folder.addAction(action_)


class GraphMenuAction(QtWidgets.QAction):
    executed = QtCore.pyqtSignal(object)

    def __init__(self, text, graph, parent=None):
        super().__init__(text, parent)
        self.graph = graph
        self.triggered.connect(self._on_triggered)

    def _on_triggered(self):
        self.executed.emit(self.graph)


def zoom_in(graph):
    """
    Set the node graph to zoom in by 0.1
    """
    zoom = graph.get_zoom() + 0.1
    graph.set_zoom(zoom)


def zoom_out(graph):
    """
    Set the node graph to zoom in by 0.1
    """
    zoom = graph.get_zoom() - 0.2
    graph.set_zoom(zoom)


def reset_zoom(graph):
    """
    Reset zoom level.
    """
    graph.reset_zoom()


def layout_h_mode(graph):
    """
    Set node graph layout direction to horizontal.
    """
    graph.set_layout_direction(0)


def layout_v_mode(graph):
    """
    Set node graph layout direction to vertical.
    """
    graph.set_layout_direction(1)


def open_session(graph):
    """
    Prompts a file open dialog to load a session.
    """
    current = graph.current_session()
    file_path = graph.load_dialog(current)
    if file_path:
        graph.load_session(file_path)


def import_session(graph):
    """
    Prompts a file open dialog to load a session.
    """
    current = graph.current_session()
    file_path = graph.load_dialog(current)
    if file_path:
        graph.import_session(file_path)


def save_session(graph):
    """
    Prompts a file save dialog to serialize a session if required.
    """
    from graph.windows import Toast
    current = graph.current_session()
    if current:
        # we should format any custom nodes extra params
        custom_save(graph, current)
        msg = 'Session layout saved:\n{}'.format(current)
        t = Toast(msg)
        t.show_at_bottom_right()
    else:
        save_session_as(graph)


def save_session_as(graph):
    """
    Prompts a file save dialog to serialize a session.
    """
    current = graph.current_session()
    file_path = graph.save_dialog(current)
    if file_path:
        custom_save(graph, file_path)


def custom_save(graph, file_path):
    graph_migrated_params = {}
    graph_nodes = graph.all_nodes()
    for idx, node in enumerate(graph_nodes):
        migrated_params = node.migrate_extra_params()
        graph_migrated_params[idx] = migrated_params
    graph.save_session(file_path)
    for idx, params in graph_migrated_params.items():
        graph_nodes[idx].restore_extra_params(params)


def clear_session(graph):
    """
    Prompts a warning dialog to new a node graph session.
    """
    if graph.question_dialog('Clear Current Session?', 'Clear Session'):
        graph.clear_session()


def quit_qt(graph):
    """
    Quit the Qt application.
    """
    from PyQt5 import QtCore
    QtCore.QCoreApplication.quit()


def clear_undo(graph):
    """
    Prompts a warning dialog to clear undo.
    """
    viewer = graph.viewer()
    msg = 'Clear all undo history, Are you sure?'
    if viewer.question_dialog('Clear Undo History', msg):
        graph.clear_undo_stack()


def copy_nodes(graph):
    """
    Copy nodes to the clipboard.
    """
    graph.copy_nodes()


def cut_nodes(graph):
    """
    Cut nodes to the clip board.
    """
    graph.cut_nodes()


def paste_nodes(graph):
    """
    Pastes nodes copied from the clipboard.
    """
    # by default the graph will inherite the global style
    # from the graph when pasting nodes.
    # to disable this behaviour set `adjust_graph_style` to False.
    graph.paste_nodes(adjust_graph_style=False)


def delete_nodes_and_pipes(graph):
    """
    Delete selected nodes and connections.
    """
    graph.delete_nodes(graph.selected_nodes())
    for pipe in graph.selected_pipes():
        pipe[0].disconnect_from(pipe[1])


def extract_nodes(graph):
    """
    Extract selected nodes.
    """
    graph.extract_nodes(graph.selected_nodes())


def clear_node_connections(graph):
    """
    Clear port connection on selected nodes.
    """
    graph.undo_stack().beginMacro('clear selected node connections')
    for node in graph.selected_nodes():
        for port in node.input_ports() + node.output_ports():
            port.clear_connections()
    graph.undo_stack().endMacro()


def select_all_nodes(graph):
    """
    Select all nodes.
    """
    graph.select_all()


def clear_node_selection(graph):
    """
    Clear node selection.
    """
    graph.clear_selection()


def invert_node_selection(graph):
    """
    Invert node selection.
    """
    graph.invert_selection()


def disable_nodes(graph):
    """
    Toggle disable on selected nodes.
    """
    graph.disable_nodes(graph.selected_nodes())


def duplicate_nodes(graph):
    """
    Duplicated selected nodes.
    """
    graph.duplicate_nodes(graph.selected_nodes())


def expand_group_node(graph):
    """
    Expand selected group node.
    """
    from graph.windows import Toast
    selected_nodes = graph.selected_nodes()
    if not selected_nodes:
        t = Toast('Please select a "GroupNode" to expand.')
        t.show_at_bottom_right()
        return
    graph.expand_group_node(selected_nodes[0])


def fit_to_selection(graph):
    """
    Sets the zoom level to fit selected nodes.
    """
    graph.fit_to_selection()


def show_undo_view(graph):
    """
    Show the undo list widget.
    """
    graph.undo_view.show()


def curved_pipe(graph):
    """
    Set node graph pipes layout as curved.
    """
    from NodeGraphQt.constants import PipeLayoutEnum
    graph.set_pipe_style(PipeLayoutEnum.CURVED.value)


def straight_pipe(graph):
    """
    Set node graph pipes layout as straight.
    """
    from NodeGraphQt.constants import PipeLayoutEnum
    graph.set_pipe_style(PipeLayoutEnum.STRAIGHT.value)


def angle_pipe(graph):
    """
    Set node graph pipes layout as angled.
    """
    from NodeGraphQt.constants import PipeLayoutEnum
    graph.set_pipe_style(PipeLayoutEnum.ANGLE.value)


def bg_grid_none(graph):
    """
    Turn off the background patterns.
    """
    from NodeGraphQt.constants import ViewerEnum
    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)


def bg_grid_dots(graph):
    """
    Set background node graph background with grid dots.
    """
    from NodeGraphQt.constants import ViewerEnum
    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_DOTS.value)


def bg_grid_lines(graph):
    """
    Set background node graph background with grid lines.
    """
    from NodeGraphQt.constants import ViewerEnum
    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_LINES.value)


def layout_graph_down(graph):
    """
    Auto layout the nodes down stream.
    """
    nodes = graph.selected_nodes() or graph.all_nodes()
    graph.auto_layout_nodes(nodes=nodes, down_stream=True)


def layout_graph_up(graph):
    """
    Auto layout the nodes up stream.
    """
    nodes = graph.selected_nodes() or graph.all_nodes()
    graph.auto_layout_nodes(nodes=nodes, down_stream=False)


def toggle_node_search(graph):
    """
    show/hide the node search widget.
    """
    graph.toggle_node_search()


def _node_from_graphics_items(items):
    for it in items:
        cur = it
        # walk up the parent chain trying to find an object that references a node
        while cur is not None:
            # common NodeGraphQt graphics objects often expose .node or ._node or .get_node()
            node = getattr(cur, "node", None) or getattr(cur, "_node", None)
            if node is not None:
                return node
            get_node = getattr(cur, "get_node", None)
            if callable(get_node):
                try:
                    n = get_node()
                    if n is not None:
                        return n
                except Exception:
                    pass
            # check python-friendly attributes that may hold a node reference
            for attr in ("_base_node", "base_node", "parent_node"):
                node = getattr(cur, attr, None)
                if node is not None:
                    return node
            cur = cur.parentItem()
    return None


def delete_node_at_cursor(graph):
    viewer = graph.viewer()
    scene_pos = viewer.mapToScene(viewer.mapFromGlobal(QtGui.QCursor.pos()))
    scene = viewer.scene()
    items = scene.items(scene_pos)
    node = _node_from_graphics_items(items)
    if node is None:
        return
    try:
        graph.delete_node(node)
    except Exception:
        # fallback: if node is a graphics wrapper that exposes .node() or .get_node(), try to resolve then delete
        try:
            node_obj = node.node() if callable(getattr(node, "node", None)) else getattr(node, "get_node", lambda: None)()
            if node_obj:
                graph.delete_node(node_obj)
        except Exception:
            pass


def install_delete_at_cursor_shortcut(graph):
    viewer = graph.viewer()
    target = viewer  # or viewer.viewport()

    for seq in ('Delete', 'Backspace'):
        sc = QtWidgets.QShortcut(QtGui.QKeySequence(seq), target)
        sc.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        sc.activated.connect(lambda g=graph: delete_node_at_cursor(g))


def create_dynamic_node_with_search(graph):
    dialog = NodeCreationDialog()
    viewer = graph.viewer()
    pos = viewer.mapToGlobal(QtGui.QCursor.pos())
    dialog.move(pos)

    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return

    name = dialog.selected()
    if not name:
        return

    scene_pos = viewer.mapToScene(viewer.mapFromGlobal(pos))

    class_name = f"{name.title().replace('_', '')}Node"
    node = graph.create_node(f'db.table.{name.lower()}.{class_name}', pos=[scene_pos.x(), scene_pos.y()])


def create_modifier_game_effects(graph):
    viewer = graph.viewer()
    pos = viewer.mapToGlobal(QtGui.QCursor.pos())
    scene_pos = viewer.mapToScene(viewer.mapFromGlobal(pos))
    node = graph.create_node('db.game_effects.GameEffectNode', pos=[scene_pos.x(), scene_pos.y()])


def create_requirement_game_effects(graph):
    viewer = graph.viewer()
    pos = viewer.mapToGlobal(QtGui.QCursor.pos())
    scene_pos = viewer.mapToScene(viewer.mapFromGlobal(pos))
    node = graph.create_node('db.game_effects.RequirementEffectNode', pos=[scene_pos.x(), scene_pos.y()])


def test_session(graph):
    """
    Tests the given graph against the database by converting it to SQL. During this process,
    we save it to serialise to JSON, so we can use that structure to build SQL form.
    """
    current = graph.current_session() or 'resources/graph.json'
    graph.save_session(current)
    sql_lines = transform_json(current)
    # save SQL, then trigger main run model
    write_sql(sql_lines)
    age = graph.property('meta').get('Age')
    push_to_log(graph, f'Testing mod for: {age}')
    data = check_valid_sql_against_db(age, sql_lines)
    extract_state_test(graph, data)
    # make the collapsible panel be shown


def save_session_to_mod(graph, parent=None):
    """
    Saves the session, converts to SQL, and packages into a new folder with a template .modinfo
    with a unique uuid? For this i assume we will need to
    """
    from graph.windows import Toast
    current = graph.current_session()
    if not current:
        current = 'resources/graph.json'

    graph.save_session(current)
    sql_lines = transform_json(current)
    write_sql(sql_lines)

    # if local mod dir exists, use that
    base_home = os.path.expanduser("~")
    civ_mods_path = db_spec.civ_config + '/Mods'
    if not os.path.exists(civ_mods_path):
        civ_mods_path = QtWidgets.QFileDialog.getExistingDirectory(
            parent,
            "Select Save Location",
            "",
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if not civ_mods_path:
            return

    template, mod_name = make_modinfo(graph)
    target = os.path.join(civ_mods_path, mod_name)
    os.makedirs(target, exist_ok=True)

    shutil.copy('resources/main.sql', os.path.join(target, "main.sql"))

    with open(os.path.join(target, f"{mod_name}.modinfo"), "w", encoding="utf-8") as f:
        f.write(template)
    t = Toast(f'Saved Mod to mods folder {target}')
    t.show_at_bottom_right()


def import_mod(graph):
    """
    Prompts a file open dialog to load an existing mod folder.
    """
    from PyQt5.QtWidgets import QFileDialog
    from PyQt5.QtCore import QUrl
    from graph.mod_conversion import build_imported_mod
    from graph.windows import Toast

    dlg = QFileDialog(graph.viewer(), "Select Folder")
    dlg.setFileMode(QFileDialog.Directory)
    dlg.setOption(QFileDialog.ShowDirsOnly, True)
    mod_dir = db_spec.civ_config + '/Mods'
    dlg.setDirectoryUrl(QUrl.fromLocalFile(mod_dir))
    dlg.exec()
    path = dlg.selectedFiles()[0] if dlg.selectedFiles() else None
    if path is not None:
        mod_info_found = build_imported_mod(path, graph)
        if mod_info_found is not None:
            layout_graph_down(graph)
            graph.auto_layout_nodes()           # layout centre
            graph.select_all()
            graph.fit_to_selection()
            graph.clear_selection()
            t = Toast('Finished loading Mod')
            t.show_at_bottom_right()
        else:
            t = Toast(f'No Modinfo found in folder {path}, or age not set.')
            t.show_at_bottom_right()


def open_settings(graph):
    from graph.windows import MetadataDialog
    dialog = MetadataDialog(graph, graph.viewer())

    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return None


def write_sql(sql_lines):
    # save SQL, then trigger main run model
    with open('resources/main.sql', 'w') as f:
        f.writelines(sql_lines)


def extract_state_test(graph, data):
    if data.get('fk_error_explanations') is not None:
        for tuple_key, val in data['fk_error_explanations']['title_errors'].items():
            push_to_log(graph, val)
            for error_list in data['fk_error_explanations']['bad_commands'][tuple_key]:
                for error in error_list:
                    push_to_log(graph, error)            # instead we should use red highlight on bad entries and cols
    else:
        push_to_log(graph, 'Valid mod setup')


def push_to_log(graph, message):
    log_display = graph.side_panel.log_display
    log_display.appendPlainText(str(message))  # ensure plain text insertion so the highlighter can run
    cursor = log_display.textCursor()  # keep view scrolled to bottom
    log_display.setTextCursor(cursor)
