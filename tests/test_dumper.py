import io
import unittest

from dumper import ROM_OFFSET, Dumper
from var_def import (
    IntType, IntBase, Integer, Boolean,
    Pointer, Field, Struct, ArrFormat, Array
)


class TestDumperInteger(unittest.TestCase):
    def test_u8(self):
        rom = io.BytesIO(b"\x7F")
        d = Dumper(rom)
        s = d.dump(0, Integer(IntType.U8))
        self.assertEqual(s, "127")

    def test_signed_s8(self):
        rom = io.BytesIO(b"\xFF")
        d = Dumper(rom)
        s = d.dump(0, Integer(IntType.S8))
        self.assertEqual(s, "-1")

    def test_hex(self):
        rom = io.BytesIO(b"\x10")
        d = Dumper(rom)
        s = d.dump(0, Integer(IntType.U8, IntBase.HEX))
        self.assertEqual(s, "0x10")

    def test_signed_hex(self):
        rom = io.BytesIO(b"\x80")
        d = Dumper(rom)
        s = d.dump(0, Integer(IntType.S8, IntBase.HEX))
        self.assertEqual(s, "-0x80")

    def test_enum_match(self):
        rom = io.BytesIO(b"\x01")
        d = Dumper(rom)
        ev = Integer(IntType.U8, enum_def={0: "ZERO", 1: "ONE"})
        self.assertEqual(d.dump(0, ev), "ONE")

    def test_enum_signed_match(self):
        rom = io.BytesIO(b"\xFF")
        d = Dumper(rom)
        ev = Integer(IntType.S8, enum_def={-1: "NONE"})
        self.assertEqual(d.dump(0, ev), "NONE")

    def test_enum_fallback(self):
        rom = io.BytesIO(b"\x02")
        d = Dumper(rom)
        ev = Integer(IntType.U8, enum_def={0: "ZERO"})
        self.assertEqual(d.dump(0, ev), "2")

    def test_enum_fallback_hex(self):
        rom = io.BytesIO(b"\x02")
        d = Dumper(rom)
        ev = Integer(IntType.U8, IntBase.HEX, {0: "ZERO"})
        self.assertEqual(d.dump(0, ev), "0x2")


class TestDumperBoolean(unittest.TestCase):
    def test_false_true(self):
        rom = io.BytesIO(b"\x00\x01")
        d = Dumper(rom)
        self.assertEqual(d.dump(0, Boolean(1)), "FALSE")
        self.assertEqual(d.dump(1, Boolean(1)), "TRUE")

    def test_invalid_bool_value(self):
        rom = io.BytesIO(b"\x02")
        d = Dumper(rom)
        with self.assertRaises(ValueError):
            d.dump(0, Boolean(1))


class TestDumperPointer(unittest.TestCase):
    def test_null_pointer(self):
        rom = io.BytesIO(b"\x00\x00\x00\x00")
        d = Dumper(rom)
        out = d.dump(0, Pointer())
        self.assertEqual(out, "NULL")

    def test_symbol_pointer(self):
        addr = ROM_OFFSET + 0x10
        rom = io.BytesIO(addr.to_bytes(4, "little"))
        d = Dumper(rom, {addr: "MySymbol"})
        out = d.dump(0, Pointer())
        self.assertEqual(out, "MySymbol")
        self.assertIn(addr, d.found_ptrs)

    def test_pointer_type_cast(self):
        addr = ROM_OFFSET + 0x20
        rom = io.BytesIO(addr.to_bytes(4, "little"))
        d = Dumper(rom)
        out = d.dump(0, Pointer("MyType"))
        self.assertEqual(out, f"(MyType)0x{addr:x}")


class TestDumperStruct(unittest.TestCase):
    def test_struct(self):
        rom = io.BytesIO(b"\x01\x02")
        d = Dumper(rom)
        s = Struct([
            Field("a", Integer(IntType.U8)),
            Field("b", Integer(IntType.U8)),
        ])
        out = d.dump(0, s)
        self.assertEqual(out, "\n".join([
            "{",
            "    .a = 1,",
            "    .b = 2",
            "}"
        ]))

    def test_bit_field_basic(self):
        rom = io.BytesIO(b"\x00\x00\x00\x00\xFF\xBA\x0C")
        d = Dumper(rom)
        s = Struct([
            Field("a", Integer(IntType.U8, IntBase.HEX)),
            Field("b", Integer(IntType.U8, IntBase.HEX), 4),
            Field("c", Integer(IntType.U8, IntBase.HEX), 4),
            Field("d", Integer(IntType.U8, IntBase.HEX), 4)
        ])
        out = d.dump(4, s)
        self.assertEqual(out, "\n".join([
            "{",
            "    .a = 0xFF,",
            "    .b = 0xA,",
            "    .c = 0xB,",
            "    .d = 0xC",
            "}"
        ]))

    def test_bit_field_cross_boundary(self):
        rom = io.BytesIO(b"\xFF\xFF\x03")
        d = Dumper(rom)
        s = Struct([
            Field("a", Integer(IntType.U16, IntBase.HEX), 14),
            Field("b", Integer(IntType.U8, IntBase.HEX), 4),
            Field("c", Integer(IntType.U8, IntBase.HEX), 6),
        ])
        out = d.dump(0, s)
        self.assertEqual(out, "\n".join([
            "{",
            "    .a = 0x3FFF,",
            "    .b = 0xF,",
            "    .c = 0x0",
            "}"
        ]))

    def test_bit_field_signed(self):
        rom = io.BytesIO(b"\x85")
        d = Dumper(rom)
        s = Struct([
            Field("a", Boolean(1), 1),
            Field("b", Integer(IntType.S8), 2),
            Field("c", Integer(IntType.S8), 5),
        ])
        out = d.dump(0, s)
        self.assertEqual(out, "\n".join([
            "{",
            "    .a = TRUE,",
            "    .b = -2,",
            "    .c = -16",
            "}"
        ]))


class TestDumperArray(unittest.TestCase):
    def test_u8_array(self):
        rom = io.BytesIO(b"\x01\x02\x03")
        d = Dumper(rom)
        arr = Array(3, Integer(IntType.U8))
        out = d.dump(0, arr)
        self.assertEqual(out, "\n".join([
            "{",
            "    1,",
            "    2,",
            "    3",
            "}"
        ]))

    def test_ascii_array(self):
        rom = io.BytesIO(b"Test\x00")
        d = Dumper(rom)
        arr = Array(5, Integer(IntType.S8), ArrFormat.ASCII)
        out = d.dump(0, arr)
        self.assertEqual('"Test"', out)

    def test_escaped_ascii_array(self):
        rom = io.BytesIO(b'\t"\\')
        d = Dumper(rom)
        arr = Array(3, Integer(IntType.S8), ArrFormat.ASCII)
        out = d.dump(0, arr)
        self.assertEqual(r'"\t\"\\"', out)


if __name__ == "__main__":
    unittest.main()
