import argparse
from dataclasses import dataclass
import json
from typing import Optional, Union, TextIO

from dumper import ROM_OFFSET, Dumper
from var_def import (
    EnumDef, VarDef, IntType, IntBase, Integer, Boolean,
    EnumVal, Pointer, Struct, ArrFormat, Array,
)


@dataclass
class Options:
    rom_file: str
    input_file: str
    context_file: Optional[str] = None
    symbols_file: Optional[str] = None
    ptr_output: Optional[str] = None


def parse_int(num: Union[int, str]) -> int:
    if isinstance(num, int):
        return num
    if isinstance(num, str):
        return int(num, 0)
    raise ValueError(num)


def parse_enum_def(obj: Union[str, list[str], dict[str, str]]) -> EnumDef:
    if isinstance(obj, list):
        return {i: n for i, n in enumerate(obj)}
    elif isinstance(obj, dict):
        return {parse_int(k): n for k, n in obj.items()}
    else:
        raise ValueError("Invalid format for enum def")


def get_enum_def(
    obj: Union[str, list[str], dict[str, str]],
    enums: dict[str, dict[int, str]]
) -> EnumDef:
    if isinstance(obj, str):
        if obj not in enums:
            raise KeyError(f"Enum '{obj}' not found")
        return enums[obj]
    else:
        return parse_enum_def(obj)


def parse_def(
    obj: Union[str, dict],
    defs: dict[str, VarDef],
    enums: dict[str, dict[int, str]]
) -> VarDef:
    if isinstance(obj, str):
        return defs[obj]
    kind = obj["kind"]
    match kind:
        case "int":
            type = IntType[obj["type"].upper()]
            base_str = obj.get("base")
            if base_str is not None:
                base = IntBase[base_str.upper()]
            else:
                base = IntBase.DEC
            return Integer(type, base)
        case "bool":
            return Boolean(parse_int(obj["size"]))
        case "enum_val":
            size = parse_int(obj["size"])
            enum_def = get_enum_def(obj["enum_def"], enums)
            return EnumVal(size, enum_def)
        case "struct":
            fields = [
                (f["name"], parse_def(f["type"], defs, enums))
                for f in obj["fields"]
            ]
            return Struct(fields)
        case "array":
            count = parse_int(obj["count"])
            items_obj = obj["items"]
            if isinstance(items_obj, list):
                items = [parse_def(i, defs, enums) for i in items_obj]
            else:
                items = parse_def(items_obj, defs, enums)
            format_str = obj.get("format")
            if format_str is not None:
                format = ArrFormat[format_str.upper()]
            else:
                format = ArrFormat.MULTI_LINE
            enum_obj = obj.get("enum_def")
            if enum_obj is not None:
                enum_def = get_enum_def(enum_obj, enums)
            else:
                enum_def = None
            return Array(count, items, format, enum_def)
        case "pointer":
            return Pointer(obj.get("type_cast"))
        case _:
            raise ValueError(f"Invalid kind '{kind}'")


def parse_context(fp: TextIO) -> tuple[dict[str, EnumDef], dict[str, VarDef]]:
    context = json.load(fp)
    # Parse enums
    enums: dict[str, EnumDef] = {}
    if "enums" in context:
        for name, vals in context["enums"].items():
            enums[name] = parse_enum_def(vals)
    # Parse defs
    defs: dict[str, VarDef] = {}
    if "defs" in context:
        for name, def_obj in context["defs"].items():
            defs[name] = parse_def(def_obj, defs, enums)
    return enums, defs


def parse_symbols(fp: TextIO) -> dict[int, str]:
    syms: dict[int, str] = {}
    names: set[str] = set()
    for line in fp:
        # Remove comments
        idx = line.find(";")
        if idx != -1:
            line = line[:idx]
        # Skip blank lines
        line = line.strip()
        if line == "":
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError()
        # Get name
        addr_str, name = parts
        if name in names:
            raise ValueError(f"Name '{name}' repeated in sym file")
        names.add(name)
        # Get address
        addr = int(addr_str, 16)
        if addr >= ROM_OFFSET:
            addr -= ROM_OFFSET
        if addr in syms:
            raise ValueError(f"Address {addr:X} repeated in sym file")
        syms[addr] = name
    return syms


@dataclass
class DataItem:
    var_def: VarDef
    addr: int
    name: str = None
    decl: str = None

    def array_str(self) -> str:
        arr_str = ""
        vd = self.var_def
        while isinstance(vd, Array):
            arr_str += f"[{vd.count}]"
            vd = vd.items
        return arr_str


def parse_input(
    fp: TextIO,
    defs: dict[str, VarDef],
    enums: dict[str, EnumDef]
) -> list[DataItem]:
    all_items: list[DataItem] = []
    data = json.load(fp)
    for group in data:
        arrays = group.get("arrays", False)
        var_def = parse_def(group["def"], defs, enums)
        decl = group.get("decl")
        items = group["items"]
        for item in items:
            addr = parse_int(item["addr"])
            name = item.get("name")
            if arrays:
                count = parse_int(item["count"])
                vd = Array(count, var_def)
            else:
                vd = var_def
            all_items.append(DataItem(vd, addr, name, decl))
    return all_items


@dataclass
class MainResult:
    c_lines: list[str]
    pointers: dict[int, set[str]]


def dump_items(dumper: Dumper, items: list[DataItem]) -> list[str]:
    c_lines: list[str] = []
    for i, item in enumerate(items):
        c_lines.append(f"// 0x{item.addr:x}")
        data_str = dumper.dump(item.addr, item.var_def, item.name)
        if item.name:
            arr_str = item.array_str()
            data_str = f"{item.decl} {item.name}{arr_str} = {data_str};"
        c_lines.append(data_str)
        if i < len(items) - 1:
            c_lines.append("")
    return c_lines


def main(options: Options) -> MainResult:
    # Parse context
    enums: dict[str, VarDef] = {}
    defs: dict[str, EnumDef] = {}
    if options.context_file:
        with open(options.context_file) as fp:
            enums, defs = parse_context(fp)

    # Parse symbols
    syms: dict[int, str] = None
    if options.symbols_file:
        with open(options.symbols_file) as fp:
            syms = parse_symbols(fp)

    # Parse input
    with open(options.input_file) as fp:
        items = parse_input(fp, defs, enums)

    # Read rom and create C output
    with open(options.rom_file, "rb") as rom:
        dumper = Dumper(rom, syms)
        c_lines = dump_items(dumper, items)

    return MainResult(c_lines, dumper.get_pointers())


def write_pointers(fp: TextIO, pointers: dict[int, set[str]]) -> None:
    ptrs = sorted(pointers.items())
    for addr, descs in ptrs:
        desc = "; ".join(sorted(descs))
        fp.write(f"{addr:X}\t{desc}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom_file", type=str)
    parser.add_argument("input_file", type=str, help="Input json file")
    parser.add_argument("-c", "--context_file", type=str,
        help="Path to a context json file")
    parser.add_argument("-s", "--symbols_file", type=str,
        help="Path to a file with addresses and names")
    parser.add_argument("-p", "--ptr_output", type=str,
        help="Output file to write all pointers encountered")

    args = parser.parse_args()

    options = Options(
        args.rom_file,
        args.input_file,
        args.context_file,
        args.symbols_file,
        args.ptr_output
    )

    result = main(options)

    # Print C output
    print("\n".join(result.c_lines))

    # Check to write pointers to file
    if options.ptr_output is not None:
        with open(options.ptr_output, "w") as fp:
            write_pointers(fp, result.pointers)
