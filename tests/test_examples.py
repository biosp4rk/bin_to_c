from pathlib import Path
import unittest

from bin_to_c import Options, main


EXAMPLES_DIR = Path("examples")


class TestExamples(unittest.TestCase):
    maxDiff = None


def _make_example_test(example_dir: Path):
    def test(self: unittest.TestCase):
        data_file = example_dir.joinpath("data.bin")
        context_file = example_dir.joinpath("context.json")
        symbols_file = example_dir.joinpath("symbols.txt")
        input_file = example_dir.joinpath("input.json")
        expected_file = example_dir.joinpath("expected.c")

        options = Options(
            str(data_file),
            str(input_file),
            str(context_file) if context_file.exists() else None,
            str(symbols_file) if symbols_file.exists() else None
        )

        result = main(options)
        with open(expected_file) as fp:
            expected = fp.read()
        self.assertEqual("\n".join(result.c_lines) + "\n", expected)
        self.assertEqual(len(result.warnings), 0)

    return test


# Create a test for each directory in examples
for example in EXAMPLES_DIR.iterdir():
    if example.is_dir():
        test_name = f"test_example_{example.name}"
        setattr(
            TestExamples,
            test_name,
            _make_example_test(example)
        )


if __name__ == "__main__":
    unittest.main()
