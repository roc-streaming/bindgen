from .definitions import *

import logging
import os.path
import subprocess
import sys
import xml.etree.ElementTree as ElementTree


_LOG = logging.getLogger(__name__)

_ODD_PREFIXES = {'roc_protocol': 'ROC_PROTO_'}

_DOXYGEN_STRUCTS = [
    'structroc__context__config.xml',
    'structroc__receiver__config.xml',
    'structroc__sender__config.xml',
    'structroc__interface__config.xml',
    'structroc__media__encoding.xml',
]

_DOXYGEN_CLASSES = [
    'context_8h.xml',
    'receiver_8h.xml',
    'sender_8h.xml',
]


def _load_config_xml(doxygen_dir, name):
    filepath = os.path.join(doxygen_dir, name)
    try:
        _LOG.info(f"Parsing {filepath}")
        tree = ElementTree.parse(filepath)
        return tree.getroot()
    except FileNotFoundError:
        _LOG.error(f"File not found: {filepath}")
        exit(1)
    except ElementTree.ParseError:
        _LOG.error(f"Error parsing XML file: {filepath}")
        exit(1)


def _parse_doc_comment(elem) -> DocComment:
    items = []
    brief = elem.find('briefdescription/para')
    items.append(_parse_doc_elem(brief))

    for para in elem.findall('detaileddescription/para'):
        items.append(_parse_doc_elem(para))

    return DocComment(items)


def _parse_doc_elem(elem: ElementTree.Element) -> list[DocItem]:
    items = []
    tag = elem.tag
    parse_children = True
    if elem.text and elem.text.strip():
        text = elem.text.strip()
    else:
        text = None
    if tag == "para":
        if text:
            items.append(DocItem("text", text))
    elif tag == "ref":
        if text:
            items.append(DocItem("ref", text))
    elif tag == "simplesect":
        kind = elem.get("kind")
        if kind == "see":
            items.append(DocItem("see"))
        else:
            _LOG.warning(
                f"unknown simplesect kind = {kind}, consider adding it to parse_doc_elem")
    elif tag == "computeroutput":
        if text:
            items.append(DocItem("code", text))
    elif tag == "bold":
        if text:
            items.append(DocItem("bold", text))
    elif tag == "emphasis":
        if text:
            items.append(DocItem("emphasis", text))
    elif tag == "itemizedlist":
        values = []
        for li in elem.findall("listitem"):
            li_values = []
            for e in li:
                li_values.extend(_parse_doc_elem(e))
            values.append(li_values)
        items.append(DocItem("list", values=values))
        parse_children = False
    else:
        _LOG.warning(f"unknown tag = {tag}, consider adding it to parse_doc_elem")
    if parse_children:
        for item in elem:
            items.extend(_parse_doc_elem(item))
            if item.tail:
                strip = item.tail.strip()
                if strip:
                    items.append(DocItem("text", text=strip))
    return items


def _parse_struct_type(type_def) -> str:
    """
    type_def could be:
       <type>
         <ref refid="config_8h_1a5671173735634f14066ec064a909f03b" kindref="member">
           roc_resampler_backend
         </ref>
       </type>
    or just:
      <type>unsigned int</type>
    """
    ref = type_def.find('ref')
    if ref is not None:
        return type_def.find('ref').text
    return type_def.text


def _collect_enums(doxygen_dir) -> list[EnumDefinition]:
    root = _load_config_xml(doxygen_dir, 'config_8h.xml')
    enum_definitions = []
    enum_memberdefs = root.findall('.//sectiondef[@kind="enum"]/memberdef[@kind="enum"]')
    for member_def in enum_memberdefs:
        name = member_def.find('name').text
        _LOG.debug(f"Found enum in docs: {name}")
        doc = _parse_doc_comment(member_def)
        values = []

        for enum_value in member_def.findall('enumvalue'):
            enum_name = enum_value.find('name').text
            value = enum_value.find('initializer').text.removeprefix('= ')
            enum_value_doc = _parse_doc_comment(enum_value)
            values.append(EnumValue(enum_name, value, enum_value_doc))

        enum_definitions.append(EnumDefinition(name, values, doc))

    return enum_definitions


def _collect_structs(doxygen_dir) -> list[StructDefinition]:
    struct_definitions = []
    for struct in _DOXYGEN_STRUCTS:
        el = _load_config_xml(doxygen_dir, struct)
        compound = el.find('.//compounddef')

        name = compound.find('compoundname').text
        doc = _parse_doc_comment(compound)
        fields = []

        _LOG.debug(f"Found struct in docs: {name}")
        for member_def in compound.findall('sectiondef/memberdef[@kind="variable"]'):
            field_name = member_def.find('name').text
            field_type = _parse_struct_type(member_def.find('type'))
            field_doc = _parse_doc_comment(member_def)
            fields.append(StructField(field_name, field_type, field_doc))

        struct_definitions.append(StructDefinition(name, fields, doc))
    return struct_definitions


def _collect_classes(doxygen_dir) -> list[ClassDefinition]:
    class_definitions = []
    for cls in _DOXYGEN_CLASSES:
        el = _load_config_xml(doxygen_dir, cls)
        compound = el.find('.//compounddef')

        typedef = compound.find('sectiondef/memberdef[@kind="typedef"]')
        name = typedef.find('name').text
        doc = _parse_doc_comment(typedef)
        methods = []

        _LOG.debug(f"Found class in docs: {name}")
        for member_def in compound.findall('sectiondef/memberdef[@kind="function"]'):
            method_name = member_def.find('name').text
            method_doc = _parse_doc_comment(member_def)
            methods.append(ClassMethod(method_name, method_doc))

        class_definitions.append(ClassDefinition(name, methods, doc))

    return class_definitions


def _collect_name_prefixes(enum_definitions, struct_definitions) -> dict[str, str]:
    name_prefixes = {}
    for enum_definition in enum_definitions:
        name = enum_definition.name
        prefix = _ODD_PREFIXES.get(name, name.upper() + "_")
        name_prefixes[name] = prefix
    for struct_definition in struct_definitions:
        name = struct_definition.name
        prefix = _ODD_PREFIXES.get(name, name.upper() + "_")
        name_prefixes[name] = prefix
    return name_prefixes


def _read_git_info(toolkit_dir):
    git_tag = subprocess.check_output(
        ['git', 'describe', '--tags'], cwd=toolkit_dir).decode('ascii').strip()
    git_commit = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD'], cwd=toolkit_dir).decode('ascii').strip()

    _LOG.debug(f"Detected git tag {git_tag}, commit {git_commit}")

    return GitInfo(git_tag, git_commit)


def parse_doxygen(toolkit_dir, doxygen_dir) -> ApiRoot:
    git_info = _read_git_info(toolkit_dir)
    enum_definitions = _collect_enums(doxygen_dir)
    struct_definitions = _collect_structs(doxygen_dir)
    class_definitions = _collect_classes(doxygen_dir)
    name_prefixes = _collect_name_prefixes(enum_definitions, struct_definitions)

    return ApiRoot(
        git_info, enum_definitions, struct_definitions, class_definitions, name_prefixes)
