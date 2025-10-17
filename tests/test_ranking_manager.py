import unittest
from app.classes.ranking_manager import RankingManager

class DummyLabel:
    def __init__(self):
        self.text = ""
    def config(self, text=None):
        if text is not None:
            self.text = text
    def grid_configure(self, row=None): pass

class DummyApp:
    def __init__(self):
        self.route_scores = {
            "C1": {"T1": 10, "T2": 5},
            "C2": {"T1": 20, "T2": 10}
        }
        self.dynamic_routes = ["T1", "T2"]
        self.cm = self  # simulate cm.get_competitors
    def get_competitors(self):
        return ["C1", "C2"]

class TestRankingManager(unittest.TestCase):

    def setUp(self):
        self.app = DummyApp()
        self.rm = RankingManager(self.app)
        self.rm.rankings_widgets = {
            "C1": {"total": DummyLabel(), "rank": DummyLabel(), "name": DummyLabel(), "T1": DummyLabel(), "T2": DummyLabel()},
            "C2": {"total": DummyLabel(), "rank": DummyLabel(), "name": DummyLabel(), "T1": DummyLabel(), "T2": DummyLabel()}
        }
        self.rm.rankings_window = type('DummyWindow', (), {'winfo_exists': lambda self: True})()

    def test_update_total_points_for_competitor(self):
        self.rm.update_total_points_for_competitor("C1")
        self.assertEqual(self.rm.rankings_widgets["C1"]["total"].text, "15.0")

    def test_update_ranking_order(self):
        self.rm.update_ranking_order()
        self.assertEqual(self.rm.rankings_widgets["C2"]["rank"].text, "1")
        self.assertEqual(self.rm.rankings_widgets["C1"]["rank"].text, "2")