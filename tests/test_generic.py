"""
Tests the functions in the `generic` module.
"""

from generic import generic 
from strategies import MACross
import os 
import unittest 
from unittest.mock import patch 

class TestGeneric(unittest.TestCase):
    """
    Tests the generic module 

    Run the tests by entering the ff command on the command line:
    `python -m unittest -b`
    """

    def setUp(self):
        """
        Sets up the parameters for testing 
        """
        self.source = "Test"
        self.default = 1 
        self.min_value = 1 
        self.valid_values = ["one","two","three"]

    def test_is_blank(self):
        """
        Tests the `is_blank` function
        """
        # Test whitespace
        self.assertTrue(generic.is_blank("   "))
        # Test empty String
        self.assertTrue(generic.is_blank(""))
        # Test string value 
        self.assertFalse(generic.is_blank("Hello World"))

    def test_validate_integer_input(self):
        """
        Tests the `validate_integer_input` function 
        """
        # Test empty string 
        self.assertTrue(generic.validate_integer_input(""))
        # Test whitespace 
        self.assertTrue(generic.validate_integer_input("  "))
        # Test character input 
        self.assertFalse(generic.validate_integer_input("Hello World"))
        # Test lower than minimum value 
        self.assertRaises(AssertionError, generic.validate_integer_input, "-10", 0)
        # Test valid case 
        self.assertTrue(generic.validate_integer_input("20", 0))

    @patch("builtins.input", return_value="")
    def test_get_integer_value_blank(self, mocked):
        """
        Tests the `get_integer_value` function, given an empty input. 

        Expected return value is the default value 
        """
        value = generic.get_integer_value(self.source, self.default, self.min_value)
        self.assertEqual(value, self.default)
        

    @patch("builtins.input", return_value="5")
    def test_get_integer_value_valid(self, mocked): 
        """
        Tests the `get_integer_value` function, given a valid value. 

        Expected return value is the input value. 
        """
        value = generic.get_integer_value(self.source, self.default, self.min_value)
        self.assertEqual(value, 5)
        

    @patch("builtins.input", return_value="")
    def test_get_string_value_blank(self, mocked):
        """
        Tests the `get_string_value` function, given an empty input. 

        Expected return value is the default value. 
        """
        value = generic.get_string_value(self.source, self.default, self.valid_values)
        self.assertEqual(value, "one")
        
    @patch("builtins.input", return_value = "two")
    def test_get_string_value_string_input(self, mocked):
        """
        Tests the `get_string_value` function, given a valid input. 

        Expected return value is the selected value 
        """
        value = generic.get_string_value(self.source, self.default, self.valid_values, use_str_input=True)
        self.assertEqual(value, "two")

    @patch("builtins.input", return_value = "0")
    def test_get_string_value_none(self, mocked):
        """
        Tests the `get_string_value` function, given 0 as an input.

        Expected return value is None. 
        """
        value = generic.get_string_value(self.source, self.default, self.valid_values)
        self.assertEqual(value, None)

    @patch("builtins.input", return_value = "2")
    def test_get_string_value_valid(self, mocked):
        """
        Tests the `get_string_value` function given a valid selection. 
        
        Expected return value is the selected value
        """
        value = generic.get_string_value(self.source, self.default, self.valid_values)
        self.assertEqual(value, "two")


    def test_cfg_as_dict(self):
        """
        Tests the `cfg_as_dict` function. 

        Tests a valid file, and an invalid file. 
        """
        directory = os.path.join("tests","test_data")

        # Tests the valid file
        valid_path = os.path.join(directory,"cfg_valid.ini")
        kv = {"value" : "1"}
        self.assertEqual(generic.cfg_as_dict(valid_path), kv)

        # Tests the file with invalid formatting
        invalid_path = os.path.join(directory, "cfg_inv.ini")
        self.assertEqual(generic.cfg_as_dict(invalid_path), dict())


    def test_load_module(self):
        """
        Tests the `load_module` function

        Checks if correct module is loaded, and the correct errors are raised when the target directory 
        or file is wrong. 
        """
        target_module = "strategies" # Raises attribute error 
        filename = "ma_cross" # 
        class_name = "MACross" # Raises attribute error 

        # Test valid module
        strategy = generic.load_module(target_module,filename,class_name)
        self.assertEqual(strategy, MACross)

        # Test invalid strategies folder 
        self.assertRaises(AttributeError, generic.load_module, "wrong_path", filename, class_name)

        # Test invalid class name 
        self.assertRaises(AttributeError, generic.load_module, target_module, filename, "wrong_class")

    def test_get_configuration_files(self):
        """
        Tests the `get_configuration_files` function 

        Scans a dummy path for `.ini` files, and returns the files as a list.
        """
        path = os.path.join("tests","test_data")      

        # Test length 
        self.assertEqual(len(generic.get_configuration_files(path)), 2)
        # Test folders with contents, but not .ini files 
        self.assertEqual(generic.get_configuration_files("tests"), list())
        # Test folder with no contents
        empty_path = os.path.join("tests","test_data","empty_folder")
        self.assertEqual(generic.get_configuration_files(empty_path), None)