from .definitions import *

from collections import OrderedDict
import itertools
import logging
import os.path
import re
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
    'endpoint_8h.xml',
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
    blocks = []

    brief = elem.find('briefdescription/para')
    blocks.append(DocBlock(_parse_doc_elem(brief)))

    for para in elem.findall('detaileddescription/para'):
        blocks.append(DocBlock(_parse_doc_elem(para)))

    return DocComment(blocks)


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
                f"Unknown simplesect kind = {kind}, consider adding it to _parse_doc_elem")
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
        child_blocks = []
        for li in elem.findall("listitem"):
            li_items = []
            for e in li:
                li_items.extend(_parse_doc_elem(e))
            child_blocks.append(DocBlock(li_items))
        items.append(DocItem("list", child_blocks=child_blocks))
        parse_children = False
    else:
        _LOG.warning(f"Unknown tag = {tag}, consider adding it to _parse_doc_elem")
    if parse_children:
        for elem_item in elem:
            items.extend(_parse_doc_elem(elem_item))
            if elem_item.tail:
                stripped_tail = elem_item.tail.strip()
                if stripped_tail:
                    items.append(DocItem("text", text=stripped_tail))
    return items


def _parse_struct_type(type_def: ElementTree.Element) -> str:
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


def _parse_enums(doxygen_dir) -> OrderedDict[str, EnumDefinition]:
    root = _load_config_xml(doxygen_dir, 'config_8h.xml')
    enum_memberdefs = root.findall('.//sectiondef[@kind="enum"]/memberdef[@kind="enum"]')
    enum_definitions = OrderedDict()

    for member_def in enum_memberdefs:
        name = member_def.find('name').text
        doc = _parse_doc_comment(member_def)
        values = []

        for enum_value in member_def.findall('enumvalue'):
            enum_name = enum_value.find('name').text
            value = enum_value.find('initializer').text.removeprefix('= ')
            enum_value_doc = _parse_doc_comment(enum_value)
            values.append(EnumValue(enum_name, value, enum_value_doc))

        _LOG.debug(f"Found enum in docs: {name}")
        enum_definitions[name] = EnumDefinition(name, values, doc)

    return enum_definitions


def _parse_structs(doxygen_dir) -> OrderedDict[str, StructDefinition]:
    struct_definitions = OrderedDict()

    for struct in _DOXYGEN_STRUCTS:
        el = _load_config_xml(doxygen_dir, struct)
        compound = el.find('.//compounddef')

        name = compound.find('compoundname').text
        doc = _parse_doc_comment(compound)
        fields = []

        for member_def in compound.findall('sectiondef/memberdef[@kind="variable"]'):
            field_name = member_def.find('name').text
            field_type = _parse_struct_type(member_def.find('type'))
            field_doc = _parse_doc_comment(member_def)
            fields.append(StructField(field_name, field_type, field_doc))

        _LOG.debug(f"Found struct in docs: {name}")
        struct_definitions[name] = StructDefinition(name, fields, doc)

    return struct_definitions


def _parse_classes(doxygen_dir) -> OrderedDict[str, ClassDefinition]:
    class_definitions = OrderedDict()

    for cls in _DOXYGEN_CLASSES:
        el = _load_config_xml(doxygen_dir, cls)
        compound = el.find('.//compounddef')

        typedef = compound.find('sectiondef/memberdef[@kind="typedef"]')
        name = typedef.find('name').text
        doc = _parse_doc_comment(typedef)
        methods = []

        for member_def in compound.findall('sectiondef/memberdef[@kind="function"]'):
            method_name = member_def.find('name').text
            method_doc = _parse_doc_comment(member_def)
            methods.append(ClassMethod(method_name, method_doc))

        _LOG.debug(f"Found class in docs: {name}")
        class_definitions[name] = ClassDefinition(name, methods, doc)

    return class_definitions


def _build_enum_prefixes(enum_definitions, struct_definitions) -> dict[str, str]:
    enum_prefixes = {}

    for enum_definition in enum_definitions.values():
        name = enum_definition.name
        prefix = _ODD_PREFIXES.get(name, name.upper() + "_")
        enum_prefixes[name] = prefix

    return enum_prefixes


