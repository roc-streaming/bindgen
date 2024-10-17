from dataclasses import dataclass
import string


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


@dataclass
class ClassMethod:
    name: string
    doc: DocComment


@dataclass
class ClassDefinition:
    name: string
    methods: list[ClassMethod]
    doc: DocComment


@dataclass
class GitInfo:
    tag: str
    commit: str


@dataclass
class ApiRoot:
    git_info: GitInfo
    enum_definitions: list[EnumDefinition]
    struct_definitions: list[StructDefinition]
    class_definitions: list[ClassDefinition]
    name_prefixes: dict[str, str]
