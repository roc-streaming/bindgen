from .definitions import *

import abc
import string


class BaseGenerator(metaclass=abc.ABCMeta):
    def __init__(self, api_root: ApiRoot):
        self._api_root = api_root

    def generate_files(self):
        for enum_definition in self._api_root.enum_definitions.values():
            self.generate_enum(enum_definition)

        for struct_definition in self._api_root.struct_definitions.values():
            self.generate_struct(struct_definition)

        for class_definition in self._api_root.class_definitions.values():
            self.generate_class(class_definition)

    @abc.abstractmethod
    def generate_enum(self, enum_definition: EnumDefinition):
        pass

    @abc.abstractmethod
    def generate_struct(self, struct_definition: StructDefinition):
        pass

    @abc.abstractmethod
    def generate_class(self, class_definition: ClassDefinition):
        pass
