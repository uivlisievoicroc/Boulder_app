import unittest
from app.classes.ranking_controller import RankingController

class TestRankingController(unittest.TestCase):

    def setUp(self):
        self.route_scores = {
            "C1": {"T1": 10, "T2": 20},
            "C2": {"T1": 5, "T2": 30},
            "C3": {"T1": 0, "T2": 0},
        }
        self.routes = ["T1", "T2"]
        self.competitors = ["C1", "C2", "C3"]
        self.controller = RankingController(self.route_scores, self.competitors, self.routes)

    def test_calculate_total(self):
        self.assertEqual(self.controller.calculate_total("C1"), 30)
        self.assertEqual(self.controller.calculate_total("C2"), 35)
        self.assertEqual(self.controller.calculate_total("C3"), 0)

    def test_generate_ranked_list(self):
        ranked = self.controller.generate_ranked_list()
        self.assertEqual(ranked, ["C2", "C1", "C3"])

if __name__ == "__main__":
    unittest.main()