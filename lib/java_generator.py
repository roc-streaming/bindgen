from .base_generator import *
from .definitions import *

import logging
import string
import textwrap


_LOG = logging.getLogger(__name__)

_JAVA_PACKAGE = "org.rocstreaming.roctoolkit"

_JAVA_TYPE_MAP = {
    "unsigned int": "int",
    "int": "int",
    "unsigned long": "long",
    "long": "ling",
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

    def __init__(self, base_path: string, name_prefixes: dict[str, str]):
        self.base_path = base_path
        self.name_prefixes: dict[str, str] = name_prefixes

    def generate_enum(self, enum_definition: EnumDefinition, autogen_comment: list[string]):
        java_name = self.get_java_class_name(enum_definition.name)

        enum_file_path = self.get_file_path(java_name)
        _LOG.debug(f"Writing {enum_file_path}")
        enum_file = open(enum_file_path, "w")

        for line in autogen_comment:
            enum_file.write("// " + line + "\n")
        enum_file.write("\n")
        enum_file.write(f"package {_JAVA_PACKAGE};\n\n")
        if java_name in _JAVA_COMMENT_OVERRIDE:
            enum_file.write(textwrap.dedent(_JAVA_COMMENT_OVERRIDE[java_name]).lstrip())
        else:
            enum_file.write(self.format_javadoc(enum_definition.doc, 0))
        enum_file.write("public enum " + java_name + " {\n")

        for enum_value in enum_definition.values:
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

    def generate_struct(self, struct_definition: StructDefinition, autogen_comment: list[string]):
        java_name = self.get_java_class_name(struct_definition.name)

        struct_file_path = self.get_file_path(java_name)
        _LOG.debug(f"Writing {struct_file_path}")
        struct_file = open(struct_file_path, "w")

        for line in autogen_comment:
            struct_file.write("// " + line + "\n")
        struct_file.write("\n")
        struct_file.write(f"package {_JAVA_PACKAGE};\n\n")
        struct_file.write("import java.time.Duration;\n")
        struct_file.write("import lombok.*;\n\n")

        if java_name in _JAVA_COMMENT_OVERRIDE:
            struct_file.write(textwrap.dedent(_JAVA_COMMENT_OVERRIDE[java_name]).lstrip())
        else:
            struct_file.write(self.format_javadoc(struct_definition.doc, 0))
        struct_file.write("@Getter\n")
        struct_file.write("@Builder(builderClassName = \"Builder\", toBuilder = true)\n")
        struct_file.write("@ToString\n")
        struct_file.write("@EqualsAndHashCode\n")
        struct_file.write("public class " + java_name + " {\n")

        for f in struct_definition.fields:
            struct_file.write("\n")
            struct_file.write(self.format_javadoc(f.doc, 4))

            field_type = self.get_field_type(f)
            struct_file.write(f"    private {field_type} {to_camel_case(f.name)};\n")

        struct_file.write("\n")
        struct_file.write(f"    public static {java_name}.Builder builder() {{\n")
        struct_file.write(f"        return new {java_name}Validator();\n")
        struct_file.write("    }\n")

        struct_file.write("}\n")

    def generate_class(self, class_definition: ClassDefinition, autogen_comment: list[string]):
        _LOG.warning(f"Class generation is not supported yet: {class_definition.name}")

    def get_java_enum_value(self, enum_name, enum_value_name):
        prefix = self.name_prefixes.get(enum_name)
        return enum_value_name.removeprefix(prefix)

    def get_java_enum_name(self, roc_enum_name):
        if roc_name in _JAVA_NAME_OVERRIDE:
            return _JAVA_NAME_OVERRIDE[roc_name]
        return to_camel_case(roc_enum_name.removeprefix('roc_'))

    def get_java_class_name(self, roc_name):
        if roc_name in _JAVA_NAME_OVERRIDE:
            return _JAVA_NAME_OVERRIDE[roc_name]
        return to_pascal_case(roc_name.removeprefix('roc_'))

    def get_field_type(self, field):
        java_field_name = to_camel_case(field.name)
        if java_field_name in _JAVA_TYPE_OVERRIDE:
            return _JAVA_TYPE_OVERRIDE[java_field_name]
        elif field.type.startswith('roc_'):
            return self.get_java_class_name(field.type)
        elif field.type in _JAVA_TYPE_MAP:
            return _JAVA_TYPE_MAP[field.type]
        else:
            return field.type

    def get_file_path(self, java_name):
        return (self.base_path + "/src/main/java/"
                + _JAVA_PACKAGE.replace(".", "/") + "/" + java_name + ".java")

    def get_java_link(self, ref_value):
        if ref_value.startswith('roc_'):
            ref_value = ref_value.removeprefix('roc_')

            if ref_value.endswith('_open()'):
                # e.g: roc_sender_open() => RocSender()
                ref_value = ref_value.removesuffix('_open()')

                if f'roc_{ref_value}' in _JAVA_NAME_OVERRIDE:
                    return _JAVA_NAME_OVERRIDE[f'roc_{ref_value}'] + '()'
                else:
                    return to_pascal_case(ref_value) + '()'

            if ref_value.endswith('()'):
                # e.g: roc_sender_write() => RocSender#write()
                parts = ref_value.split('_', 1)
                if len(parts) == 2:
                    if f'roc_{parts[0]}' in _JAVA_NAME_OVERRIDE:
                        return _JAVA_NAME_OVERRIDE[f'roc_{parts[0]}'] + '#' + to_camel_case(parts[1])
                    else:
                        return to_pascal_case(parts[0]) + '#' + to_camel_case(parts[1])

            return to_pascal_case(ref_value)

        if ref_value.startswith('ROC_'):
            for roc_enum_name in self.name_prefixes:
                prefix = self.name_prefixes.get(roc_enum_name)
                if ref_value.startswith(prefix):
                    java_type = self.get_java_class_name(roc_enum_name)
                    java_enum = self.get_java_enum_value(roc_enum_name, ref_value)
                    return f"{java_type}#{java_enum}"

        if ref_value[0].isalpha():
            return to_camel_case(ref_value.lower())

        return None

    def format_javadoc(self, doc: DocComment, indent_size: int):
        indent = " " * indent_size
        indent_line = indent + " * "

        doc_string = indent + "/**\n"

        for i, items in enumerate(doc.items):
            if i != 0:
                doc_string += indent + " * <p>\n"

            text = self.doc_item_to_string(items)
            # hack: don't break links
            text = text.replace("{@link ", "{@link_")

            for t in text.split("\n"):
                lines = textwrap.wrap(t, width=80,
                                      break_on_hyphens=False,
                                      initial_indent=indent_line,
                                      subsequent_indent=indent_line)
                for line in lines:
                    # restore space
                    line = line.replace("{@link_", "{@link ")
                    doc_string += line + "\n"

        doc_string += indent + " */\n"
        return doc_string

    def doc_item_to_string(self, items: list[DocItem]):
        result = []
        for item in items:
            t = item.type
            if t == "text":
                result.append(item.text)
            elif t == "bold":
                result.append(f'<b>{item.text}</b>')
            elif t == "emphasis":
                result.append(f'<em>{item.text}</em>')
            elif t == "ref" or t == "code":
                result.append(self.ref_to_string(item.text) or item.text)
            elif t == "see":
                result.append("@see")
            elif t == "list":
                ul = "<ul>\n"
                for li in item.values:
                    ul += f"<li>{self.doc_item_to_string(li)}</li>\n"
                ul += "</ul>\n"
                result.append(ul)
            else:
                _LOG.warning(
                    f"unknown doc item type = {t}, consider adding it to doc_item_to_string")
        return ' '.join(result).replace(" ,", ",").replace(" .", ".")

    def ref_to_string(self, ref_value):
        """
        :param ref_value: enum_value or enum_type, e.g. roc_endpoint or ROC_INTERFACE_CONSOLIDATED
        :return: java link javadoc or None if not found
        """
        link = self.get_java_link(ref_value)
        return "{@link " + link + "}" if link else ref_value
