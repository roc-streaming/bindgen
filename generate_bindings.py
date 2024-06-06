#! /usr/bin/env python3

import argparse
import os
import re
import string
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass

DEFAULT_DOXYGEN_DIR = "build/docs/public_api/xml"

ROC_TOOLKIT_BASE_PATH = "../roc-toolkit"
ROC_JAVA_BASE_PATH = "../roc-java"
ROC_GO_BASE_PATH = "../roc-go"

ROC_JAVA_PACKAGE = "org.rocstreaming.roctoolkit"

ODD_PREFIXES = {'roc_protocol': 'ROC_PROTO_'}

JAVA_TYPE_MAP = {
    "unsigned int": "int",
    "unsigned long long": "long",
}

GO_TYPE_MAP = {
    "unsigned int": "uint32",
    "int": "int32",
    "unsigned long": "uint32",
    "long": "int32",
    "unsigned long long": "uint64",
    "long long": "int64",
}

STRUCTS = [
    'structroc__context__config.xml',
    'structroc__receiver__config.xml',
    'structroc__sender__config.xml',
    'structroc__interface__config.xml',
    'structroc__media__encoding.xml',
]


def to_pascal_case(name):
    return ''.join(x.capitalize() for x in name.split('_'))


def to_camel_case(name):
    return name[0].lower() + to_pascal_case(name)[1:]


@dataclass
class DocItem:
    type: string
    text: string = None
    values: list[list['DocItem']] = None


@dataclass
class DocComment:
    items: list[list[DocItem]]


@dataclass
class EnumValue:
    name: string
    value: string
    doc: DocComment


@dataclass
class EnumDefinition:
    name: string
    values: list[EnumValue]
    doc: DocComment


@dataclass
class StructField:
    name: string
    type: string
    doc: DocComment


@dataclass
class StructDefinition:
    name: string
    fields: list[StructField]
    doc: DocComment


class Generator:
    def generate_enum(self, enum_definition: EnumDefinition, autogen_comment: list[string]):
        raise NotImplementedError

    def generate_struct(self, struct_definition: StructDefinition, autogen_comment: list[string]):
        raise NotImplementedError


