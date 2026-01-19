import io
import json
import unittest

from bin_to_c import (
    Options, parse_int, parse_enum_def, get_enum_def, parse_def,
    parse_context, parse_symbols, DataItem, parse_input
)
from var_def import (
    IntType, IntBase, Integer, Boolean,
    EnumVal, Pointer, Struct, ArrFormat, Array
)


class TestParseInt(unittest.TestCase):
    def test_int_and_string(self):
        self.assertEqual(parse_int(5), 5)
        self.assertEqual(parse_int("5"), 5)
        self.assertEqual(parse_int("0x10"), 16)

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            parse_int(None)


class TestParseEnumDef(unittest.TestCase):
    def test_parse_enum_def_list(self):
        enum = parse_enum_def(["A", "B"])
        self.assertEqual(enum, {0: "A", 1: "B"})

    def test_parse_enum_def_dict(self):
        enum = parse_enum_def({"0x1": "ONE"})
        self.assertEqual(enum, {1: "ONE"})

    def test_parse_enum_def_invalid(self):
        with self.assertRaises(ValueError):
            parse_enum_def("Invalid")

    def test_get_enum_def_by_name(self):
        enums = {"Name": {0: "ZERO"}}
        self.assertEqual(get_enum_def("Name", enums), {0: "ZERO"})

    def test_get_enum_def_missing(self):
        with self.assertRaises(KeyError):
            get_enum_def("Missing", {})


class TestParseDef(unittest.TestCase):
    def test_parse_integer(self):
        vd = parse_def(
            {"kind": "int", "type": "u8", "base": "hex"},
            {}, {}
        )
        self.assertIsInstance(vd, Integer)
        self.assertEqual(vd.type, IntType.U8)
        self.assertEqual(vd.base, IntBase.HEX)

    def test_parse_boolean(self):
        vd = parse_def({"kind": "bool", "size": 1}, {}, {})
        self.assertIsInstance(vd, Boolean)

    def test_parse_enum_val(self):
        enums = {"Name": {0: "ZERO"}}
        vd = parse_def(
            {"kind": "enum_val", "size": 1, "enum_def": "Name"},
            {}, enums
        )
        self.assertIsInstance(vd, EnumVal)

    def test_parse_struct(self):
        vd = parse_def(
            {
                "kind": "struct",
                "fields": [
                    {"name": "a", "type": {"kind": "int", "type": "u8"}}
                ]
            },
            {}, {}
        )
        self.assertIsInstance(vd, Struct)

    def test_parse_array(self):
        vd = parse_def(
            {
                "kind": "array",
                "count": 3,
                "items": {"kind": "int", "type": "u8"},
                "format": "single_line",
            },
            {}, {}
        )
        self.assertIsInstance(vd, Array)
        self.assertEqual(vd.count, 3)
        self.assertEqual(vd.format, ArrFormat.SINGLE_LINE)

    def test_parse_pointer(self):
        vd = parse_def({"kind": "pointer", "type_cast": "Foo"}, {}, {})
        self.assertIsInstance(vd, Pointer)

    def test_invalid_kind(self):
        with self.assertRaises(ValueError):
            parse_def({"kind": "invalid"}, {}, {})


class TestParseContext(unittest.TestCase):
    def test_parse_context(self):
        context = {
            "enums": {"E": ["A", "B"]},
            "defs": {
                "X": {"kind": "int", "type": "u8"}
            }
        }
        fp = io.StringIO(json.dumps(context))
        enums, defs = parse_context(fp)

        self.assertIn("E", enums)
        self.assertIn("X", defs)
        self.assertIsInstance(defs["X"], Integer)


class TestParseSymbols(unittest.TestCase):
    def test_parse_symbols(self):
        fp = io.StringIO("10\tFOO\n20\tBAR\n")
        syms = parse_symbols(fp)
        self.assertEqual(syms, {0x10: "FOO", 0x20: "BAR"})

    def test_duplicate_name(self):
        fp = io.StringIO("10\tFOO\n20\tFOO\n")
        with self.assertRaises(ValueError):
            parse_symbols(fp)

    def test_duplicate_address(self):
        fp = io.StringIO("10\tFOO\n10\tBAR\n")
        with self.assertRaises(ValueError):
            parse_symbols(fp)


class TestDataItem(unittest.TestCase):
    def test_array_str(self):
        vd = Array(3, Array(2, Integer(IntType.U8)))
        item = DataItem(vd, 0)
        self.assertEqual(item.array_str(), "[3][2]")


class TestParseInput(unittest.TestCase):
    def test_parse_input_items(self):
        data = [
            {
                "kind": "items",
                "def": {"kind": "int", "type": "u8"},
                "items": [{"addr": "0x10", "name": "a"}]
            }
        ]
        fp = io.StringIO(json.dumps(data))
        items = parse_input(fp, {}, {})
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].addr, 0x10)
        self.assertEqual(items[0].name, "a")

    def test_parse_input_arrays(self):
        data = [
            {
                "arrays": True,
                "def": {"kind": "int", "type": "u8"},
                "items": [{"addr": "0x0", "name": "arr", "count": 4}]
            }
        ]
        fp = io.StringIO(json.dumps(data))
        items = parse_input(fp, {}, {})
        self.assertIsInstance(items[0].var_def, Array)
        self.assertEqual(items[0].var_def.count, 4)


# TODO: Test main
# class TestMain(unittest.TestCase):

if __name__ == "__main__":
    unittest.main()
