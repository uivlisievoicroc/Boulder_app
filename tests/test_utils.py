import tkinter as tk
import unittest
from app.helpers.utils import get_selected_value

class TestUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()  # ascunde fereastra

    def test_get_selected_value_with_mapping(self):
        var = tk.StringVar(master=self.root)
        var.set("A")
        mapping = {"A": 1, "B": 2}
        self.assertEqual(get_selected_value(var, mapping), 1)

    def test_get_selected_value_as_digit(self):
        var = tk.StringVar(master=self.root)
        var.set("5")
        self.assertEqual(get_selected_value(var), 5)

    def test_get_selected_value_as_string(self):
        var = tk.StringVar(master=self.root)
        var.set("Test")
        self.assertEqual(get_selected_value(var), "Test")

    def test_get_selected_value_empty(self):
        var = tk.StringVar(master=self.root)
        var.set("")
        self.assertIsNone(get_selected_value(var))