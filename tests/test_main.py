import unittest
from unittest.mock import patch, MagicMock

class TestMainEntryPoint(unittest.TestCase):

    @patch("app.main.tk.Tk")
    @patch("app.main.TimerApp")
    def test_run_app_initializes_timer_app_and_calls_mainloop(self, mock_app_class, mock_tk_class):
        mock_root = MagicMock()
        mock_app_instance = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_app_class.return_value = mock_app_instance

        from app.main import run_app
        run_app()

        mock_tk_class.assert_called_once()
        mock_app_class.assert_called_once_with(mock_root)
        mock_root.mainloop.assert_called_once()