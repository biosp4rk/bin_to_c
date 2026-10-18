from typing import BinaryIO

from var_def import (
    VarDef, IntBase, Integer, Boolean,
    Pointer, Struct, ArrFormat, Array,
)

TAB_SIZE = 4
TAB = " " * TAB_SIZE

MAX_ROM_SIZE = 0x200_0000
ROM_OFFSET = 0x800_0000

GBA_MEMORY_REGIONS = [
    (0x2000000, 0x2040000),
    (0x3000000, 0x3008000),
    (0x4000000, 0x4000400),
    (0x5000000, 0x5000400),
    (0x6000000, 0x6018000),
    (0x7000000, 0x7000400),
    (0x8000000, 0xA000000),
    (0xE000000, 0xE010000)
]

CHAR_MAP = {
    0x9: r"\t",
    0xA: r"\n",
    0xD: r"\r",
    0x22: r"\"",
    0x5C: r"\\"
}


class Dumper:
    def __init__(self, rom: BinaryIO, syms: dict[int, str] = None):
        self.rom = rom
        self.syms = {}
        if syms is not None:
            for addr, name in syms.items():
                if addr < MAX_ROM_SIZE:
                    addr += ROM_OFFSET
                self.syms[addr] = name
        self.found_ptrs: dict[int, set[str]] = {}
        self.warnings: list[str] = []

    def dump(self, addr: int, var_def: VarDef, name: str = None) -> str:
        self.rom.seek(addr)
        parents: list[str] = []
        if name:
            parents.append(name)
        return self._dump(var_def, 0, parents)
    
    def get_pointers(self) -> dict[int, set[str]]:
        return self.found_ptrs

    def _dump(self, var_def: VarDef, depth: int, parents: list[str]) -> str:
        if isinstance(var_def, Integer):
            size = var_def.size()
            val = self.read_int(size, var_def.signed())
            return self._dump_integer(var_def, val)
        elif isinstance(var_def, Boolean):
            val = self.read_int(var_def.size, False)
            return self._dump_boolean(val)
        elif isinstance(var_def, Struct):
            return self._dump_struct(var_def, depth, parents)
        elif isinstance(var_def, Array):
            return self._dump_array(var_def, depth, parents)
        elif isinstance(var_def, Pointer):
            return self._dump_pointer(var_def, parents)
        else:
            raise TypeError(type(var_def))

    def _dump_int_literal(self, integer: Integer, value: int) -> str:
        if integer.base == IntBase.DEC:
            return f"{value}"
        elif integer.base == IntBase.HEX:
            sign = "-" if value < 0 else ""
            value = abs(value)
            return f"{sign}0x{value:X}"
        else:
            raise ValueError(integer.base)

    def _dump_integer(self, integer: Integer, value: int) -> str:
        if integer.flags:
            enum_def = integer.enum_def or {}
            if value == 0:
                return enum_def.get(0, self._dump_int_literal(integer, 0))
            flags: list[tuple[int, str]] = []
            # Check enum values first
            enums = sorted(enum_def.items(), reverse=True)
            for v, n in enums:
                if v != 0 and value & v == v:
                    flags.append((v, n))
                    value &= ~v
            for i in range(value.bit_length()):
                f = 1 << i
                if value & f:
                    flags.append((f, self._dump_int_literal(integer, f)))
            flags.sort()
            return " | ".join(s for _, s in flags)
        if integer.enum_def is not None and value in integer.enum_def:
            return integer.enum_def[value]
        return self._dump_int_literal(integer, value)

    def _dump_boolean(self, value: int) -> str:
        if value > 1:
            raise ValueError("Invalid bool value")
        return "FALSE" if value == 0 else "TRUE"

    def _dump_struct(self, struct: Struct, depth: int, parents: list[str]) -> str:
        indent = depth * TAB
        indent2 = indent + TAB
        lines = ["{"]
        self._align(4)
        start = self.rom.tell()
        bit_pos = 0
        for i, f in enumerate(struct.fields):
            if f.bits is None:
                # Seek to the start of the next byte
                r = bit_pos % 8
                if r > 0:
                    bit_pos += 8 - r
                    self.rom.seek(start + bit_pos // 8)
                s = self._dump(f.type, depth + 1, parents + [f.name])
                bit_pos = (self.rom.tell() - start) * 8
            else:
                first = bit_pos // 8
                last = (bit_pos + f.bits - 1) // 8
                self.rom.seek(start + first)
                raw = int.from_bytes(self.rom.read(last - first + 1), "little")
                val = (raw >> (bit_pos % 8)) & ((1 << f.bits) - 1)
                if isinstance(f.type, Integer):
                    if f.type.signed() and val & (1 << (f.bits - 1)):
                        val -= 1 << f.bits
                    s = self._dump_integer(f.type, val)
                elif isinstance(f.type, Boolean):
                    s = self._dump_boolean(val)
                else:
                    raise ValueError(type(f.type))
                bit_pos += f.bits
            s = f"{indent2}.{f.name} = {s}"
            if i < len(struct.fields) - 1:
                s += ","
            lines.append(s)
        self._align(4)
        s = indent + "}"
        lines.append(s)
        return "\n".join(lines)

    def _dump_array(self, array: Array, depth: int, parents: list[str]) -> str:
        arr_items = array.items
        is_list = isinstance(arr_items, list)
        if is_list and array.count != len(arr_items):
            raise ValueError("Items length does not match count")
        is_ascii = array.format == ArrFormat.ASCII
        is_single_line = array.format == ArrFormat.SINGLE_LINE
        lines = []
        if not is_ascii:
            lines.append("{")
        indent = depth * TAB
        indent2 = "" if is_single_line else indent + TAB
        if array.format == ArrFormat.ASCII:
            assert isinstance(arr_items, Integer) and arr_items.size() == 1
            vals = bytes(self._read_8(False) for _ in range(array.count)).rstrip(b"\x00")
            s = "".join(
                CHAR_MAP[v] if v in CHAR_MAP
                else chr(v) if 0x20 <= v < 0x7F
                else f"\\{v:03o}"
                for v in vals
            )
            lines.append(f'"{s}"')
        else:
            for i in range(array.count):
                arr_item = arr_items[i] if is_list else arr_items
                s = self._dump(arr_item, depth + 1, parents + [str(i)])
                # Get index string
                i_str: str = None
                if (
                    array.format == ArrFormat.INT_INDEX or
                    (array.enum_def is not None and i not in array.enum_def)
                ):
                    i_str = f"{i}"
                elif array.enum_def is not None and i in array.enum_def:
                    i_str = array.enum_def[i]
                # Get full item string
                if i_str is None:
                    s = indent2 + s
                else:
                    s = f"{indent2}[{i_str}] = {s}"
                if i < array.count - 1 or array.trailing_comma:
                    s += ","
                lines.append(s)
        if not is_ascii:
            s = "}" if is_single_line else indent + "}"
            lines.append(s)
        if is_single_line:
            return " ".join(lines)
        return "\n".join(lines)

    def _dump_pointer(self, ptr: Pointer, parents: list[str]) -> str:
        # Get pointer value
        val = self._read_32(False)
        if val == 0:
            return "NULL"
        if not any(start <= val < end for start, end in GBA_MEMORY_REGIONS):
            addr = self.rom.tell() - 4
            path = " (" + ",".join(parents) + ")" if parents else ""
            msg = f"Invalid pointer 0x{val:X} at 0x{addr:X}{path}"
            self.warnings.append(msg)
        # Get pointer string
        if val in self.syms:
            s = self.syms[val]
            desc = s
        else:
            tc = "void*" if ptr.type_cast is None else ptr.type_cast
            s = f"({tc})0x{val:x}"
            desc = tc
        # Track pointer and its description
        parents.append(desc)
        desc = ",".join(parents)
        if val not in self.found_ptrs:
            self.found_ptrs[val] = set()
        self.found_ptrs[val].add(desc)
        return s

    def _align(self, size: int) -> None:
        r = self.rom.tell() % size
        if r > 0:
            self.rom.seek(size - r, 1)

    def _read_8(self, signed: bool) -> int:
        val = self.rom.read(1)[0]
        if signed and val >= 0x80:
            val -= 0x100
        return val

    def _read_16(self, signed: bool) -> int:
        self._align(2)
        b = self.rom.read(2)
        val = b[0] | (b[1] << 8)
        if signed and val >= 0x8000:
            val -= 0x10000
        return val

    def _read_32(self, signed: bool) -> int:
        self._align(4)
        b = self.rom.read(4)
        val = b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)
        if signed and val >= 0x8000_0000:
            val -= 0x1_0000_0000
        return val

    def read_int(self, size: int, signed: bool) -> int:
        match size:
            case 1:
                return self._read_8(signed)
            case 2:
                return self._read_16(signed)
            case 4:
                return self._read_32(signed)
            case _:
                raise ValueError(f"Invalid int size: {size}")