class JavaGenerator(Generator):

    def __init__(self, base_path: string, name_prefixes: dict[str, str]):
        self.base_path = base_path
        self.name_prefixes: dict[str, str] = name_prefixes

    def generate_enum(self, enum_definition: EnumDefinition, autogen_comment: list[string]):
        java_name = self.get_java_class_name(enum_definition.name)
        enum_values = enum_definition.values

        enum_file = open(self.get_file_path(java_name), "w")

        for line in autogen_comment:
            enum_file.write("// " + line + "\n")
        enum_file.write("\n")
        enum_file.write(f"package {ROC_JAVA_PACKAGE};\n\n")
        enum_file.write(self.format_javadoc(enum_definition.doc, 0))
        enum_file.write("public enum " + java_name + " {\n")

        for enum_value in enum_values:
            java_enum_value = self.get_java_enum_value(enum_definition.name, enum_value.name)
            enum_file.write("\n")
            enum_file.write(self.format_javadoc(enum_value.doc, 4))
            enum_file.write("    " + java_enum_value + "(" + enum_value.value + "),\n")

        enum_file.write("    ;\n\n")

        enum_file.write("    final int value;\n\n")

        enum_file.write("    " + java_name + "(int value) {\n")
        enum_file.write("        this.value = value;\n")
        enum_file.write("    }\n")
        enum_file.write("}\n")

        enum_file.close()

    def generate_struct(self, struct: StructDefinition, autogen_comment: list[string]):
        java_name = self.get_java_class_name(struct.name)
        file = open(self.get_file_path(java_name), "w")

        for line in autogen_comment:
            file.write("// " + line + "\n")
        file.write("\n")
        file.write("\n")
        file.write(f"package {ROC_JAVA_PACKAGE};\n\n")
        file.write("import lombok.*;\n\n")

        file.write(self.format_javadoc(struct.doc, 0))
        file.write("@Getter\n")
        file.write("@Builder(builderClassName = \"Builder\", toBuilder = true)\n")
        file.write("@ToString\n")
        file.write("@EqualsAndHashCode\n")
        file.write("public class " + java_name + " {\n")

        for f in struct.fields:
            file.write("\n")
            file.write(self.format_javadoc(f.doc, 4))

            field_type = self.get_java_class_name(f.type) \
                if f.type.startswith('roc') else JAVA_TYPE_MAP.get(f.type, f.type)
            file.write(f"    private {field_type} {to_camel_case(f.name)};\n")

        file.write("\n")
        file.write(f"    public static {java_name}.Builder builder() {{\n")
        file.write(f"        return new ValidationBuilder();\n")
        file.write("    }\n")

        file.write("\n")
        file.write(f"    private static class ValidationBuilder extends {java_name}.Builder {{\n")
        file.write(f"        @Override\n")
        file.write(f"        public {java_name} build() {{\n")
        for f in struct.fields:
            field_name = to_camel_case(f.name)
            if (f.type.startswith('roc')):
                file.write(f"            Check.notNull(super.{field_name}, \"{field_name}\");\n")
            else:
                file.write(f"            Check.notNegative(super.{field_name}, \"{field_name}\");\n")
        file.write(f"            return super.build();\n")
        file.write("        }\n")
        file.write("    }\n")

        file.write("}\n")


    def get_java_enum_value(self, enum_name, enum_value_name):
        prefix = self.name_prefixes.get(enum_name)
        return enum_value_name.removeprefix(prefix)

    def get_java_enum_name(self, roc_enum_name):
        return to_camel_case(roc_enum_name.removeprefix('roc_'))
    def get_java_class_name(self, roc_name):
        return to_pascal_case(roc_name.removeprefix('roc_'))

    def get_file_path(self, java_name):
        return (self.base_path + "/src/main/java/"
                + ROC_JAVA_PACKAGE.replace(".", "/") + "/" + java_name + ".java")


    def get_java_link(self, roc_enum_value_name):
        for roc_enum_name in self.name_prefixes:
            prefix = self.name_prefixes.get(roc_enum_name)
            if roc_enum_value_name.startswith(prefix):
                java_type = self.get_java_class_name(roc_enum_name)
                java_enum = self.get_java_enum_value(roc_enum_name, roc_enum_value_name)
                return f"{java_type}#{java_enum}"

    def format_javadoc(self, doc: DocComment, indent_size: int):
        indent = " " * indent_size
        indent_line = indent + " * "

        doc_string = indent + "/**\n"

        for i, items in enumerate(doc.items):
            if i != 0:
                doc_string += indent + " * <p>\n"

            text = self.doc_item_to_string(items)
            for t in text.split("\n"):
                lines = textwrap.wrap(t, width=80,
                                      break_on_hyphens=False,
                                      initial_indent=indent_line,
                                      subsequent_indent=indent_line)
                for line in lines:
                    doc_string += line + "\n"

        doc_string += indent + " */\n"
        return doc_string

    def doc_item_to_string(self, items: list[DocItem]):
        # TODO: handle "see" DocItem
        result = []
        for item in items:
            t = item.type
            if t == "text":
                result.append(item.text)
            elif t == "ref" or t == "code":
                result.append(self.ref_to_string(item.text) or item.text)
            elif t == "list":
                ul = "<ul>\n"
                for li in item.values:
                    ul += f"<li>{self.doc_item_to_string(li)}</li>\n"
                ul += "</ul>\n"
                result.append(ul)
            else:
                print(f"unknown doc item type = {t}, consider adding it to doc_item_to_string")
        return ' '.join(result).replace(" ,", ",").replace(" .", ".")

    def ref_to_string(self, ref_value):
        """
        :param ref_value: enum_value or enum_type, e.g. roc_endpoint or ROC_INTERFACE_CONSOLIDATED
        :return: java link javadoc or None if not found
        """
        if ref_value.startswith("roc_"):
            java_name = self.get_java_class_name(ref_value)
            return "{@link " + java_name + "}"

        link = self.get_java_link(ref_value)
        return "{@link " + link + "}" if link else None


