from typing import BinaryIO

from var_def import (
    VarDef, IntBase, Integer, Boolean, EnumVal,
    Pointer, Struct, ArrFormat, Array,
)

TAB_SIZE = 4
TAB = " " * TAB_SIZE

ROM_OFFSET = 0x800_0000
ROM_SIZE = 0x80_0000

CHAR_MAP = {
    0x0: r"\0",
    0x9: r"\t",
    0xA: r"\n",
    0xD: r"\r",
}


class Dumper:
    def __init__(self, rom: BinaryIO, syms: dict[int, str] = None):
        self.rom = rom
        self.syms = {}
        if syms is not None:
            for addr, name in syms.items():
                if addr < ROM_OFFSET:
                    addr += ROM_OFFSET
                self.syms[addr] = name
        self.found_ptrs: dict[int, set[str]] = {}

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
            if var_def.base == IntBase.DEC:
                s = f"{val}"
            elif var_def.base == IntBase.HEX:
                if val < 0:
                    val = (1 << (size * 8)) + val
                s = f"0x{val:X}"
            return s
        elif isinstance(var_def, Boolean):
            val = self.read_int(var_def.size, False)
            if val > 1:
                raise ValueError("Invalid bool value")
            s = "FALSE" if val == 0 else "TRUE"
            return s
        elif isinstance(var_def, EnumVal):
            val = self.read_int(var_def.size, False)
            if val in var_def.enum_def:
                s = var_def.enum_def[val]
            else:
                s = f"{val}"
            return s
        elif isinstance(var_def, Struct):
            return self._dump_struct(var_def, depth, parents)
        elif isinstance(var_def, Array):
            return self._dump_array(var_def, depth, parents)
        elif isinstance(var_def, Pointer):
            return self._dump_pointer(var_def, parents)


    def _dump_struct(self, struct: Struct, depth: int, parents: list[str]) -> str:
        self._align(4)
        lines = ["{"]
        indent = depth * TAB
        indent2 = indent + TAB
        for i, field in enumerate(struct.fields):
            name, f_def = field
            s = self._dump(f_def, depth + 1, parents + [name])
            s = f"{indent2}.{name} = {s}"
            if i < len(struct.fields) - 1:
                s += ","
            lines.append(s)
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
            s = "".join(CHAR_MAP[v] if v in CHAR_MAP else chr(v) for v in vals)
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
        val = self._read_ptr()
        if val == 0:
            return "NULL"
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

    def _read_ptr(self) -> int:
        val = self._read_32(False)
        if val != 0 and (val < ROM_OFFSET or val >= ROM_OFFSET + ROM_SIZE):
            raise ValueError(f"Invalid pointer at {self.rom.tell():X}")
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
