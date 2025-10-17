import unittest
from app.config import Config

class TestConfig(unittest.TestCase):

    def test_colors_defined(self):
        self.assertIn("blue", Config.COLORS)
        self.assertIn("red", Config.COLORS)
        self.assertIsInstance(Config.COLORS["blue"], str)

    def test_fonts_defined(self):
        self.assertIn("default", Config.FONTS)
        self.assertEqual(Config.FONTS["default"][0], "Helvetica")

    def test_timers_defined(self):
        self.assertGreater(Config.TIMERS["route"], 0)

    def test_paths_defined(self):
        self.assertIn("csv_competitors", Config.PATHS)

    def test_flags_structure(self):
        self.assertIn("debug", Config.FLAGS)