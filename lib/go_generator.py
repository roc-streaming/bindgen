from .base_generator import *
from .definitions import *

import logging
import string
import textwrap


_LOG = logging.getLogger(__name__)

_GO_TYPE_MAP = {
    "unsigned int": "uint32",
    "int": "int32",
    "unsigned long": "uint32",
    "long": "int32",
    "unsigned long long": "uint64",
    "long long": "int64",
    "char": "string",
}

_GO_TYPE_OVERRIDE = {
    "PacketLength": "time.Duration",
    "PacketInterleaving": "bool",
    "TargetLatency": "time.Duration",
    "LatencyTolerance": "time.Duration",
    "NoPlaybackTimeout": "time.Duration",
    "ChoppyPlaybackTimeout": "time.Duration",
    "ReuseAddress": "bool",
}

_GO_COMMENT_OVERRIDE = {
    "ContextConfig": """
        // Context configuration.
        // You can zero-initialize this struct to get a default config.
        // See also Context.
    """,
    "SenderConfig": """
        // Sender configuration.
        // You can zero-initialize this struct to get a default config.
        // See also Sender.
    """,
    "ReceiverConfig": """
        // Receiver configuration.
        // You can zero-initialize this struct to get a default config.
        // See also Receiver.
    """,
}


class GoGenerator(BaseGenerator):

    def __init__(self, base_path: string, name_prefixes: dict[str, str]):
        self.base_path = base_path
        self.name_prefixes: dict[str, str] = name_prefixes

    def generate_enum(self, enum_definition: EnumDefinition, autogen_comment: list[string]):
        go_name = enum_definition.name.removeprefix('roc_')

        enum_file_path = self.base_path + "/roc/" + go_name + ".go"
        _LOG.debug(f"Writing {enum_file_path}")
        enum_file = open(enum_file_path, "w")

        go_type_name = to_pascal_case(go_name)

        for line in autogen_comment:
            enum_file.write("// " + line + "\n")
        enum_file.write("\n")
        enum_file.write("package roc\n\n")

        if go_type_name in _GO_COMMENT_OVERRIDE:
            enum_file.write(textwrap.dedent(_GO_COMMENT_OVERRIDE[go_type_name]).lstrip())
        else:
            enum_file.write(self.format_comment(enum_definition.doc, ""))

        roc_prefix = self.name_prefixes[enum_definition.name]
        go_prefix = to_pascal_case(roc_prefix.lower().removeprefix('roc_').removesuffix('_'))
        enum_file.write("//\n")
        enum_file.write(f"//go:generate stringer")
        enum_file.write(f" -type {go_type_name} -trimprefix {go_prefix} -output {go_name}_string.go\n")

        enum_file.write(f"type {go_type_name} int\n\n")
        enum_file.write("const (\n")

        for i, enum_value in enumerate(enum_definition.values):
            go_enum_value = to_pascal_case(enum_value.name.lower().removeprefix('roc_'))

            if i != 0:
                enum_file.write("\n")
            enum_file.write(self.format_comment(enum_value.doc, "\t"))
            enum_file.write(f"\t{go_enum_value} {go_type_name} = {enum_value.value}\n")

        enum_file.write(")\n")

        enum_file.close()

    def generate_struct(self, struct_definition: StructDefinition, autogen_comment: list[string]):
        go_name = struct_definition.name.removeprefix('roc_')
        go_type_name = to_pascal_case(go_name)

        struct_file_path = self.base_path + "/roc/" + go_name + ".go"
        _LOG.debug(f"Writing {struct_file_path}")
        struct_file = open(struct_file_path, "w")

        field_name_map = {}
        field_type_map = {}
        for struct_field in struct_definition.fields:
            field_name = to_pascal_case(struct_field.name.lower().removeprefix('roc_'))

            if struct_field.type.startswith('roc'):
                field_type = to_pascal_case(struct_field.type.removeprefix('roc_'))
            elif field_name in _GO_TYPE_OVERRIDE:
                field_type = _GO_TYPE_OVERRIDE[field_name]
            elif struct_field.type in _GO_TYPE_MAP:
                field_type = _GO_TYPE_MAP[struct_field.type]
            else:
                field_type = struct_field.type

            field_name_map[struct_field.name] = field_name
            field_type_map[struct_field.name] = field_type

        go_imports = set()
        for field_type in field_type_map.values():
            if field_type.startswith("time."):
                go_imports.add("time")

        for line in autogen_comment:
            struct_file.write("// " + line + "\n")
        struct_file.write("\n")
        struct_file.write("package roc\n\n")

        if go_imports:
            struct_file.write("import (\n")
            for imp in sorted(go_imports):
                struct_file.write("\t\""+imp+"\"\n")
            struct_file.write(")\n\n")

        if go_type_name in _GO_COMMENT_OVERRIDE:
            struct_file.write(textwrap.dedent(_GO_COMMENT_OVERRIDE[go_type_name]).lstrip())
        else:
            struct_file.write(self.format_comment(struct_definition.doc, ""))

        struct_file.write(f"type {go_type_name} struct {{\n")

        for i, struct_field in enumerate(struct_definition.fields):
            field_name = field_name_map[struct_field.name]
            field_type = field_type_map[struct_field.name]

            if i != 0:
                struct_file.write("\n")
            struct_file.write(self.format_comment(struct_field.doc, "\t"))
            struct_file.write(f"\t{field_name} {field_type}\n")

        struct_file.write("}\n")

        struct_file.close()

    def generate_class(self, class_definition: ClassDefinition, autogen_comment: list[string]):
        go_name = class_definition.name.removeprefix('roc_')

        class_file_path = self.base_path + "/roc/" + go_name + "_DUMMY.go"
        _LOG.debug(f"Writing {class_file_path}")
        class_file = open(class_file_path, "w")

        go_type_name = to_pascal_case(go_name)
        for line in autogen_comment:
            class_file.write("// " + line + "\n")
        class_file.write("\n")
        class_file.write("package roc\n\n")
        class_file.write(self.format_comment(class_definition.doc, ""))
        class_file.write("//\n")

        class_file.write(f"type {go_type_name} struct {{\n")
        class_file.write("}\n")
        class_file.write("\n")

        for method in class_definition.methods:
            go_method_name = to_pascal_case(method.name.removeprefix(class_definition.name + "_"))
            if go_method_name == "Open":
                go_method_name += go_type_name
            class_file.write(self.format_comment(method.doc, ""))
            class_file.write(f"func {go_method_name}() {{\n")
            class_file.write("// TODO: implement; fix signature\n")
            class_file.write("}\n")
            class_file.write("\n")
        class_file.close()

    def format_comment(self, doc: DocComment, indent: string):
        indent_line = indent + "// "
        doc_string = ""

        for i, items in enumerate(doc.items):
            if i != 0:
                doc_string += indent_line.rstrip() + "\n"

            text = self.doc_item_to_string(items)
            for t in text.split("\n"):
                subsequent_indent = indent_line + "   " \
                    if t.startswith(" - ") else indent_line

                t = t.replace("( ", "(").replace(" )", ")")
                lines = textwrap.wrap(t, width=80,
                                      break_on_hyphens=False,
                                      initial_indent=indent_line,
                                      subsequent_indent=subsequent_indent)
                for line in lines:
                    doc_string += line + "\n"

        return doc_string

    def doc_item_to_string(self, doc_item: list[DocItem]):
        result = []
        for item in doc_item:
            t = item.type
            if t == "text" or t == "bold" or t == "emphasis":
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
                _LOG.warning(
                    f"unknown doc item type = {t}, consider adding it to doc_item_to_string")
        return ' '.join(result).replace(" ,", ",").replace(" .", ".")

    def ref_to_string(self, ref_value):
        """
        :param ref_value: enum_value or enum_type, e.g. roc_endpoint or ROC_INTERFACE_CONSOLIDATED
        :return: go value
        """
        if ref_value.startswith('roc_'):
            ref_value = ref_value.removeprefix('roc_')

            if ref_value.endswith('_open()'):
                # e.g: roc_sender_open() => OpenSender()
                return 'Open' + to_pascal_case(ref_value.removesuffix('_open()')) + '()'

            if ref_value.endswith('()'):
                # e.g: roc_sender_write() => Sender.Write()
                parts = ref_value.split('_', 1)
                if len(parts) == 2:
                    return to_pascal_case(parts[0]) + '.' + to_pascal_case(parts[1])

            return to_pascal_case(ref_value)

        return to_pascal_case(ref_value.lower().removeprefix('roc_'))
