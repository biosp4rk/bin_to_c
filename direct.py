import argparse

from bin_to_c import (
    parse_context, parse_symbols, DataItem,
    dump_items, write_pointers
)
from dumper import Dumper
from var_def import (
    EnumDef, VarDef, IntType, IntBase, Integer, Boolean,
    EnumVal, Pointer, Struct, ArrFormat, Array,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom_file", type=str)
    parser.add_argument("-x", "--context_file", type=str,
        help="Path to a context json file")
    parser.add_argument("-s", "--symbols_file", type=str,
        help="Path to a file with addresses and names")
    parser.add_argument("-p", "--ptr_output", type=str,
        help="Output file to write all pointers encountered")
    
    args = parser.parse_args()

    # Get context
    if args.context_file:
        with open(args.context_file) as fp:
            enums, defs = parse_context(fp)
    else:
        # Manually define context here
        enums: dict[str, EnumDef] = {}
        defs: dict[str, VarDef] = {}

    # Get symbols
    if args.symbols_file:
        with open(args.symbols_file) as fp:
            syms = parse_symbols(fp)
    else:
        # Manually define symbols here
        syms: dict[int, str] = None

    # Create items here (replace the examples)
    items: list[DataItem] = [
        DataItem(
            Integer(IntType.U8, IntBase.HEX),
            0, "MyInt", "const u8"
        ),
        DataItem(
            Boolean(1),
            1, "MyBool", "const bool8"
        ),
        DataItem(
            EnumVal(1, {0: "VAL_0"}),
            2, "MyEnum", "const u8"
        ),
        DataItem(
            Pointer("const MyType*"),
            4, "MyPointer", "const MyType*"
        ),
        DataItem(
            Struct([("field0", Integer(IntType.U8))]),
            8, "MyStruct", "const MyType"
        ),
        DataItem(
            Array(4, Integer(IntType.U8), ArrFormat.SINGLE_LINE),
            12, "MyArray", "const u8"
        ),
    ]

    # Read rom and create C output
    with open(args.rom_file, "rb") as rom:
        dumper = Dumper(rom, syms)
        c_lines = dump_items(dumper, items)
    
    # Print C output
    print("\n".join(c_lines))

    # Check to write pointers to file
    if args.ptr_output is not None:
        with open(args.ptr_output, "w") as fp:
            write_pointers(fp, dumper.get_pointers())
