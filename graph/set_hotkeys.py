from Qt import QtGui, QtWidgets, QtCore
import sys, os, json

from graph.db_node_support import NodeCreationDialog
from graph.model_positioning import force_forward_spring_graphs
from graph.transform_json_to_sql import transform_json
from graph.db_spec_singleton import ResourceLoader

db_spec = ResourceLoader()

# This file exists because the convenience method for doing hotkeys dies in packaged executables


def set_hotkeys(context_menu):
    rsc_path = os.path.join(getattr(sys, "_MEIPASS", os.path.abspath(".")), "resources/hotkeys.json")
    with open(rsc_path, "r") as f:
        hotkeys_list = json.load(f)
    for item in hotkeys_list:
        if item["type"] == "menu":
            hotkey_menu = context_menu.add_menu(item["label"])
            for command_info in item.get('items', []):
                if command_info["type"] == "command":
                    insert_command(command_info, hotkey_menu)
        if item["type"] == "command":
            insert_command(item, context_menu)


def insert_command(command_dict, menu=None):
    func_name = command_dict.get("function_name", None)
    if func_name is not None:
        hk_func = globals().get(func_name, False)
        if not hk_func:
            raise Exception(f"When importing hotkeys,"
                            f"Function {command_dict['function_name']} on command {command_dict.get('label', '')} did not exist.")
        shtcut = command_dict.get("shortcut", None)
        menu.add_command(name=command_dict["label"], func=hk_func, shortcut=shtcut)


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
    current = graph.current_session()
    if current:
        graph.save_session(current)
        msg = 'Session layout saved:\n{}'.format(current)
        viewer = graph.viewer()
        viewer.message_dialog(msg, title='Session Saved')
    else:
        save_session_as(graph)


def test_session(graph):
    """
    Tests the given graph against the database by converting it to SQL. During this process,
    we save it to serialise to JSON, so we can use that structure to build SQL form.
    """
    current = graph.current_session()
    if not current:
        current = 'resources/graph.json'

    graph.save_session(current)
    transform_json(current, graph.main_window)
    msg = 'Running Test in main Window'.format(current)
    viewer = graph.viewer()
    viewer.message_dialog(msg, title='Running Test')


def save_session_as(graph):
    """
    Prompts a file save dialog to serialize a session.
    """
    current = graph.current_session()
    file_path = graph.save_dialog(current)
    if file_path:
        graph.save_session(file_path)


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
    from Qt import QtCore
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
    selected_nodes = graph.selected_nodes()
    if not selected_nodes:
        graph.message_dialog('Please select a "GroupNode" to expand.')
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


def edit_antiquity_scene(graph):
    views, id_map = force_forward_spring_graphs('../../resources/antiquity-db.sqlite')
    first_view = views[0]
    for node_info in first_view['nodes']:
        node = graph.create_node('nodes.widget.DynamicFieldsNode',
                                 pos=[node_info['pos']['x'], node_info['pos']['y']])
        node.set_spec(node_info['table_name'])
        node.set_name(node_info['table_name'])

    for edge_info in first_view['edges']:
        start_table = id_map[edge_info['start_node_id']]
        end_table = id_map[edge_info['end_node_id']]
        pk = db_spec.node_templates[start_table]

    # make edges from graphs.
    # convert views (old style) into graphs





