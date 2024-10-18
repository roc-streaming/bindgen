from dataclasses import dataclass
# note that it's typing.OrderedDict, not collections.OrderedDict
from typing import OrderedDict
import string


# DocRef represents a resolved code reference in doxygen comment.
# For example, "roc_sender_write()" is resolved to a DocRef with
# type="class_method" and class_name="roc_sender".
@dataclass
class DocRef:
    type: string
    name: string
    # if type is "enum_value"
    enum_name: string = None
    enum_value_name: string = None
    # if type is "class_method"
    class_name: string = None
    class_method_name: string = None


# DocItem represents a single formatting unit, e.g. a chunk of bold text
# a code reference, or just a plain text.
# Items of some types are hierarchical, e.g. items of type "list" contain
# children item blocks, one block corresponding to one list element.
@dataclass
class DocItem:
    type: string
    text: string = None
    child_blocks: list['DocBlock'] = None


# DocBlock is a sequence of successive items.
# For example, a block may represent a paragraph or a list element.
@dataclass
class DocBlock:
    items: list[DocItem]



# DocComment represents a comment for a definition (enum, struct, etc).
# Comment consists of a list of blocks, each block corresponding to
# one paragraph.
@dataclass
class DocComment:
    blocks: list[DocBlock]


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
    # roc-toolkit revision
    git_info: GitInfo

    # definitions from roc-toolkit C API
    enum_definitions: OrderedDict[str, EnumDefinition]
    struct_definitions: OrderedDict[str, StructDefinition]
    class_definitions: OrderedDict[str, ClassDefinition]

    # maps enum name to enum value prefix
    enum_prefixes: dict[str, str]
    # maps struct field name to struct name(s)
    struct_fields: dict[str, set[str]]

    # holds all references in every DocItem
    # if DocItem.type is "ref" or "code", then DocItem.text can
    # be used as a key for this map to resolve the reference
    doc_refs: dict[str: DocRef]
