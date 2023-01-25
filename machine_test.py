import unittest
import machine
import translator


class MachineTest(unittest.TestCase):
    input = "tests/input_file.txt"

    def start_machine(self, code, output):
        translator.main([code, output])
        return machine.main([output, self.input])

    def test_hello(self):
        output = self.start_machine("tests/test_hello.asm", "tests/output_hello.ins")
        self.assertEqual(output, "Hello, World!")

    def test_cat(self):
        output = self.start_machine("tests/test_cat.asm", "tests/output_cat.ins")
        self.assertEqual(output, "Hello, World! From input file.")

    def test_prob2(self):
        output = self.start_machine("tests/test_prob2.asm", "tests/output_prob2.ins")
        self.assertEqual(output, "4613732")


if __name__ == '__main__':
    unittest.main()