class GoGenerator(Generator):

    def __init__(self, base_path: string, name_prefixes: dict[str, str]):
        self.base_path = base_path
        self.name_prefixes: dict[str, str] = name_prefixes

    def generate_enum(self, enum_definition: EnumDefinition, autogen_comment: list[string]):
        go_name = enum_definition.name.removeprefix('roc_')
        enum_values = enum_definition.values

        enum_file_path = self.base_path + "/roc/" + go_name + ".go"
        enum_file = open(enum_file_path, "w")

        go_type_name = to_pascal_case(go_name)
        for line in autogen_comment:
            enum_file.write("// " + line + "\n")
        enum_file.write("\n")
        enum_file.write("package roc\n\n")
        enum_file.write(self.format_comment(enum_definition.doc, ""))
        enum_file.write("//\n")
        roc_prefix = self.name_prefixes[enum_definition.name]
        go_prefix = to_pascal_case(roc_prefix.lower().removeprefix('roc_').removesuffix('_'))
        enum_file.write(
            f"//go:generate stringer -type {go_type_name} -trimprefix {go_prefix} -output {go_name}_string.go\n")
        enum_file.write(f"type {go_type_name} int\n\n")

        enum_file.write("const (\n")

        for i, enum_value in enumerate(enum_values):
            go_enum_value = to_pascal_case(enum_value.name.lower().removeprefix('roc_'))

            if i != 0:
                enum_file.write("\n")
            enum_file.write(self.format_comment(enum_value.doc, "\t"))
            enum_file.write(f"\t{go_enum_value} {go_type_name} = {enum_value.value}\n")

        enum_file.write(")\n")

        enum_file.close()

    def generate_struct(self, struct_definition: StructDefinition, autogen_comment: list[string]):
        go_name = struct_definition.name.removeprefix('roc_')
        struct_fields = struct_definition.fields

        struct_file_path = self.base_path + "/roc/" + go_name + ".go"
        struct_file = open(struct_file_path, "w")

        go_type_name = to_pascal_case(go_name)
        for line in autogen_comment:
            struct_file.write("// " + line + "\n")
        struct_file.write("\n")
        struct_file.write("package roc\n\n")
        struct_file.write(self.format_comment(struct_definition.doc, ""))
        struct_file.write("//\n")

        struct_file.write(f"type {go_type_name} struct {{\n")

        for i, struct_field in enumerate(struct_fields):
            field_name = to_pascal_case(struct_field.name.lower().removeprefix('roc_'))
            field_type = to_pascal_case(struct_field.type.removeprefix('roc_')) \
                if struct_field.type.startswith('roc') \
                   else GO_TYPE_MAP.get(struct_field.type, struct_field.type)

            if i != 0:
                struct_file.write("\n")
            struct_file.write(self.format_comment(struct_field.doc, "\t"))
            struct_file.write(f"\t{field_name} {field_type}\n")

        struct_file.write("}\n")

        struct_file.close()

    def format_comment(self, doc: DocComment, indent: string):
        indent_line = indent + "// "
        doc_string = ""

        for i, items in enumerate(doc.items):
            if i != 0:
                doc_string += indent_line.rstrip() + "\n"

            text = self.doc_item_to_string(items)
            for t in text.split("\n"):
                lines = textwrap.wrap(t, width=80,
                                      break_on_hyphens=False,
                                      initial_indent=indent_line,
                                      subsequent_indent=indent_line)
                for line in lines:
                    doc_string += line + "\n"

        return doc_string

    def doc_item_to_string(self, doc_item: list[DocItem]):
        result = []
        for item in doc_item:
            t = item.type
            if t == "text":
                result.append(item.text)
            elif t == "ref" or t == "code":
                result.append(self.ref_to_string(item.text))
            elif t == "see":
                result.append('See')
            elif t == "list":
                ul = "\n"
                for li in item.values:
                    ul += f" - {self.doc_item_to_string(li)}\n"
                ul += "\n"
                result.append(ul)
            else:
                print(f"unknown doc item type = {t}, consider adding it to doc_item_to_string")
        return ' '.join(result).replace(" ,", ",").replace(" .", ".")

    def ref_to_string(self, ref_value):
        """
        :param ref_value: enum_value or enum_type, e.g. roc_endpoint or ROC_INTERFACE_CONSOLIDATED
        :return: go value
        """
        if ref_value.startswith("roc_"):
            return to_pascal_case(ref_value.removeprefix('roc_'))

        return to_pascal_case(ref_value.lower().removeprefix('roc_'))


