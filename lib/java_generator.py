from .base_generator import *
from .case_utils import *
from .definitions import *

import logging
import re
import string
import textwrap


_LOG = logging.getLogger(__name__)

_JAVA_PACKAGE = "org.rocstreaming.roctoolkit"

_JAVA_TYPE_MAP = {
    "unsigned int": "int",
    "int": "int",
    "unsigned long": "long",
    "long": "long",
    "unsigned long long": "long",
    "long long": "long",
    "char": "String",
}

_JAVA_TYPE_OVERRIDE = {
    "packetLength": "Duration",
    "targetLatency": "Duration",
    "latencyTolerance": "Duration",
    "noPlaybackTimeout": "Duration",
    "choppyPlaybackTimeout": "Duration",
    "reuseAddress": "boolean",
}

_JAVA_NAME_OVERRIDE = {
    "roc_context": "RocContext",
    "roc_sender": "RocSender",
    "roc_receiver": "RocReceiver",
    "roc_context_config": "RocContextConfig",
    "roc_sender_config": "RocSenderConfig",
    "roc_receiver_config": "RocReceiverConfig",
}

_JAVA_COMMENT_OVERRIDE = {
    "RocContextConfig": """
        /**
         * Context configuration.
         * <p>
         * RocContextConfig object can be instantiated with {@link RocContextConfig#builder()}.
         *
         * @see RocContext
         */
    """,
    "RocSenderConfig": """
        /**
         * Sender configuration.
         * <p>
         * RocSenderConfig object can be instantiated with {@link RocSenderConfig#builder()}.
         *
         * @see RocSender
         */
    """,
    "RocReceiverConfig": """
        /**
         * Receiver configuration.
         * <p>
         * RocReceiverConfig object can be instantiated with {@link RocReceiverConfig#builder()}.
         *
         * @see RocReceiver
         */
    """,
    "InterfaceConfig": """
        /**
         * Interface configuration.
         * <p>
         * Sender and receiver can have multiple slots ( {@link Slot} ), and each slot
         * can be bound or connected to multiple interfaces ( {@link Interface} ).
         * <p>
         * Each such interface has its own configuration, defined by this class.
         * <p>
         * See {@link RocSender.Configure()}, {@link RocReceiver.Configure()}.
         */
    """,
}


