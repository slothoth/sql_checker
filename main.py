import sys
from PyQt5.QtWidgets import QApplication

from graph.node_controller import NodeEditorWindow

'''from NodeGraphQt.base.model import NodeModel
from NodeGraphQt.errors import NodePropertyError

def _patched_set_property(self, name, value):
    """
    Args:
        name (str): property name.
        value (object): property value.
    """
    if name in self.properties.keys():
        setattr(self, name, value)
    elif name in self._custom_prop.keys():
        self._custom_prop[name] = value
        if name == 'arg_params':            # patch somehow?
            self.reapply_arg_params()
    else:
        raise NodePropertyError('No property "{}"'.format(name))

NodeModel.set_property = _patched_set_property'''

# the pain is that we never set the custom properties on the widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NodeEditorWindow()
    window.show()
    sys.exit(app.exec())
