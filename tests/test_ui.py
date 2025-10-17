import unittest
import tkinter as tk
from app.classes.ui import Ui

class DummyParent(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # ascunde fereastra
        self.app_frames = {}
        self.small_font = ("Helvetica", 12)
        self.font_face = "Helvetica"
        self.selector_font = ("Helvetica", 14)

class TestUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    def setUp(self):
        self.parent = DummyParent()
        self.ui = Ui(self.parent)

    def test_create_frame_adds_to_dict(self):
        frame = self.ui.create_frame("test_frame", row=0, column=0)
        self.assertIn("test_frame", self.parent.app_frames)
        self.assertEqual(self.parent.app_frames["test_frame"], frame)

    def test_render_text_creates_label(self):
        frame = self.ui.create_frame("frame", row=0, column=0)
        label = self.ui.render_text("Hello", frame, row=0, column=0)
        self.assertIsInstance(label, tk.Label)
        self.assertEqual(label.cget("text"), "Hello")

    def test_hide_and_show_frame(self):
        self.ui.create_frame("demo", row=0, column=0)
        self.ui.hide_frame("demo")
        self.ui.show_frame("demo", row=1, column=1)  # Should not raise error

    def test_configure_grid(self):
        frame = self.ui.create_frame("grid", row=0, column=0)
        self.ui.configure_grid(frame, grid_type="row", positions=[0, 1], weights=[1, 2])
        self.ui.configure_grid(frame, grid_type="col", positions=[0], weights=[1])