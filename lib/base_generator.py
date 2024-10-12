from .definitions import *

import string


def to_pascal_case(name):
    return ''.join(x.capitalize() for x in name.split('_'))


def to_camel_case(name):
    return name[0].lower() + to_pascal_case(name)[1:]


class BaseGenerator:
    def generate_enum(self, enum_definition: EnumDefinition, autogen_comment: list[string]):
        raise NotImplementedError

    def generate_struct(self, struct_definition: StructDefinition, autogen_comment: list[string]):
        raise NotImplementedError

    def generate_class(self, class_definition: ClassDefinition, autogen_comment: list[string]):
        raise NotImplementedError
