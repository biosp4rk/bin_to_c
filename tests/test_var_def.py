import unittest

from var_def import (
    Integer, IntType, IntBase, Boolean, EnumVal,
    Pointer, Struct, Array, ArrFormat
)


class TestInteger(unittest.TestCase):
    def test_integer_size(self):
        self.assertEqual(Integer(IntType.U8).size(), 1)
        self.assertEqual(Integer(IntType.S16).size(), 2)
        self.assertEqual(Integer(IntType.U32).size(), 4)

    def test_integer_signed(self):
        self.assertFalse(Integer(IntType.U8).signed())
        self.assertTrue(Integer(IntType.S8).signed())

    def test_integer_repr(self):
        i = Integer(IntType.U16, IntBase.HEX)
        self.assertEqual(
            repr(i),
            "Integer(type=IntType.U16, base=IntBase.HEX)"
        )


class TestBoolean(unittest.TestCase):
    def test_valid_sizes(self):
        for size in (1, 2, 4):
            Boolean(size)

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            Boolean(3)

    def test_repr(self):
        self.assertEqual(repr(Boolean(1)), "Boolean(size=1)")


class TestEnumVal(unittest.TestCase):
    def test_valid_enum(self):
        ev = EnumVal(1, {0: "ZERO", 1: "ONE"})
        self.assertEqual(repr(ev), "EnumVal(size=1, enum_def={0: 'ZERO', 1: 'ONE'})")

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            EnumVal(3, {})


class TestPointer(unittest.TestCase):
    def test_default_pointer(self):
        p = Pointer()
        self.assertEqual(repr(p), 'Pointer(type_cast=None)')

    def test_pointer_with_type_cast(self):
        p = Pointer("MyStruct")
        self.assertEqual(repr(p), 'Pointer(type_cast="MyStruct")')


class TestStruct(unittest.TestCase):
    def test_repr(self):
        s = Struct([
            ("a", Integer(IntType.U8)),
            ("b", Boolean(1))
        ])
        self.assertEqual(
            repr(s),
            'Struct(fields=[("a", Integer(type=IntType.U8, base=IntBase.DEC)), ("b", Boolean(size=1))])'
        )


class TestArray(unittest.TestCase):
    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            Array(0, Integer(IntType.U8))

    def test_items_length_mismatch(self):
        with self.assertRaises(ValueError):
            Array(2, [Integer(IntType.U8)])

    def test_invalid_format_with_enum(self):
        with self.assertRaises(ValueError):
            Array(2, Integer(IntType.U8), ArrFormat.SINGLE_LINE, {0: "A"})

    def test_invalid_single_line_items(self):
        s = Struct([("a", Integer(IntType.U8))])
        with self.assertRaises(ValueError):
            Array(2, s, ArrFormat.SINGLE_LINE)

    def test_invalid_ascii_items(self):
        with self.assertRaises(ValueError):
            Array(2, Pointer(), ArrFormat.ASCII)

    def test_repr_single_item(self):
        arr = Array(2, Integer(IntType.U8))
        self.assertIn("count=2", repr(arr))
        self.assertIn("items=Integer", repr(arr))


if __name__ == "__main__":
    unittest.main()
