import unittest
from app.classes.timer import Timer

class DummyApp:
    def __init__(self):
        self.canvas = DummyCanvas()
        self.bar = "bar"
        self.time_text = "text"
        self.control_timer_var = DummyVar()
        self.blue_light_color = "blue"
        self.green_color = "green"
        self.black_color = "black"
        self.white_color = "white"

    def update_display_window_contest(self): pass

class DummyCanvas:
    def itemconfig(self, *args, **kwargs): pass
    def coords(self, *args): return [0, 0, 100, 20]
    def winfo_width(self): return 100
    def winfo_height(self): return 20
    def update_idletasks(self): pass

class DummyVar:
    def set(self, value): pass


class TestTimer(unittest.TestCase):
    def setUp(self):
        self.app = DummyApp()
        self.timer = Timer(self.app, None, None, None)

    def test_adjust_time(self):
        self.timer.adjust_time(100)
        self.assertEqual(self.timer.remaining_time, 100)