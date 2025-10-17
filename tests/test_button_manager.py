import unittest
from unittest.mock import MagicMock
from app.classes.button_manager import ButtonManager

class DummyParent:
    def __init__(self):
        self.button_font = ("Helvetica", 12)

class DummyFrame:
    def __init__(self):
        self.children = []

class TestButtonManager(unittest.TestCase):
    def setUp(self):
        self.parent = DummyParent()
        self.manager = ButtonManager(self.parent)

    def test_toggle_button_enables(self):
        self.manager.buttons["Test"] = {"button": MagicMock()}
        self.manager.toggle_button("Test", enabled=True)
        self.manager.buttons["Test"]["button"].configure.assert_called_with(state='normal')

    def test_toggle_button_disables(self):
        self.manager.buttons["Test"] = {"button": MagicMock()}
        self.manager.toggle_button("Test", enabled=False)
        self.manager.buttons["Test"]["button"].configure.assert_called_with(state='disabled')

    def test_alter_button_text_and_command(self):
        mock_button = MagicMock()
        self.manager.buttons["Start"] = {"button": mock_button}
        self.manager.alter_button("Start", text="Go", command=lambda: print("Go"))
        mock_button.configure.assert_any_call(text="Go")