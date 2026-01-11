
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
            print('when connecting nodes and changing vals, both had values, so default change input')
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
                print(f'oh no! wrong input table: {input_node_name}')


def update_widget_or_prop(node, widget_name, new_val):
    display_widget = node.get_widget(widget_name)
    if display_widget is not None:
        display_widget.set_value(new_val)
    else:
        hidden_property = node.get_property(widget_name)
        if hidden_property is not None:
            node.set_property(widget_name, new_val)