def _build_struct_fields(struct_definitions) -> dict[str, set[str]]:
    struct_fields = {}

    for struct_definition in struct_definitions.values():
        for struct_field in struct_definition.fields:
            if struct_field.name not in struct_fields:
                struct_fields[struct_field.name] = set()
            struct_fields[struct_field.name].add(struct_definition.name)

    return struct_fields


def _build_doc_ref(enum_definitions, struct_definitions, class_definitions,
                   enum_prefixes, struct_fields,
                   doc_item):
    name = doc_item.text

    # enum/struct/class name (e.g. "roc_interface")
    if name in enum_definitions:
        return DocRef("enum", name)
    if name in struct_definitions:
        return DocRef("struct", name)
    if name in class_definitions:
        return DocRef("class", name)

    # enum value (e.g. "ROC_INTERFACE_AUDIO_SOURCE")
    if name.startswith('ROC_'):
        for enum_name, prefix in enum_prefixes.items():
            if name.startswith(prefix):
                value_name = name.removeprefix(prefix)
                return DocRef("enum_value", name,
                              enum_name=enum_name,
                              enum_value_name=value_name)

    # struct field (e.g. "packet_length")
    if name in struct_fields:
        return DocRef("struct_field", name)

    # class method (e.g. "roc_sender_write()")
    m = re.match(r'^(roc_[a-z]+)_([a-z_]+)(\(\))?$', name)
    if m:
        class_name, method_name = m.group(1), m.group(2)
        if class_name in class_definitions:
            return DocRef("class_method", name,
                          class_name=class_name,
                          class_method_name=method_name)

    # another type name (e.g. "roc_slot")
    if re.match(r'^roc_[a-z_]+$', name):
        return DocRef("typedef", name)

    return None


def _build_doc_refs(enum_definitions, struct_definitions, class_definitions,
                    enum_prefixes, struct_fields):
    doc_refs = dict()

    def _visit_item(doc_item):
        name = doc_item.text
        if name not in doc_refs:
            ref = _build_doc_ref(enum_definitions, struct_definitions, class_definitions,
                                 enum_prefixes, struct_fields,
                                 doc_item)
            if ref:
                doc_refs[name] = ref

    def _visit_items(doc_items):
        for item in doc_items:
            if item.type == "ref" or item.type == "code":
                _visit_item(item)
            elif item.child_blocks:
                for block in item.child_blocks:
                    _visit_items(block.items)

    def _visit_definition(definition):
        if definition.doc:
            for doc_block in definition.doc.blocks:
                _visit_items(doc_block.items)

    for enum_definition in enum_definitions.values():
        _visit_definition(enum_definition)
        for enum_value in enum_definition.values:
            _visit_definition(enum_value)

    for struct_definition in struct_definitions.values():
        _visit_definition(struct_definition)
        for struct_field in struct_definition.fields:
            _visit_definition(struct_field)

    for class_definition in class_definitions.values():
        _visit_definition(class_definition)
        for class_method in class_definition.methods:
            _visit_definition(class_method)

    return doc_refs


def _read_git_info(toolkit_dir) -> GitInfo:
    git_tag = subprocess.check_output(
        ['git', 'describe', '--tags'], cwd=toolkit_dir).decode('ascii').strip()
    git_commit = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD'], cwd=toolkit_dir).decode('ascii').strip()

    _LOG.debug(f"Detected git tag {git_tag}, commit {git_commit}")

    return GitInfo(git_tag, git_commit)


def parse_doxygen(toolkit_dir, doxygen_dir) -> ApiRoot:
    git_info = _read_git_info(toolkit_dir)

    # parse definitions from doxygen xml
    enum_definitions = _parse_enums(doxygen_dir)
    struct_definitions = _parse_structs(doxygen_dir)
    class_definitions = _parse_classes(doxygen_dir)

    # build indexes
    enum_prefixes = _build_enum_prefixes(enum_definitions, struct_definitions)
    struct_fields = _build_struct_fields(struct_definitions)
    doc_refs = _build_doc_refs(
        enum_definitions, struct_definitions, class_definitions, enum_prefixes, struct_fields)

    return ApiRoot(
        git_info,
        enum_definitions, struct_definitions, class_definitions,
        enum_prefixes, struct_fields,
        doc_refs
    )