def parse_config_xml(doxygen_dir, name):
    filepath = os.path.join(doxygen_dir, name)
    try:
        tree = ElementTree.parse(filepath)
        return tree.getroot()
    except FileNotFoundError:
        print(f"File not found: {filepath}", file=sys.stderr)
        exit(1)
    except ElementTree.ParseError:
        print(f"Error parsing XML file: {filepath}", file=sys.stderr)
        exit(1)


def get_enums(doxygen_dir) -> list[EnumDefinition]:
    root = parse_config_xml(doxygen_dir, 'config_8h.xml')
    enum_definitions = []
    enum_memberdefs = root.findall('.//sectiondef[@kind="enum"]/memberdef[@kind="enum"]')
    for member_def in enum_memberdefs:
        name = member_def.find('name').text
        print(f"found enum in docs: {name}")
        doc = parse_doc(member_def)
        values = []

        for enum_value in member_def.findall('enumvalue'):
            enum_name = enum_value.find('name').text
            value = enum_value.find('initializer').text.removeprefix('= ')
            enum_value_doc = parse_doc(enum_value)
            values.append(EnumValue(enum_name, value, enum_value_doc))

        enum_definitions.append(EnumDefinition(name, values, doc))

    return enum_definitions


def parse_doc(elem) -> DocComment:
    items = []
    brief = elem.find('briefdescription/para')
    items.append(parse_doc_elem(brief))

    for para in elem.findall('detaileddescription/para'):
        items.append(parse_doc_elem(para))

    return DocComment(items)


def strip_text(text):
    if text:
        strip = text.strip()
        if strip:
            return strip
    return None


def parse_doc_elem(elem: ElementTree.Element) -> list[DocItem]:
    items = []
    tag = elem.tag
    parse_children = True
    text = strip_text(elem.text)
    if tag == "para":
        if text:
            # text = re.sub(' *\n *', ' ', text)
            items.append(DocItem("text", text))
    elif tag == "ref":
        if text:
            items.append(DocItem("ref", text))
    elif tag == "simplesect":
        kind = elem.get("kind")
        if kind == "see":
            items.append(DocItem("see"))
        else:
            print(f"unknown simplesect kind = {kind}, consider adding it to parse_doc_elem")
    elif tag == "computeroutput":
        if text:
            items.append(DocItem("code", text))
    elif tag == "itemizedlist":
        values = []
        for li in elem.findall("listitem"):
            li_values = []
            for e in li:
                li_values.extend(parse_doc_elem(e))
            values.append(li_values)
        items.append(DocItem("list", values=values))
        parse_children = False
    else:
        print(f"unknown tag = {tag}, consider adding it to parse_doc_elem")
    if parse_children:
        for item in elem:
            items.extend(parse_doc_elem(item))
            if item.tail:
                strip = item.tail.strip()
                if strip:
                    items.append(DocItem("text", text=strip))
    return items


