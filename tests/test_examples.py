from pathlib import Path
import unittest

from bin_to_c import Options, main


EXAMPLES_DIR = Path("examples")


class TestExamples(unittest.TestCase):
    pass


def _make_example_test(example_dir: Path):
    def test(self: unittest.TestCase):
        data_file = example_dir.joinpath("data.bin")
        context_file = example_dir.joinpath("context.json")
        symbols_file = example_dir.joinpath("symbols.txt")
        input_file = example_dir.joinpath("input.json")

        options = Options(
            str(data_file),
            str(input_file),
            str(context_file) if context_file.exists() else None,
            str(symbols_file) if symbols_file.exists() else None
        )

        result = main(options)
        self.assertTrue(len(result.c_lines) > 0)

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
