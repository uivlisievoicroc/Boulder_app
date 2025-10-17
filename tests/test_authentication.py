import unittest
from unittest.mock import MagicMock
from app.classes.authentication import Authentication

class DummyMaster:
    def winfo_rootx(self): return 100
    def winfo_rooty(self): return 200
    def winfo_width(self): return 800
    def winfo_height(self): return 600

class DummyApp:
    def __init__(self):
        self.master = DummyMaster()

class TestAuthentication(unittest.TestCase):

    def setUp(self):
        self.auth = Authentication(DummyApp())

    def test_initial_login_state(self):
        self.assertFalse(self.auth.is_user_logged_in)

    def test_authenticate_sets_logged_in(self):
        mock_callback = MagicMock()
        self.auth.prompt_password = MagicMock(side_effect=lambda: [setattr(self.auth, "is_user_logged_in", True), mock_callback()])
        self.auth.authenticate_user(mock_callback)
        self.assertTrue(self.auth.is_user_logged_in)
        mock_callback.assert_called_once()

if __name__ == '__main__':
    unittest.main()