class JavaGenerator(BaseGenerator):

    def __init__(self, base_path: str, api_root: ApiRoot):
        super().__init__(api_root)

        self._base_path = base_path
        self._api_root = api_root

        self._autogen_comment = [
            f"Code generated by bindgen.py from roc-streaming/bindgen",
            f"roc-toolkit git tag: {api_root.git_info.tag}, commit: {api_root.git_info.commit}",
        ]

    def generate_enum(self, enum_definition: EnumDefinition):
        java_name = self._get_java_enum_name(enum_definition.name)
        java_comment = self._get_java_comment(java_name, enum_definition.doc)

        enum_file_path = self._get_java_path(java_name)
        _LOG.debug(f"Writing {enum_file_path}")
        enum_file = open(enum_file_path, "w")

        for line in self._autogen_comment:
            enum_file.write("// " + line + "\n")
        enum_file.write("\n")
        enum_file.write(f"package {_JAVA_PACKAGE};\n\n")
        enum_file.write(java_comment)
        enum_file.write("public enum " + java_name + " {\n")

        for enum_value in enum_definition.values:
            java_enum_value = self._get_java_enum_value_name(enum_definition.name, enum_value.name)
            enum_file.write("\n")
            enum_file.write(self._format_javadoc(enum_value.doc, 4))
            enum_file.write("    " + java_enum_value + "(" + enum_value.value + "),\n")

        enum_file.write("    ;\n\n")

        enum_file.write("    final int value;\n\n")

        enum_file.write("    " + java_name + "(int value) {\n")
        enum_file.write("        this.value = value;\n")
        enum_file.write("    }\n")
        enum_file.write("}\n")

        enum_file.close()

    def generate_struct(self, struct_definition: StructDefinition):
        java_name = self._get_java_struct_name(struct_definition.name)
        java_comment = self._get_java_comment(java_name, struct_definition.doc)

        struct_file_path = self._get_java_path(java_name)
        _LOG.debug(f"Writing {struct_file_path}")
        struct_file = open(struct_file_path, "w")

        for line in self._autogen_comment:
            struct_file.write("// " + line + "\n")
        struct_file.write("\n")
        struct_file.write(f"package {_JAVA_PACKAGE};\n\n")
        struct_file.write("import java.time.Duration;\n")
        struct_file.write("import lombok.*;\n\n")

        struct_file.write(java_comment)
        struct_file.write("@Getter\n")
        struct_file.write("@Builder(builderClassName = \"Builder\", toBuilder = true)\n")
        struct_file.write("@ToString\n")
        struct_file.write("@EqualsAndHashCode\n")
        struct_file.write("public class " + java_name + " {\n")

        for f in struct_definition.fields:
            struct_file.write("\n")
            struct_file.write(self._format_javadoc(f.doc, 4))

            field_type = self._get_java_struct_field_type(f)
            field_name = self._get_java_struct_field_name(f.name)
            struct_file.write(f"    private {field_type} {field_name};\n")

        struct_file.write("\n")
        struct_file.write(f"    public static {java_name}.Builder builder() {{\n")
        struct_file.write(f"        return new {java_name}Validator();\n")
        struct_file.write("    }\n")

        struct_file.write("}\n")
        struct_file.close()

    def generate_class(self, class_definition: ClassDefinition):
        _LOG.warning(f"Class generation is not supported yet: {class_definition.name}")
        # TODO: implement this

    def _get_java_path(self, java_name):
        return (self._base_path + "/src/main/java/"
                + _JAVA_PACKAGE.replace(".", "/") + "/" + java_name + ".java")

    def _get_java_comment(self, java_name, doc):
        if java_name in _JAVA_COMMENT_OVERRIDE:
            return textwrap.dedent(_JAVA_COMMENT_OVERRIDE[java_name]).lstrip()
        else:
            return self._format_javadoc(doc, 0)

    def _get_java_enum_name(self, roc_name):
        if roc_name in _JAVA_NAME_OVERRIDE:
            return _JAVA_NAME_OVERRIDE[roc_name]
        return to_pascal_case(roc_name.removeprefix('roc_'))

    def _get_java_enum_value_name(self, roc_enum_name, roc_enum_value_name):
        prefix = self._api_root.enum_prefixes.get(roc_enum_name)
        return roc_enum_value_name.removeprefix(prefix)

    def _get_java_struct_name(self, roc_name):
        if roc_name in _JAVA_NAME_OVERRIDE:
            return _JAVA_NAME_OVERRIDE[roc_name]
        return to_pascal_case(roc_name.removeprefix('roc_'))

    def _get_java_struct_field_type(self, field):
        java_field_name = to_camel_case(field.name)
        if java_field_name in _JAVA_TYPE_OVERRIDE:
            return _JAVA_TYPE_OVERRIDE[java_field_name]
        elif field.type.startswith('roc_'):
            return self._get_java_class_name(field.type)
        elif field.type in _JAVA_TYPE_MAP:
            return _JAVA_TYPE_MAP[field.type]
        else:
            return field.type

    def _get_java_struct_field_name(self, field_name):
        return to_camel_case(field_name)

    def _get_java_class_name(self, roc_name):
        if roc_name in _JAVA_NAME_OVERRIDE:
            return _JAVA_NAME_OVERRIDE[roc_name]
        return to_pascal_case(roc_name.removeprefix('roc_'))

    def _get_java_class_method_name(self, roc_method_name):
        return to_camel_case(roc_method_name)

    def _format_javadoc(self, doc: DocComment, indent_size: int):
        indent = " " * indent_size
        indent_line = indent + " * "

        doc_string = indent + "/**\n"

        for i, block in enumerate(doc.blocks):
            if i != 0:
                doc_string += indent + " * <p>\n"

            text = self._doc_block_to_string(block)
            # hack: mask spaces to prevent textwrap from breaking inline tags
            # (like {@link ...})
            text = re.sub(r'(\{@[a-z]+)(\s+)(\S+)(\})',
                          r'\1_\3\4',
                          text, flags=re.MULTILINE)

            for t in text.split("\n"):
                lines = textwrap.wrap(t, width=80,
                                      break_on_hyphens=False,
                                      initial_indent=indent_line,
                                      subsequent_indent=indent_line)
                for line in lines:
                    # restore spaces
                    line = re.sub(r'(\{@[a-z]+)(_)(\S+)(\})',
                                  r'\1 \3\4',
                                  line)

                    doc_string += line + "\n"

        doc_string += indent + " */\n"
        return doc_string

    def _doc_block_to_string(self, block: DocBlock):
        result = []
        for item in block.items:
            t = item.type
            if t == "text":
                result.append(item.text)
            elif t == "bold":
                result.append(f'<b>{item.text}</b>')
            elif t == "emphasis":
                result.append(f'<em>{item.text}</em>')
            elif t == "ref" or t == "code":
                result.append(self._doc_ref_to_string(item.text))
            elif t == "see":
                result.append("@see")
            elif t == "list":
                ul = "<ul>\n"
                for li in item.child_blocks:
                    ul += f"<li>{self._doc_block_to_string(li)}</li>\n"
                ul += "</ul>\n"
                result.append(ul)
            else:
                _LOG.warning(
                    f"Unknown doc item type = {t}, consider adding it to _doc_block_to_string")
        return ' '.join(result).replace(" ,", ",").replace(" .", ".")

    def _doc_ref_to_string(self, ref_value: str):
        """
        :param ref_value: enum_value or enum_type, e.g. roc_endpoint or ROC_INTERFACE_AUDIO_SOURCE
        :return: java link javadoc or None if not found
        """
        ref_link = None
        ref_code = ref_value

        if ref_value in self._api_root.doc_refs:
            ref = self._api_root.doc_refs[ref_value]

            if ref.type == "enum":
                ref_link = self._get_java_enum_name(ref.name)
            elif ref.type == "enum_value":
                enum_name = self._get_java_enum_name(ref.enum_name)
                value_name = self._get_java_enum_value_name(ref.enum_name, ref.enum_value_name)
                ref_link = f"{enum_name}#{value_name}"
            elif ref.type == "struct":
                ref_link = self._get_java_struct_name(ref.name)
            elif ref.type == "struct_field":
                ref_code = self._get_java_struct_field_name(ref.name)
            elif ref.type == "class":
                ref_link = self._get_java_class_name(ref.name)
            elif ref.type == "class_method" and ref.class_method_name == "open":
                class_name = self._get_java_class_name(ref.class_name)
                ref_link = f"{class_name}()"
            elif ref.type == "class_method":
                class_name = self._get_java_class_name(ref.class_name)
                method_name = self._get_java_class_method_name(ref.class_method_name)
                ref_link = f"{class_name}#{method_name}()"
            elif ref.type == "typedef":
                ref_link = self._get_java_class_name(ref.name)
            else:
                _LOG.warning(
                    f"Unknown doc ref type = {ref.type}, consider adding it to _doc_ref_to_string")
                ref_code = self._get_java_class_name(ref.name)

        if ref_link:
            return "{@link " + ref_link + "}"
        else:
            return "{@code " + ref_code + "}"
