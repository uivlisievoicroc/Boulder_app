import unittest
from app.classes.competitor_manager import CompetitorManager

class DummyApp:
    def __init__(self):
        self.master = None
        self.competitors_listbox = DummyListbox()

class DummyListbox:
    def __init__(self):
        self.items = []

    def insert(self, index, value):
        self.items.append(value)

    def get(self, start, end):
        return self.items

    def itemconfig(self, index, config):
        pass

    def delete(self, index):
        del self.items[index]

class TestCompetitorManager(unittest.TestCase):
    def setUp(self):
        self.app = DummyApp()
        self.cm = CompetitorManager(self.app, ui=None, button_manager=DummyButtonManager(), authentication=None)

    def test_add_competitor(self):
        self.cm.set_competitors([])
        self.cm.add_competitor()
        self.assertIn("C1", self.cm.get_competitors())

class DummyButtonManager:
    def toggle_button(self, *args, **kwargs): pass