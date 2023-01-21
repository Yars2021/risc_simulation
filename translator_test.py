import unittest
import translator
import isa


class TranslatorTest(unittest.TestCase):
    def translate_and_compare_files(self, input_path, output_path, correct_path):
        translator.main([input_path, output_path])
        output_code = isa.read_code(output_path)
        correct_code = isa.read_code(correct_path)
        self.assertEqual(output_code, correct_code)

    def test_hello_world(self):
        self.translate_and_compare_files("tests/test_hello.asm", "tests/output_hello.ins", "tests/correct_hello.ins")

    def test_cat(self):
        self.translate_and_compare_files("tests/test_cat.asm", "tests/output_cat.ins", "tests/correct_cat.ins")

    def test_prob2(self):
        self.translate_and_compare_files("tests/test_prob2.asm", "tests/output_prob2.ins", "tests/correct_prob2.ins")


if __name__ == '__main__':
    unittest.main()
