import io
import unittest

from dumper import ROM_OFFSET, Dumper
from var_def import (
    IntType, IntBase, Integer, Boolean, EnumVal,
    Pointer, Struct, ArrFormat, Array
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


class TestDumperEnum(unittest.TestCase):
    def test_enum_match(self):
        rom = io.BytesIO(b"\x01")
        d = Dumper(rom)
        ev = EnumVal(1, {0: "ZERO", 1: "ONE"})
        self.assertEqual(d.dump(0, ev), "ONE")

    def test_enum_fallback(self):
        rom = io.BytesIO(b"\x02")
        d = Dumper(rom)
        ev = EnumVal(1, {0: "ZERO"})
        self.assertEqual(d.dump(0, ev), "2")


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
            ("a", Integer(IntType.U8)),
            ("b", Integer(IntType.U8)),
        ])
        out = d.dump(0, s)
        self.assertIn(".a = 1", out)
        self.assertIn(".b = 2", out)
        self.assertTrue(out.startswith("{"))
        self.assertTrue(out.endswith("}"))


class TestDumperArray(unittest.TestCase):
    def test_u8_array(self):
        rom = io.BytesIO(b"\x01\x02\x03")
        d = Dumper(rom)
        arr = Array(3, Integer(IntType.U8))
        out = d.dump(0, arr)
        self.assertIn("1", out)
        self.assertIn("2", out)
        self.assertIn("3", out)

    def test_ascii_array(self):
        rom = io.BytesIO(b"Test\x00")
        d = Dumper(rom)
        arr = Array(5, Integer(IntType.S8), ArrFormat.ASCII)
        out = d.dump(0, arr)
        self.assertEqual('"Test"', out)


if __name__ == "__main__":
    unittest.main()
