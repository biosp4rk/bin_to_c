import unittest

from var_def import (
    Integer, IntType, IntBase, Boolean,
    Pointer, Field, Struct, Array, ArrFormat
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
            "Integer(type=IntType.U16, base=IntBase.HEX, enum_def=None, flags=False)"
        )

    def test_integer_enum_repr(self):
        i = Integer(IntType.U16, enum_def={0: "ZERO", 1: "ONE"})
        self.assertEqual(
            repr(i),
            "Integer(type=IntType.U16, base=IntBase.DEC, enum_def={0: 'ZERO', 1: 'ONE'}, flags=False)"
        )

    def test_invalid_flags_signed(self):
        with self.assertRaises(ValueError):
            Integer(IntType.S32, flags=True)


class TestBoolean(unittest.TestCase):
    def test_valid_sizes(self):
        for size in (1, 2, 4):
            Boolean(size)

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            Boolean(3)

    def test_repr(self):
        self.assertEqual(repr(Boolean(1)), "Boolean(size=1)")


class TestPointer(unittest.TestCase):
    def test_default_pointer(self):
        p = Pointer()
        self.assertEqual(repr(p), 'Pointer(type_cast=None)')

    def test_pointer_with_type_cast(self):
        p = Pointer("MyStruct")
        self.assertEqual(repr(p), 'Pointer(type_cast="MyStruct")')


class TestField(unittest.TestCase):
    def test_bits_valid(self):
        Field("a", Integer(IntType.U8), 1)
        Field("b", Integer(IntType.S8), 8)
        Field("c", Integer(IntType.U32), 32)

    def test_bits_invalid_type(self):
        with self.assertRaises(ValueError):
            Field("a", Pointer(), 4)

    def test_bits_out_of_range(self):
        cases = [
            (Integer(IntType.U8), 0),
            (Integer(IntType.U8), -1),
            (Integer(IntType.U32), 33),
            (Boolean(1), 9)
        ]
        for var_def, bits in cases:
            with self.subTest(var_def=var_def, bits=bits):
                with self.assertRaises(ValueError):
                    Field("a", var_def, bits)


class TestStruct(unittest.TestCase):
    def test_empty_struct(self):
        with self.assertRaises(ValueError):
            Struct([])

    def test_repr(self):
        s = Struct([
            Field("a", Integer(IntType.U8)),
            Field("b", Boolean(1))
        ])
        self.assertEqual(
            repr(s),
            'Struct(fields=[Field(name="a", type=Integer(type=IntType.U8, base=IntBase.DEC, enum_def=None, flags=False), bits=None), Field(name="b", type=Boolean(size=1), bits=None)])'
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
        s = Struct([Field("a", Integer(IntType.U8))])
        with self.assertRaises(ValueError):
            Array(2, s, ArrFormat.SINGLE_LINE)

    def test_invalid_ascii_items(self):
        with self.assertRaises(ValueError):
            Array(2, Pointer(), ArrFormat.ASCII)

    def test_invalid_ascii_enum_items(self):
        with self.assertRaises(ValueError):
            Array(2, Integer(IntType.U8, enum_def={0: "A"}), ArrFormat.ASCII)

    def test_invalid_ascii_flags_items(self):
        with self.assertRaises(ValueError):
            Array(2, Integer(IntType.U8, flags=True), ArrFormat.ASCII)

    def test_repr_single_item(self):
        arr = Array(2, Integer(IntType.U8))
        self.assertIn("count=2", repr(arr))
        self.assertIn("items=Integer", repr(arr))


if __name__ == "__main__":
    unittest.main()
