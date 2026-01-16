from graph.db_node_support import sync_node_options
from graph.db_spec_singleton import db_spec

import logging

log = logging.getLogger(__name__)


def port_connect_transmit(input_port, output_port):
    input_name, output_name = input_port.name(), output_port.name()
    input_node, output_node = input_port.node(), output_port.node()
    input_widget = input_node.get_widget(input_name)
    current_input_value = input_node.get_property(input_name) if input_widget is None else input_widget.get_value()
    output_widget = output_node.get_widget(output_name)
    current_output_value = output_node.get_property(output_name) if output_widget is None else output_widget.get_value()
    if current_input_value == current_output_value:
        return
    else:
        changing_node, new_value = None, None
        if current_input_value == '' or current_input_value is None:            # change input to match output
            changing_node = input_node
            changing_name = input_name
            new_value = current_output_value
        elif current_output_value == '' or current_output_value is None:        # change output to match input
            changing_node = output_node
            changing_name = output_name
            new_value = current_input_value
        else:                               # ideally whichever was connected first?
            log.info('when connecting nodes and changing vals, both had values, so default to input change')
            changing_node, changing_name, new_value = input_node, input_name, current_output_value
        if changing_node is not None and new_value is not None:
            update_widget_or_prop(changing_node, changing_name, new_value)
    # update gameEffects property to build requirements Set, with nested req OR AND
    if output_node.name() == 'CustomGameEffect' and input_name in ['ReqSet', 'RequirementSetId']:
        current_reqset = output_node.get_property('RequirementSetDict')
        if current_reqset:
            current_reqset = current_reqset[output_name]
            # build new req
            input_node_name = input_node.get_property('table_name')
            if input_node_name == 'ReqEffectCustom':            # add single req to list
                req_id = input_node.get_widget('RequirementId').get_value()
                current_reqset['reqs'].append(req_id)
            elif input_node_name == 'RequirementSets':          # use existant reqset
                reqset_id = input_node.get_widget('RequirementSetId').get_value()
                current_reqset['reqs'].append({'reqset': reqset_id})
            else:
                log.warning(f'wrong input table when building connection between CustomGameEffect'
                            f' and {input_node_name}')


def update_widget_or_prop(node, widget_name, new_val):
    display_widget = node.get_widget(widget_name)
    if display_widget is not None:
        display_widget.set_value(new_val)
    else:
        hidden_property = node.get_property(widget_name)
        if hidden_property is not None:
            node.set_property(widget_name, new_val)


def sync_nodes_check(node, property_name):
    age = node.graph.property('meta').get('Age')
    age_specific_db = db_spec.all_possible_vals if age == 'ALWAYS' else db_spec.possible_vals.get(age, {})
    pk_list = age_specific_db.get(node.name(), {}).get('primary_keys', {})
    if len(pk_list) == 1 and pk_list[0] == property_name:
        sync_node_options(node.graph, age_specific_db)


# handles recursion. We want it so if a node changes a field that is linked to another node, backwards OR forwards
# it updates downstream and upstream, changing fields. This prevents those field change retriggering on the
# original node, ad infinitum. Couldn't find a cleaner way with blocking signals.
# bodge job for blocking recursion
recently_changed = {}

def propogate_port_check(node, property_name):
    node_name = node.name()
    if recently_changed.get(node_name,  {}).get(property_name, {}):
        recently_changed[node_name][property_name] = False
        return
    else:
        if node_name not in recently_changed:
            recently_changed[node_name] = {}
        recently_changed[node_name][property_name] = True
        propogate_node_ports(node, property_name)
        recently_changed[node_name][property_name] = False


def propogate_node_ports(node, property_name):
    matching_ports = [p for p in list(node.inputs().values()) + list(node.outputs().values())
                      if p.name() == property_name]
    for matching_port in matching_ports:
        is_connected = bool(matching_port.connected_ports())
        if is_connected:
            propagate_value_by_port_name(node, property_name)


def propagate_value_by_port_name(source_node, prop_name):
    prop_value = source_node.get_property(prop_name)
    all_ports = list(source_node.inputs().values()) + list(source_node.outputs().values())
    for port in all_ports:
        if port.name() == prop_name:
            for connected_port in port.connected_ports():
                target_prop_name = connected_port.name()
                target_node = connected_port.node()
                if target_node.has_property(target_prop_name):
                    # we need to make sure if the target node is a comboBox, we first add the option
                    widget = target_node.get_widget(target_prop_name)
                    if widget.__class__.__name__ == 'NodeComboBox':
                        widget.add_items([prop_value])
                    target_node.set_property(target_prop_name, prop_value)