def get_structs(doxygen_dir) -> list[StructDefinition]:
    struct_definitions = []

    for struct in STRUCTS:
        el = parse_config_xml(doxygen_dir, struct)
        compound = el.find('.//compounddef')

        name = compound.find('compoundname').text
        doc = parse_doc(compound)
        fields = []

        print(f"found struct in docs: {name}")
        for member_def in compound.findall('sectiondef/memberdef[@kind="variable"]'):
            field_name = member_def.find('name').text
            field_type = get_struct_type(member_def.find('type'))
            field_doc = parse_doc(member_def)
            fields.append(StructField(field_name, field_type, field_doc))

        struct_definitions.append(StructDefinition(name, fields, doc))
    return struct_definitions


def get_struct_type(type_def):
    """
    type_def could be <type><ref refid="config_8h_1a5671173735634f14066ec064a909f03b" kindref="member">roc_resampler_backend</ref></type>
    or just <type>unsigned int</type>
    """
    ref = type_def.find('ref')
    if ref is not None:
        return type_def.find('ref').text
    return type_def.text


def get_name_prefixes(enum_definitions, struct_definitions):
    name_prefixes = {}
    for enum_definition in enum_definitions:
        name = enum_definition.name
        prefix = ODD_PREFIXES.get(name, name.upper() + "_")
        name_prefixes[name] = prefix
    for struct_definition in struct_definitions:
        name = struct_definition.name
        prefix = ODD_PREFIXES.get(name, name.upper() + "_")
        name_prefixes[name] = prefix
    return name_prefixes


def generate(generator_construct, toolkit_dir, output_dir, name_prefixes,
             enum_definitions: list[EnumDefinition],
             struct_definitions: list[StructDefinition]):
    if not os.path.isdir(output_dir):
        print(f"Directory does not exist: {output_dir}. "+
              "Can't generate bindings {generator_construct.__name__}",
              file=sys.stderr)
        exit(1)
    git_tag = subprocess.check_output(
        ['git', 'describe', '--tags'], cwd=toolkit_dir).decode('ascii').strip()
    git_commit = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD'], cwd=toolkit_dir).decode('ascii').strip()
    autogen_comment = [f"Code generated by generate_bindings.py script from roc-streaming/bindgen",
                       f"roc-toolkit git tag: {git_tag}, commit: {git_commit}"]
    generator = generator_construct(output_dir, name_prefixes)
    for enum_definition in enum_definitions:
        generator.generate_enum(enum_definition, autogen_comment)
    for struct_definition in struct_definitions:
        generator.generate_struct(struct_definition, autogen_comment)


def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    parser = argparse.ArgumentParser(description='Generate bindings')

    parser.add_argument('-t', '--type', choices=['all', 'java', 'go'],
                        help='Type of enum generation', required=True)
    parser.add_argument('--toolkit_dir',
                        default=ROC_TOOLKIT_BASE_PATH,
                        help=f"Roc Toolkit directory (default: {ROC_TOOLKIT_BASE_PATH})")
    parser.add_argument('--doxygen_dir',
                        default=None,
                        help=f"Doxygen XML directory (default: <toolkit_dir>/{DEFAULT_DOXYGEN_DIR})")
    parser.add_argument('--go_output_dir',
                        default=ROC_GO_BASE_PATH,
                        help=f"Go output directory (default: {ROC_GO_BASE_PATH})")
    parser.add_argument('--java_output_dir',
                        default=ROC_JAVA_BASE_PATH,
                        help=f"Java output directory (default: {ROC_JAVA_BASE_PATH})")

    args = parser.parse_args()

    if not args.doxygen_dir:
        args.doxygen_dir = os.path.join(args.toolkit_dir, DEFAULT_DOXYGEN_DIR)

    enum_definitions = get_enums(args.doxygen_dir)
    struct_definitions = get_structs(args.doxygen_dir)
    name_prefixes = get_name_prefixes(enum_definitions, struct_definitions)

    if args.type == "all" or args.type == "java":
        generate(JavaGenerator, args.toolkit_dir, args.java_output_dir,
                 name_prefixes, enum_definitions, struct_definitions)

    if args.type == "all" or args.type == "go":
        generate(GoGenerator, args.toolkit_dir, args.go_output_dir,
                 name_prefixes, enum_definitions, struct_definitions)


if __name__ == '__main__':
    main()
