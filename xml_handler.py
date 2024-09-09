import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
import tempfile

def dict_to_etree(d, root):
    for k, v in d.items():
        if isinstance(v, list):
            for item in v:
                sub_elem = ET.SubElement(root, k)
                dict_to_etree(item, sub_elem)
        elif isinstance(v, dict):
            sub_elem = ET.SubElement(root, k)
            dict_to_etree(v, sub_elem)
        else:
            if k.startswith('@'):
                root.set(k[1:], v)
            elif k == '#text':
                root.text = v
            else:
                sub_elem = ET.SubElement(root, k)
                sub_elem.text = str(v)


def dict_to_xml(d):
    if len(d) != 1:
        raise ValueError("Dictionary must have exactly one root key")

    root_key = next(iter(d))
    root = ET.Element(root_key)
    dict_to_etree(d[root_key], root)
    return root


def xml_to_string(root):
    return ET.tostring(root, encoding='unicode')


def pretty_print_xml(xml_string):
    parsed_xml = minidom.parseString(xml_string)
    return parsed_xml.toprettyxml(indent="    ")


def save_pretty_xml_to_file(xml_string, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(xml_string)


def read_xml(filepath):
    try:
        tree = ET.parse(filepath)
    except ET.ParseError as e:
        with open(filepath, 'r') as f:
            file = f.readlines()
        current_error, pretty_file, test = None, None, None
        new_error = e
        line, position = e.position
        tries = 0
        while test is None and current_error != new_error and tries < 10:
            try:
                tries += 1
                line_fail = file[line - 1]
                new_file = file
                if line_fail[position - 1] == '"':              # deals with no space between elements
                    line_fail = line_fail[:position - 1] + '\t' + line_fail[position:]
                    new_file[line - 1] = line_fail
                main_tag_idx = [idx for idx, i in enumerate(new_file) if '<' in i and '>' in i][0]
                if main_tag_idx != 0:
                    new_file = new_file[main_tag_idx:]
                bad_comments = [(idx, i) for idx, i in enumerate(new_file) if '-' in i and '<' not in i and '>' not in i]
                for i in bad_comments:
                    new_file[i[0]] = '$$$REMOVE$$$'
                pretty_file = "".join(new_file)
                pretty_file = pretty_file.replace('$$$REMOVE$$$', '')
                test = ET.XML(pretty_file)
            except ET.ParseError as e:
                new_error = e
                print(f'on file: {filepath}')
                print(e)
                line, position = e.position
        if test is None:
            print('couldnt find a way to parse xml')
            raise new_error
        with tempfile.TemporaryFile() as fp:
            fp.write(pretty_file.encode('utf-8'))
            fp.seek(0)
            tree = ET.parse(fp)
    t = tree.getroot()
    return etree_to_dict(t)


def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if children:
        dd = defaultdict(list)
        if d[t.tag] is not None and len(d[t.tag]) > 0:
            for col, val in d[t.tag].items():
                dd[col] = val
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d[t.tag] = {k: v[0] if len(v) == 1 else v for k, v in dd.items()}
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text

    return d
