# config.py

class Config:
    COLORS = {
        "blue": "#001219",
        "blue_light": "#21BBDD",
        "blue_light2": "#94d2e5",
        "red": "#EE5529",
        "yellow": "#f5bf17",
        "yellow_light": "#e9d8a6",
        "green": "#317F45",
        "black": "#050708",
        "white": "#ffffff",
        "lightgray": "lightgray",
        "darkgray": "darkgray",
        "gray": "gray",
        "blue_dark": "#136173",
        "dark_blue": "#2e5283"
    }

    FONTS = {
        "font_face": "Helvetica",
        "default": ("Helvetica", 24),
        "small": ("Helvetica", 14),
        "medium": ("Helvetica", 17),
        "input": ("Helvetica", 12),
        "button": ("Helvetica", 27),
        "control_timer": ("Helvetica", 22),
        "selector": ("Helvetica", 14),
        "timer_clock": ("Helvetica", 165, "bold"),
        "izolare": ("Helvetica", 32, "bold"),
        "trasee": ("Helvetica", 58, "bold"),
        "ranking_header": ("Helvetica", 24, "bold"),
        "ranking_cell": ("Helvetica", 20),
        "ranking_button": ("Helvetica", 9),
        "popup_entry": ("Helvetica", 12),
        "menubutton": ("Helvetica", 12),
    }

    TIMERS = {
        "preview": 8 * 60,
        "route": 4 * 60,
        "transit": 15,
        "pause_between_rounds": 90
    }

    PATHS = {
        "csv_competitors": "db/competitors-list.csv",
        "logo": "resources/images/logo.jpeg"
    }

    FLAGS = {
        "debug": True,
        "fullscreen": False
    }