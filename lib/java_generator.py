from .base_generator import *
from .definitions import *

import string
import textwrap

JAVA_PACKAGE = "org.rocstreaming.roctoolkit"

JAVA_TYPE_MAP = {
    "unsigned int": "int",
    "unsigned long long": "long",
}

class JavaGenerator(BaseGenerator):

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
        enum_file.write(f"package {JAVA_PACKAGE};\n\n")
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
        file.write(f"package {JAVA_PACKAGE};\n\n")
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

    def generate_class(self, class_definition: ClassDefinition, autogen_comment: list[string]):
        print(f"Class generation is not supported yet: {class_definition.name}")

    def get_java_enum_value(self, enum_name, enum_value_name):
        prefix = self.name_prefixes.get(enum_name)
        return enum_value_name.removeprefix(prefix)

    def get_java_enum_name(self, roc_enum_name):
        return to_camel_case(roc_enum_name.removeprefix('roc_'))

    def get_java_class_name(self, roc_name):
        return to_pascal_case(roc_name.removeprefix('roc_'))

    def get_file_path(self, java_name):
        return (self.base_path + "/src/main/java/"
                + JAVA_PACKAGE.replace(".", "/") + "/" + java_name + ".java")

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
        # TODO: handle "see, bold, emphasis" DocItem's
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
