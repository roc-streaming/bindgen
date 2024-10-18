from .base_generator import *
from .case_utils import *
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

    def __init__(self, base_path: str, api_root: ApiRoot):
        super().__init__(api_root)

        self._base_path = base_path
        self._api_root = api_root

        self._autogen_comment = [
            f"Code generated by bindgen.py from roc-streaming/bindgen",
            f"roc-toolkit git tag: {api_root.git_info.tag}, commit: {api_root.git_info.commit}",
        ]

    def generate_enum(self, enum_definition: EnumDefinition):
        go_name = enum_definition.name.removeprefix('roc_')
        go_type_name = to_pascal_case(go_name)

        enum_file_path = self._get_go_path(go_name)
        _LOG.debug(f"Writing {enum_file_path}")
        enum_file = open(enum_file_path, "w")

        for line in self._autogen_comment:
            enum_file.write("// " + line + "\n")
        enum_file.write("\n")
        enum_file.write("package roc\n\n")

        enum_file.write(self._get_go_comment(go_type_name, enum_definition.doc))
        roc_prefix = self._api_root.enum_prefixes[enum_definition.name]
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
            enum_file.write(self._format_comment(enum_value.doc, "\t"))
            enum_file.write(f"\t{go_enum_value} {go_type_name} = {enum_value.value}\n")

        enum_file.write(")\n")
        enum_file.close()

    def generate_struct(self, struct_definition: StructDefinition):
        go_name = struct_definition.name.removeprefix('roc_')
        go_type_name = to_pascal_case(go_name)

        struct_file_path = self._get_go_path(go_name)
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

        for line in self._autogen_comment:
            struct_file.write("// " + line + "\n")
        struct_file.write("\n")
        struct_file.write("package roc\n\n")

        if go_imports:
            struct_file.write("import (\n")
            for imp in sorted(go_imports):
                struct_file.write("\t\""+imp+"\"\n")
            struct_file.write(")\n\n")

        struct_file.write(self._get_go_comment(go_type_name, struct_definition.doc))
        struct_file.write(f"type {go_type_name} struct {{\n")

        for i, struct_field in enumerate(struct_definition.fields):
            field_name = field_name_map[struct_field.name]
            field_type = field_type_map[struct_field.name]

            if i != 0:
                struct_file.write("\n")
            struct_file.write(self._format_comment(struct_field.doc, "\t"))
            struct_file.write(f"\t{field_name} {field_type}\n")

        struct_file.write("}\n")
        struct_file.close()

    def generate_class(self, class_definition: ClassDefinition):
        go_name = class_definition.name.removeprefix('roc_')
        go_type_name = to_pascal_case(go_name)

        class_file_path = self._get_go_path(go_name, dummy=True)
        _LOG.debug(f"Writing {class_file_path}")
        class_file = open(class_file_path, "w")

        for line in self._autogen_comment:
            class_file.write("// " + line + "\n")
        class_file.write("\n")
        class_file.write("package roc\n\n")
        class_file.write(self._get_go_comment(go_type_name, class_definition.doc))
        class_file.write("//\n")

        class_file.write(f"type {go_type_name} struct {{\n")
        class_file.write("}\n")
        class_file.write("\n")

        for method in class_definition.methods:
            go_method_name = to_pascal_case(method.name.removeprefix(class_definition.name + "_"))
            if go_method_name == "Open":
                go_method_name += go_type_name
            class_file.write(self._format_comment(method.doc, ""))
            class_file.write(f"func {go_method_name}() {{\n")
            class_file.write("// TODO: implement; fix signature\n")
            class_file.write("}\n")
            class_file.write("\n")

        class_file.close()

    def _get_go_path(self, go_name, dummy=False):
        if dummy:
            go_name += "_DUMMY"
        return self._base_path + "/roc/" + go_name + ".go"

    def _get_go_comment(self, go_name: str, doc: DocComment):
        if go_name in _GO_COMMENT_OVERRIDE:
            return textwrap.dedent(_GO_COMMENT_OVERRIDE[go_name]).lstrip()
        else:
            return self._format_comment(doc, "")

    def _format_comment(self, doc: DocComment, indent: string):
        indent_line = indent + "// "
        doc_string = ""

        for i, block in enumerate(doc.blocks):
            if i != 0:
                doc_string += indent_line.rstrip() + "\n"

            text = self._doc_block_to_string(block)
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

    def _doc_block_to_string(self, block: DocBlock):
        result = []
        for item in block.items:
            t = item.type
            if t == "text" or t == "bold" or t == "emphasis":
                result.append(item.text)
            elif t == "ref" or t == "code":
                result.append(self._doc_ref_to_string(item.text))
            elif t == "see":
                result.append('See')
            elif t == "list":
                ul = "\n"
                for li in item.child_blocks:
                    ul += f" - {self._doc_block_to_string(li)}\n"
                ul += "\n"
                result.append(ul)
            else:
                _LOG.warning(
                    f"unknown doc item type = {t}, consider adding it to _doc_block_to_string")
        return ' '.join(result).replace(" ,", ",").replace(" .", ".")

    def _doc_ref_to_string(self, ref_value: str):
        """
        :param ref_value: enum_value or enum_type, e.g. roc_endpoint or ROC_INTERFACE_AUDIO_SOURCE
        :return: go value
        """
        if ref_value in self._api_root.doc_refs:
            ref = self._api_root.doc_refs[ref_value]

            if ref.type == "enum":
                return to_pascal_case(ref.name.removeprefix("roc_"))
            elif ref.type == "enum_value":
                return to_pascal_case(ref.name.removeprefix("ROC_"))
            elif ref.type == "struct":
                return to_pascal_case(ref.name.removeprefix("roc_"))
            elif ref.type == "struct_field":
                return to_pascal_case(ref.name)
            elif ref.type == "class":
                return to_pascal_case(ref.name.removeprefix("roc_"))
            elif ref.type == "class_method" and ref.class_method_name == "open":
                class_name = to_pascal_case(ref.class_name.removeprefix("roc_"))
                return f"Open{class_name}()"
            elif ref.type == "class_method":
                class_name = to_pascal_case(ref.class_name.removeprefix("roc_"))
                method_name = to_pascal_case(ref.class_method_name)
                return f"{class_name}.{method_name}()"
            elif ref.type == "typedef":
                return to_pascal_case(ref_value.removeprefix("roc_"))
            else:
                _LOG.warning(
                    f"Unknown doc ref type = {ref.type}, consider adding it to _doc_ref_to_string")
                return to_pascal_case(ref_value.removeprefix("roc_"))

        return ref_value
