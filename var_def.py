from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Union


EnumDef = dict[int, str]


class VarDef(ABC):
    pass


class IntType(Enum):
    U8 = auto()
    U16 = auto()
    U32 = auto()
    S8 = auto()
    S16 = auto()
    S32 = auto()

class IntBase(Enum):
    DEC = auto()
    HEX = auto()

@dataclass(frozen=True)
class Integer(VarDef):
    type: IntType
    base: IntBase = IntBase.DEC
    enum_def: EnumDef = None
    flags: bool = False

    def __post_init__(self):
        if self.signed() and self.flags:
            raise ValueError("Integer cannot be signed when using bit flags")

    def __repr__(self) -> str:
        fields_str = ", ".join([
            f"type=IntType.{self.type.name}",
            f"base=IntBase.{self.base.name}",
            f"enum_def={self.enum_def}",
            f"flags={self.flags}"
        ])
        return f"Integer({fields_str})"

    def size(self) -> int:
        match self.type:
            case IntType.U8 | IntType.S8:
                return 1
            case IntType.U16 | IntType.S16:
                return 2
            case IntType.U32 | IntType.S32:
                return 4

    def signed(self) -> bool:
        match self.type:
            case IntType.U8 | IntType.U16 | IntType.U32:
                return False
            case IntType.S8 | IntType.S16 | IntType.S32:
                return True


@dataclass(frozen=True)
class Boolean(VarDef):
    size: int

    def __post_init__(self):
        if self.size not in [1, 2, 4]:
            raise ValueError(f"Invalid boolean size: {self.size}")

    def __repr__(self) -> str:
        return f"Boolean(size={self.size})"


@dataclass(frozen=True)
class Pointer(VarDef):
    type_cast: str = None

    def __repr__(self) -> str:
        tc = "None" if self.type_cast is None else f'"{self.type_cast}"'
        return f"Pointer(type_cast={tc})"


@dataclass(frozen=True)
class Field:
    name: str
    type: VarDef
    bits: Optional[int] = None

    def __post_init__(self):
        if self.bits is not None:
            if isinstance(self.type, Integer):
                size = self.type.size()
            elif isinstance(self.type, Boolean):
                size = self.type.size
            else:
                raise ValueError("Bit fields must be integer or boolean")
            if self.bits <= 0 or self.bits > size * 8:
                raise ValueError(f"Invalid bit width: {self.bits}")

    def __repr__(self) -> str:
        return f'Field(name="{self.name}", type={self.type!r}, bits={self.bits})'


@dataclass(frozen=True)
class Struct(VarDef):
    fields: list[Field]

    def __post_init__(self):
        if len(self.fields) == 0:
            raise ValueError("Structs cannot be empty")

    def __repr__(self) -> str:
        fs = ", ".join(repr(f) for f in self.fields)
        return f"Struct(fields=[{fs}])"


class ArrFormat(Enum):
    SINGLE_LINE = auto()
    MULTI_LINE = auto()
    INT_INDEX = auto()
    ENUM_INDEX = auto()
    ASCII = auto()

@dataclass(frozen=True)
class Array(VarDef):
    count: int
    items: Union[VarDef, list[VarDef]]
    format: ArrFormat = ArrFormat.MULTI_LINE
    enum_def: EnumDef = None
    trailing_comma: bool = False
    
    def __post_init__(self):
        # Check size
        if self.count <= 0:
            raise ValueError("Array count must be greater than 0")
        # Check items length
        if isinstance(self.items, list) and len(self.items) != self.count:
            raise ValueError("Items length must match count")
        # Check format if enum def provided
        if (
            self.enum_def is not None and
            self.format not in [ArrFormat.MULTI_LINE, ArrFormat.ENUM_INDEX]
        ):
            raise ValueError(f"Array format cannot be {self.format.name} when enum def is provided")
        # Require an enum def for enum_index format
        if self.format == ArrFormat.ENUM_INDEX and self.enum_def is None:
            raise ValueError("Array format enum_index requires an enum def")
        # Check item type if format is single line
        if self.format == ArrFormat.SINGLE_LINE:
            if (
                isinstance(self.items, (Struct, Array)) or
                (
                    isinstance(self.items, list) and
                    any(isinstance(i, (Struct, Array)) for i in self.items)
                )
            ):
                raise ValueError(f"Array format cannot be {self.format.name} when items are structs or arrays")
        # Check item type if format is ASCII
        elif self.format == ArrFormat.ASCII:
            if not (isinstance(self.items, Integer) and self.items.size() == 1):
                raise ValueError("Array items must be S8 or U8 when format is ASCII")
            if self.items.enum_def is not None:
                raise ValueError("Integer cannot specify enum def when used for ASCII")
            if self.items.flags:
                raise ValueError("Integer cannot use bit flags when used for ASCII")

    def __repr__(self) -> str:
        if isinstance(self.items, list):
            items_str = "[" + ", ".join(repr(i) for i in self.items) + "]"
        else:
            items_str = repr(self.items)
        fields_str = ", ".join([
            f"count={self.count}",
            f"items={items_str}",
            f"format=ArrFormat.{self.format.name}",
            f"enum_def={self.enum_def}",
            f"trailing_comma={self.trailing_comma}"
        ])
        return f"Array({fields_str})"
