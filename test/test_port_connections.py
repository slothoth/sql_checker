import pytest

from graph.singletons.db_spec_singleton import db_spec
db_spec.initialize(False)

from graph.node_controller import NodeEditorWindow
from utils import create_node


def test_port_updates(qtbot):
    window = NodeEditorWindow()
    qtbot.addWidget(window)
    unit = create_node(window, 'Units')
    qtbot.wait(1)
    trait_node = create_node(window, 'Traits')
    qtbot.wait(1)
    trait_node.get_widget('TraitType').set_value('TEST_TRAIT')
    qtbot.wait(1)

    trait_output_port = trait_node.outputs()['TraitType']  # connect req and effect
    unit_input_port = unit.inputs()['TraitType']
    trait_output_port.connect_to(unit_input_port)
    qtbot.wait(1)
    new_unit_value = unit.get_property('TraitType')
    assert new_unit_value == 'TEST_TRAIT'
