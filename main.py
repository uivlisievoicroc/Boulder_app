import sys
import os
os.makedirs("logs", exist_ok=True)

# Add the parent directory (one level up) to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import math
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import font
from app.config import Config
from datetime import datetime, timedelta
import tkinter.simpledialog as simpledialog
from tkinter import PhotoImage
import sounddevice as sd
import numpy as np
import re
import logging
import threading
from PIL import Image, ImageTk
from app.classes.timer import Timer
from app.classes.button_manager import ButtonManager
from app.classes.ui import Ui
from app.classes.authentication import Authentication
from app.classes.competitor_manager import CompetitorManager
from helpers.utils import *
from app.classes.ranking_manager import RankingManager
# Setează dispozitivul de redare implicit al sistemului
default_output_device = sd.query_devices(kind="output")["name"]
sd.default.device = default_output_device

DEBUG = True
VERSION = 1

def catch_exceptions(func):
    """
    Decorator pentru a captura excepțiile și a le înregistra, evitând oprirea neașteptată a aplicației.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Exception in {func.__name__}: {e}")
    return wrapper

def warmup_audio():
    """
    Redă un sunet silențios scurt pentru a încălzi buffer-ul audio.
    """
    fs = 44100
    silence = np.zeros(int(fs * 0.1))  # 0.1 secunde de silențiu
    sd.play(silence, fs)
    sd.wait()

# Configurare logging: nivelul poate fi schimbat (ex. DEBUG, INFO, WARNING, etc.)

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configurare logging avansată
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Evită dublarea handlerelor dacă sunt deja setate
if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Scriere în fișier
file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Afișare și în terminal
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class TimerApp:

    def __init__(self, master):

        self.master = master
        self.styles = {
            "colors": Config.COLORS,
            "fonts": Config.FONTS
        }
        self.blue_color = self.styles["colors"]["blue"]
        self.blue_light_color = self.styles["colors"]["blue_light"]
        self.blue_light2_color = self.styles["colors"]["blue_light2"]
        self.red_color = self.styles["colors"]["red"]
        self.yellow_color = self.styles["colors"]["yellow"]
        self.yellow_light_color = self.styles["colors"]["yellow_light"]
        self.green_color = self.styles["colors"]["green"]
        self.black_color = self.styles["colors"]["black"]
        self.white_color = self.styles["colors"]["white"]
        self.dark_blue_color = self.styles["colors"]["dark_blue"]

        self.window_bg_color = self.yellow_color

        self.app_locked = False
        self.contest_started = False

        # Dictionary for label → value mapping
        self.contest_types = {
            "Calificări": "qualifiers",
            "Semifinale": "semifinals",
            "Finală": "finals"
        }

        self.app_frames = {}  # Dictionary to store all frames and their state

        # Variabile pentru modul full screen
        self.fullscreen = False
        self.font_face = self.styles["fonts"]["font_face"]
        self.default_font = self.styles["fonts"]["default"]
        self.current_font = self.default_font
        self.medium_font = self.styles["fonts"]["medium"]
        self.small_font = self.styles["fonts"]["small"]
        self.input_font = self.styles["fonts"]["input"]
        self.button_font = self.styles["fonts"]["button"]
        self.control_timer_font = self.styles["fonts"]["control_timer"]
        self.selector_font = self.styles["fonts"]["selector"]
        self.timer_clock_font = self.styles["fonts"]["timer_clock"]
        self.izolare_font = self.styles["fonts"]["izolare"]
        self.trasee_font = self.styles["fonts"]["trasee"]
        
        
        # Init the contest boxes
        self.isolation1_contest = []
        self.isolation2_contest = []
        self.contest_finished = []
        self.all_routes = []
        self.contest_competitors = []
        self.dynamic_routes = []
        self.contest_finished_competitors = []
        self.group_A = []
        self.group_B = []

        self.rotation_contest = 0
        self.old_rotation = 0
        self.dynamic_routes_number = 0

        self.contest_type = None
        self.competitors_loaded = False
        self.contest_type_label = None
        self.bar = None

        # Frames
        self.timer_frame = None
        self.state_frame = None
        self.finished_frame = None

        # Windows
        self.state_window = None
        self.competitors_window = None
        self.timer_window = None

        # Load dependencies
        self.button_manager = ButtonManager(self)
        self.ui = Ui(self)
        self.authentication = Authentication(self)
        self.timer = Timer(self, self.ui, self.button_manager, self.authentication)
        self.cm = CompetitorManager(self, self.ui, self.button_manager, self.authentication)
        self.ranking_manager = RankingManager(self)

        self.toggle_button = self.button_manager.toggle_button
        self.alter_button = self.button_manager.alter_button
        self.hide_button = self.button_manager.hide_button
        """
        self.control_timer_var = tk.StringVar()
        self.control_timer_var.set("00:00:00")
        """
        # Render main window
        self.render_main_window(master)

    def auto_scale_label(self, label, base_font_name="Helvetica", weight="bold"):
        """
        Ligat la <Configure>, calculează dinamic un font-size
        care să umple cât mai mult spațiul din Label.
        """
        def on_resize(event):
            width = label.winfo_width()
            height = label.winfo_height()

            # Heuristica simplă: font-size ca 75% din înălțime
            new_size = int(height * 0.75)

            # Poți adăuga verificări extra dacă textul e prea lung față de lățime
            # ex.:
            # if len(label.cget('text')) > 0:
            #     candidate_w = int(width / len(label.cget('text')) * 1.3)
            #     new_size = min(new_size, candidate_w)

            if new_size < 5:
                new_size = 5

            label.config(font=(base_font_name, new_size, weight))

        label.bind("<Configure>", on_resize)


    # Method to clear the current screen content (but not the main window or global components)
    def clear_screen(self):
        for widget in self.master.winfo_children():
             if isinstance(widget, tk.Widget):  # Check if it's a widget that supports grid_forget
                    widget.grid_forget()

        # If needed, reset any specific state related to canvas, frame, etc.
#         if hasattr(self, 'canvas'):
#             self.canvas.delete("all")  # Clears everything on the canvas

        # Clear the app_frames dictionary
        self.app_frames.clear()

          # clear buttons dictionary
        self.button_manager.buttons.clear()

    # main frame props / position / width etc
    def render_main_window(self, master):

        # In MainApp or another class that has an instance of Ui:
        self.ui.create_window(
            title='Campionatul National Bouldering 2025',
            width=1200,
            height=1050,
            resizable=(True, True),
            bg=self.dark_blue_color
        )

        # Clear current content before rendering
        self.clear_screen()

        # Create the button frame and center it using grid
        self.contest_select_frame = self.ui.create_frame(
            'contest_select_frame',
            self.master,
            row=1,
            column=0,
            bg=self.dark_blue_color,
            padx=20,
            pady=20,
            sticky="nsew"
        )

        #render main logo screen
        self.ui.render_logo(self.contest_select_frame)

        # Text box for frame
        self.ui.render_text(
            'Campionatul National de Bouldering 2025',
            self.contest_select_frame,
            1,
            0,
            3,
            sticky="ew",
            font=self.default_font,
            bg=self.dark_blue_color,
            padx=40,
            pady=40
        )

        # Render Start CNB 2025 button
        self.button_manager.render_button(
            self.contest_select_frame,
            'Start CNB',
            2,
            1,
            self.render_control_screen,
            sticky="nsew"
        )

        # Configure columns for self.contest_select_frame
        self.ui.configure_grid(self.contest_select_frame,'col',positions=[0, 1, 2],weights=[1, 1, 1])

        # Configure rows for self.master
        self.ui.configure_grid(self.master,'row',positions=[0, 1, 2],weights=[1, 0, 1])

    def render_control_screen(self):

        # baypass password for debug
        if DEBUG:
            self.authentication.is_user_logged_in = DEBUG

        # If user is not logged in, start authentication
        if not self.authentication.is_user_logged_in:
            self.authentication.authenticate_user(self.render_control_screen)
            return

        # hide splash frame screen
        self.ui.hide_frame('contest_select_frame')

        # Make new frame in master frame
        self.competitors_frame = self.ui.create_frame(
            'competitors_frame',
            self.master,
            row=0,
            column=0,
            padx=20,
            pady=20,
            bg=self.dark_blue_color
        )
        # Text box for frame
        self.competitors_listbox_message = self.ui.render_text(
            'Panou Control CNB 2025',
            self.competitors_frame,
            0,
            0,
            4,
            font=self.default_font,
            bg=self.dark_blue_color
        )

        # Select contest type label
        self.select_type_label = self.ui.render_text(
            'Select contest type',
            self.competitors_frame,
            1,
            0,
            1,
            sticky="w",
            font=self.input_font,
            bg=self.dark_blue_color,
            pady=0
        )

        # Creează un Menubutton "Duplicate..." pe rândul 1, col 3
        duplicate_menu = tk.Menubutton(self.competitors_frame, text="Duplicate...", relief=tk.RAISED, font=('Helvetica',12))
        menu = tk.Menu(duplicate_menu, tearoff=0)
        menu.add_command(label="Duplicate Timer", command=self.create_timer_duplicate_window)
        menu.add_command(label="Duplicate Contest State", command=self.create_state_duplicate_window)
        duplicate_menu.config(menu=menu)
        duplicate_menu.grid(row=1, column=3, sticky="ew", padx=5)
        duplicate_menu.config(state=tk.DISABLED)
        self.duplicate_menu = duplicate_menu  # păstrează referința
 
        self.contest_type_var = tk.StringVar(value="Select type")
        self.type_dropdown = self.ui.create_dropdown(
            self.competitors_frame,
            self.contest_type_var,
            list(self.contest_types.keys()),
            row=2,
            column=0,
            callback=lambda e: self.contest_type_selected(self.contest_type_var.get()),
            font=self.input_font
        )

        # Text box for frame
        self.contest_type_label = self.ui.render_text(
            'Route number',
            self.competitors_frame,
            1,
            1,
            1,
            sticky="w",
            font=self.input_font,
            bg=self.dark_blue_color
        )

 
        self.route_num_var = tk.StringVar(value="Select routes")
        self.route_dropdown = self.ui.create_dropdown(
            self.competitors_frame,
            self.route_num_var,
            [str(v) for v in range(1, 31)],
            row=2,
            column=1,
            callback=lambda e: self.routes_number_selected(self.route_num_var.get()),
            font=self.input_font
         )

        csv_files = {
            "Seniori": "db/Seniori.csv",
            "Senioare": "db/Senioare.csv",
            "U21B": "db/U21B.csv",
            "U21F": "db/U21F.csv",
            "U19B": "db/U19B.csv",
            "U19F": "db/U19F.csv",
            "U15B": "db/U15B.csv",
            "U15F": "db/U15F.csv",
            "U13B": "db/U13B.csv",
            "U13F": "db/U13F.csv",
            "U11B": "db/U11B.csv",
            "U11F": "db/U11F.csv"
        }
        self.category_var = tk.StringVar(value="Load competitors/category")
        self.category_dropdown = self.ui.create_dropdown(
            self.competitors_frame,
            self.category_var,
            list(csv_files.keys()),
            row=3,
            column=0,
            callback=lambda e: self.cm.load_competitors(self.competitors_listbox, csv_files[self.category_var.get()]) and self.is_contest_ready(),
            font=self.input_font
        )
        

        # Create Listbox for competitors
        self.competitors_listbox = tk.Listbox(
            self.competitors_frame,
            height=5,
            width=10,
            selectmode=tk.MULTIPLE,
            font=self.selector_font
        )
        self.competitors_listbox.grid(row=4, column=0, columnspan=2, padx=0, pady=0, sticky="we")
        self.toggle_competitors_listbox(enabled=True, update_callback=self.cm.set_competitors)

        self.button_manager.render_button(
            self.competitors_frame,
            'Delete list',
            3,
            1,
            lambda: self.cm.delete_competitors(self.competitors_listbox),
            sticky="ew",
            padx=5
        )
        self.toggle_button('Delete list', False)

        # Render add competitor button horizontally centered
        # Leave this below competitors_listbox
        self.button_manager.render_button(
            self.competitors_frame,
            'Add competitor',
            3,
            2,
            self.cm.add_competitor,
            sticky="ew",
            padx=5
        )

        self.button_manager.render_button(
            self.competitors_frame,
            'Rankings',
            3,
            3,
            self.ranking_manager.show_rankings,
            sticky="ew",
            padx=5,
            state=tk.DISABLED
        )

        # Lock screens for contest
        self.button_manager.render_button(
            self.competitors_frame,
            'Update Competitors',
            5,
            0,
            self.update_competitors_from_listbox,
            sticky="ew"
        )
        self.button_manager.render_button(
            self.competitors_frame,
            'Lock app',
            6,
            0,
            self.lock_app,
            sticky="ew",
        )
 
        # Render "Initiate contest" button (row 4)
        self.button_manager.render_button(
            self.competitors_frame,
            'Initiate contest',
            5,
            3,
            self.start_contest,
            text_color=self.red_color,
            font=("Helvetica", 35, "bold"),
            sticky="ew"
        )
        self.toggle_button('Initiate contest', False)
        
        # Configurează grid-ul pentru layout responsive
        for col in range(4):
            self.competitors_frame.grid_columnconfigure(col, weight=1)
        for row in range(8):
            self.competitors_frame.grid_rowconfigure(row, weight=1)

        # Label timer for CONTROL TIMER
        self.control_timer_var = tk.StringVar()
        self.control_timer_var.set('00:00:00')
        self.ui.render_text(
            self.control_timer_var,
            self.competitors_frame,
            6,
            3,
            1,
            sticky="ew",
            font=self.control_timer_font,
            bg=self.dark_blue_color,
            fg=self.white_color
        )

        # Text box for CONTROL TIMER
        self.ui.render_text(
            'Control timer',
            self.competitors_frame,
            7,
            3,
            1,
            sticky="nsew",
            font=self.input_font,
            bg=self.dark_blue_color,
            padx=0,
            pady=0
        )
        tk.Label(self.competitors_frame, bg=self.dark_blue_color, text="Font C.Zone:   -->", font=self.small_font).grid(row=4, column=2, sticky="nw")
        self.izolare_font_size_var = tk.IntVar(value=32)
        tk.Spinbox(self.competitors_frame, from_=10, to=100, textvariable=self.izolare_font_size_var, width=5).grid(row=4, column=2, sticky="ne")

        tk.Label(self.competitors_frame, bg=self.dark_blue_color, text="Font Routes:   -->", font=self.small_font).grid(row=4, column=2, sticky="w")
        self.trasee_font_size_var = tk.IntVar(value=40)
        tk.Spinbox(self.competitors_frame, from_=10, to=300, textvariable=self.trasee_font_size_var, width=5).grid(row=4, column=2, sticky="e")
        
        tk.Label(self.competitors_frame, bg=self.dark_blue_color, text="Font Timer:     -->", font=self.small_font).grid(row=4, column=2, sticky="sw")
        self.timer_clock_font_size_var = tk.IntVar(value=165)
        tk.Spinbox(self.competitors_frame, from_=10, to=1000, textvariable=self.timer_clock_font_size_var, width=5).grid(row=4, column=2, sticky="se")

        def apply_font_settings():
            size1 = self.izolare_font_size_var.get()
            size2 = self.trasee_font_size_var.get()
            size3 = self.timer_clock_font_size_var.get()
            self.izolare_font = (self.font_face, size1, "bold")
            self.trasee_font = (self.font_face, size2, "bold")
            self.timer_clock_font = (self.font_face, size3, "bold")
            if self.time_text:  # <- dacă textul din cronometru există
                self.canvas.itemconfig(self.time_text, font=self.timer_clock_font)
            self.update_display_window_contest()  # Reafișează cu noile fonturi

        self.button_manager.render_button(
            self.competitors_frame,
            'Apply Fonts',
            4,
            3,
            apply_font_settings,
            sticky="we"
        )
        self.button_manager.toggle_button('Apply Fonts', False)

     #create crb delection
        self.button_manager.render_button(
            self.competitors_frame,
            'Switch to CRB',
            2,
            3,
            self.toggle_crb_mode,
            sticky="ew",
            padx=5
        )

    def render_common_timer_buttons(self, frame, start_timer_cmd, reset_timer_cmd, global_sync_cmd):
        self.button_manager.render_button(
            frame, 'Start time', 5, 2, start_timer_cmd, sticky="ew"
        )
        self.button_manager.render_button(
            frame, 'Start global time sync', 6, 2, global_sync_cmd, sticky="ew"
        )
        self.button_manager.render_button(
            frame, 'Reset All Timers', 6, 1, reset_timer_cmd, sticky="ew"
        )


    def category_selected(self, category, popup):
        file_path = f"db/{category}.csv"
        result = self.cm.load_competitors(self.competitors_listbox, file_path)
        self.save_competitors_status(result)
        popup.destroy()
        self.is_contest_ready()

        # Configure the col grid
        self.ui.configure_grid(self.competitors_frame,'col',positions=[0, 1, 2, 3],weights=[1, 1, 1, 1])

        # Configure the row grid
        self.ui.configure_grid(self.competitors_frame,'row',positions=[0, 1, 2, 3, 4, 5, 6, 7],weights=[1, 1, 1, 1, 1, 1, 0, 0])

    def toggle_crb_mode(self):
        self.is_crb_mode = not getattr(self, 'is_crb_mode', False)

        if self.is_crb_mode:
            self.competitors_listbox_message.config(text="Panou Control CRB 2025")
            self.type_dropdown.grid_remove()
            self.select_type_label.grid_remove()
            self.type_dropdown.update_idletasks()

        if self.is_crb_mode:
            self.competitors_listbox_message.config(text="Panou Control CRB 2025")
            self.type_dropdown.grid_remove()
            self.select_type_label.grid_remove()
            self.type_dropdown.update_idletasks()

            def crb_contest_ready():
                competitors_exist = len(self.competitors_listbox.get(0, tk.END)) > 0
                contest_ready = self.dynamic_routes_number > 0 and competitors_exist
                self.toggle_button('Initiate contest', contest_ready)
                return contest_ready

            self.is_contest_ready = crb_contest_ready
            self.button_manager.alter_button("Switch to CRB", text="Switch to CNB", command=self.toggle_crb_mode)
        else:
            self.competitors_listbox_message.config(text="Panou Control CNB 2025")
            self.type_dropdown.grid()
            self.select_type_label.grid()
            self.type_dropdown.update_idletasks()

            # Revine la metoda originală
            self.is_contest_ready = self.__class__.is_contest_ready
            self.button_manager.alter_button("Switch to CRB", text="Switch to CRB", command=self.toggle_crb_mode)
   
    def toggle_competitors_listbox(self, enabled=True, update_callback=None):

        events = {
            "<Delete>": self.cm.delete_competitor,
            "<Double-1>": lambda event: self.cm.enable_inline_edit(
                self.competitors_listbox,
                self.selector_font,
                update_callback
            ),
            "<ButtonPress-1>": self.cm.on_competitor_press,
            "<B1-Motion>": self.cm.on_competitor_motion,
            "<ButtonRelease-1>": self.cm.on_competitor_release
        }

        self.competitors_listbox.config(state=tk.NORMAL if enabled else tk.DISABLED)

        # Loop through the dictionary and either bind or unbind the events
        for event, func in events.items():
            if enabled:
                self.competitors_listbox.bind(event, func)  # Enable event
            else:
                self.competitors_listbox.bind(event, lambda event: "break")  # Disable event


    def update_contest_controls(self):
        """Updates contest controls based on contest readiness."""

        is_ready = self.authentication.is_user_logged_in

        # Determine states
        general_buttons_enabled = is_ready and not self.app_locked
        contest_buttons_enabled = self.contest_started and not self.app_locked
        self.update_competitors_from_listbox()
        has_competitors = bool(self.cm.get_competitors())
 
        # Button state mapping
        button_states = {
            "Initiate contest": general_buttons_enabled and not self.contest_started,
            "Start time": general_buttons_enabled,
            "Rotate competitors": general_buttons_enabled,
            "Reset All Timers": general_buttons_enabled,
            "Update Competitors": general_buttons_enabled,
            "Apply Fonts": contest_buttons_enabled,
            "Add competitor": contest_buttons_enabled,
            "Delete list": contest_buttons_enabled and has_competitors
        }
 
        # Apply all button states
        for button_name, enabled in button_states.items():
            self.toggle_button(button_name, enabled)
        
        
        # Competitor list
        self.toggle_competitors_listbox(enabled=is_ready)

        # Inputs & selectors
        state = tk.DISABLED if not is_ready else tk.NORMAL

        self.route_dropdown.config(state="readonly" if is_ready else "disabled")
        self.type_dropdown.config(state="readonly" if is_ready else "disabled")
        self.category_dropdown.config(state="readonly" if is_ready else "disabled")

        input_state = "disabled" if not is_ready else "normal"


        if hasattr(self, 'canvas') and self.canvas:
            # Disable canvas interaction if not ready
            if not is_ready:
                self.canvas.bind("<Button-1>", lambda event: None)
                self.canvas.bind("<B1-Motion>", lambda event: None)
                self.canvas.bind("<Configure>", lambda event: None)
            else:
                # Re-enable canvas interactions if the contest is ready
                self.canvas.bind("<Button-1>", self.timer.on_bar_click)
                self.canvas.bind("<B1-Motion>", self.timer.on_bar_drag)
                self.canvas.bind("<Configure>", self.on_canvas_resize)

    def lock_app(self):

        self.app_locked = True
        self.authentication.is_user_logged_in = False

        # Update contest controls
        self.update_contest_controls()

        self.button_manager.alter_button('Lock app', text='Unlock app', command=self.unlock_app, text_color="red")
        logging.info("🔒 Aplicația a fost blocată.")

        # Prevent main window
        self.ui.block_window(self.master)


    def unlock_app(self):
        
        self.app_locked = False
        # If user is not logged in, start authentication
        if not self.authentication.is_user_logged_in:
            self.authentication.authenticate_user(self.unlock_app)
            return

        # Update contest controls
        self.update_contest_controls()

        self.button_manager.alter_button('Lock app', text='Lock app', command=self.lock_app, text_color="white")
        logging.info("🔓 Aplicația a fost deblocată.")

        if hasattr(self, 'lock_label'):
            self.lock_label.grid_forget()

        # Prevent main window
        self.ui.unblock_window(self.master)

    def save_competitors_status(self, result):
        self.competitors_loaded = result

    def routes_number_selected(self, event=None):
        selected_value = get_selected_value(self.route_num_var)  # Get value using the main method

        if selected_value is not None:
            self.dynamic_routes_number = selected_value  # Store the selected value
            self.is_contest_ready()
            logging.debug(f"Selected routes: {self.dynamic_routes_number}")


    def contest_type_selected(self, event=None):
        selected_value = get_selected_value(self.contest_type_var, self.contest_types)

        if selected_value is not None:
            self.contest_type = selected_value
            if self.contest_type == "qualifiers":
                self.ask_pause_duration()
            self.is_contest_ready()

            logging.debug(f"Selected contest type: {self.contest_type}")


    def is_contest_ready(self):
        logging.debug("Checking contest readiness...")

        # Get the number of competitors currently in the listbox
        competitors_list = list(self.competitors_listbox.get(0, tk.END))
        competitors_exist = len(competitors_list) > 0

        logging.debug(f"Number of competitors in list: {len(competitors_list)}")
        logging.debug(f"Have competitors been added manually?: {competitors_exist}")

        # Contest is ready if:
        # - A contest type is selected
        # - At least 1 dynamic route is selected
        # - EITHER competitors are loaded from CSV OR at least one competitor was added manually
        contest_ready = (
            self.contest_type is not None
            and self.dynamic_routes_number > 0
            and (self.competitors_loaded or competitors_exist)  # Either one should be True
           # and self.competitors_loaded  # Either one should be True
        )
        self.toggle_button('Initiate contest', contest_ready)
        return contest_ready
    
        logging.debug(f"Is contest ready? {contest_ready}")

        # Toggle button visibility based on readiness
        self.toggle_button('Initiate contest', contest_ready)

        return contest_ready
    
    def ask_pause_duration(self):
        duration = simpledialog.askinteger(
            "Pauză între trasee",
            "Introduceți durata pauzei între trasee (minute):",
            minvalue=1,
            maxvalue=60
        )

        if duration is not None:
            self.pause_duration = duration
            logging.debug(f"Pauză setată la {self.pause_duration} minute.")
        else:
            messagebox.showerror("Eroare", "Trebuie să introduceți durata pauzei!")

    def start_global_time_sync(self):
        input_time = self.global_time_input_field.get()
        try:
            target_time = datetime.strptime(input_time, '%H:%M:%S').time()
            now = datetime.now().time()
            now_seconds = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second).total_seconds()
            target_seconds = timedelta(hours=target_time.hour, minutes=target_time.minute, seconds=target_time.second).total_seconds()
            delay = target_seconds - now_seconds

            if delay < 0:
                messagebox.showerror("Eroare", "Ora specificată a trecut deja!")
                return

            messagebox.showinfo("Timer setat", f"Timer-ul va porni automat la {input_time}.")
            self.master.after(int(delay * 1000), self.timer.start_timer)
            self.master.after(int(delay * 1000), lambda: self.toggle_button("Start time", True))
            
        except ValueError:
            messagebox.showerror("Eroare", "Format oră invalid! Folosește hh:mm:ss.")
        if delay > 0:
            self.toggle_button("Start time", False)
            self.master.after(int(delay * 1000), lambda: self.toggle_button("Start time", True))

    # start the contest screens
    def start_contest(self):
        if getattr(self, 'is_crb_mode', False):
            self.contest_type = 'crb'
            self.render_timer_window(crb_mode=True)

            self.global_time_input_field = tk.Entry(self.competitors_frame)
            self.global_time_input_field.grid(
                row=7,
                column=2,
                padx=5,
                pady=5,
                sticky="ew"
            )
            self.global_time_input_field.insert(0, "hh:mm:ss")
            self.global_time_input_field.focus_set()

            self.toggle_button("Start time", True)
            self.toggle_button("Start global time sync", True)
        

        # Dezactivează etapa de preview (8 minute) exclusiv pentru calificări
        if self.contest_type == 'qualifiers':
            self.timer.preview_completed = True
        self.contest_competitors = self.cm.get_competitors()

        # prepare competitors
        self.contest_competitors = [
            {"name": name, "start": None, "state": 'Call_zone', "transit_status": False}
            for name in self.contest_competitors
        ]

        # set contest_competitors to isolation
        self.isolation1_contest = [comp["name"] for comp in self.contest_competitors if comp.get("state") == 'Call_zone']
        # Activează butonul Rankings după începerea competiției
        self.toggle_button('Rankings', True)

        logging.debug(f"Izolation1: {self.isolation1_contest}")

        # Render buttons in the first row (row 0) with equal width
        self.render_common_timer_buttons(
            self.competitors_frame,
            start_timer_cmd=self.timer.start_timer,
            reset_timer_cmd=self.timer.reset_timer,
            global_sync_cmd=self.start_global_time_sync
        )

        # generate routes like T1, T2, ... etc
        self.generate_dynamic_routes()

        # Split competitors into Group A & Group B (before rendering) for qualifiers only
        if self.contest_type == 'qualifiers':
            self.generate_qualifiers_groups()
        elif self.contest_type in ['semifinals', 'finals']:
            self.generate_semifinals_finals_contest_competitors()

        if not getattr(self, 'is_crb_mode', False):
            # everything is set we open timer
            self.render_timer_window()

            # open secondary standings window
            self.render_contest_standings_window()

        # Global time sync input and button
        self.global_time_input_field = tk.Entry(self.competitors_frame)
        self.global_time_input_field.grid(
            row=7,
            column=2,
            padx=5,
            pady=5,
            sticky="ew"
        )
        self.global_time_input_field.insert(0, "hh:mm:ss")  # Placeholder for format guidance
        self.global_time_input_field.focus_set()
        self.button_manager.toggle_button('Apply Fonts', True)
        self.duplicate_menu.config(state=tk.NORMAL)
        self.contest_started = True
        self.toggle_button("Initiate contest", False)
        self.update_contest_controls()

        self.toggle_button("Start time", True)
        self.toggle_button("Start global time sync", True)

    def open_duration_dialog(self, callback):
            """
            Deschide o fereastră Toplevel pentru a introduce timpul în format MM:SS.
            După validare, apelează `callback(total_seconds)`.
            """
            window = tk.Toplevel(self.master)
            window.title("Setare durată")
            window.geometry("300x150")
            window.configure(bg="lightgray")
            window.grab_set()  # modal behavior

            tk.Label(window, text="Introduceți durata (MM:SS):", font=self.input_font, bg="lightgray").pack(pady=10)

            duration_var = tk.StringVar()
            entry = tk.Entry(window, textvariable=duration_var, font=self.input_font, justify="center", width=10)
            entry.pack(pady=5)
            entry.focus_set()

            def submit():
                val = duration_var.get().strip()
                try:
                    minutes, seconds = map(int, val.split(":"))
                    total_seconds = minutes * 60 + seconds
                    window.destroy()
                    callback(total_seconds)
                except Exception:
                    messagebox.showerror("Eroare", "Format invalid. Folosiți MM:SS\n(ex: 04:30)")

            tk.Button(window, text="OK", font=self.input_font, command=submit).pack(pady=10)
            entry.bind("<Return>", lambda e: submit())

    def reset_app_to_start(self):
        confirm = messagebox.askyesno("Confirm Reset", "Ești sigur că vrei să închizi concursul și să revii la ecranul principal?")
        if not confirm:
            return

        # Închide toate ferestrele Toplevel dacă există
        if self.timer_window:
            self.ui.close_window(self.timer_window)
            self.timer_window = None
        if self.state_window:
            self.ui.close_window(self.state_window)
            self.state_window = None
        if self.competitors_window:
            self.ui.close_window(self.competitors_window)
            self.competitors_window = None

        self.parent.toggle_button("Initiate contest", True)
        self.parent.contest_started = False  # reset și flag-ul

        # Șterge tot din fereastra principală
        self.clear_screen()

        # Reafișează ecranul principal
        self.render_main_window(self.master)


    def render_timer_window(self, crb_mode=False):

        window_title = self.get_contest_title_by_contest_type() if not crb_mode else "CRB"
        # Create a new window
        self.timer_window = self.ui.create_window(
            title=f'Cronometru {window_title}',
            is_toplevel=True,
            width=800,
            height=220,
            resizable=(True, True),
            position="tr"
        )

        # Prevent the window from closing
        self.ui.block_window(self.timer_window)

        # Create a frame for the contest window
        self.timer_frame = self.ui.create_frame('timer_frame', self.timer_window, row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Configure column
        self.ui.configure_grid(self.timer_frame,'col',positions=[0],weights=[1])

        # Configure rows
        self.ui.configure_grid(self.timer_frame,'row',positions=[0],weights=[1])

        # build canvas to put time bar on
        self.canvas_width = 800
        self.canvas_height = 220
        self.canvas = tk.Canvas(self.timer_window, width=self.canvas_width, height=self.canvas_height)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # create bar
        self.bar_background = self.canvas.create_rectangle(0, 0, self.canvas_width, self.canvas_height, fill=self.red_color)

        self.bar = self.canvas.create_rectangle(0, 0, self.canvas_width, self.canvas_height, fill=self.blue_light_color)

        self.time_text = self.canvas.create_text(
            self.canvas_width // 2,
            self.canvas_height // 2,
            text=self.get_formatted_time(self.timer.remaining_time),
            font=self.timer_clock_font
        )

        if crb_mode:
            self.open_duration_dialog(self.timer.set_manual_timer)

        # Adjust the vertical alignment based on the actual text size
        self.canvas.update_idletasks()  # Ensure the text is drawn
        bbox = self.canvas.bbox(self.time_text)  # Get text bounding box (x1, y1, x2, y2)

        # Update timer text position in canvas on TIMER WINDOW
        self.update_text_position(self.canvas, self.time_text)

        # Bring the time text to the front
        self.canvas.tag_raise(self.time_text)

        # Lower the red bar to the back
        self.canvas.tag_lower(self.bar)

        # lower background
        self.canvas.tag_lower(self.bar_background)

        self.canvas = self.canvas

        # add buttons to bar for interaction
        self.canvas.bind("<Button-1>", self.timer.on_bar_click)
        self.canvas.bind("<B1-Motion>", self.timer.on_bar_drag)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Call initialize_bar to make sure the bar is 100% width when the screen is first rendered
        self.timer.initialize_bar()


    def get_formatted_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes):02d}:{int(seconds):02d}"

    def update_text_position(self, canvas, text_to_update):
        """Reposition the text in the canvas, centering it both vertically and horizontally."""
        canvas.update_idletasks()  # Ensure the text is drawn

        # Get the bounding box of the text (x1, y1, x2, y2)
        bbox = canvas.bbox(text_to_update)

        if bbox:
            # Calculate text height and font line height
            text_height = bbox[3] - bbox[1]  # Height of the text
            text_baseline = bbox[1]  # Y position of the top baseline of the text

            # Calculate center of the canvas
            canvas_center_y = canvas.winfo_height() / 2

            # Calculate the center of the text
            text_center_y = text_baseline + text_height / 2

            # Calculate the vertical offset to center the text
            vertical_offset = (canvas_center_y - text_center_y)

            # Optionally, you can adjust this with a constant for fine-tuning the vertical position
            vertical_offset += 0  # Fine-tune if necessary (e.g., add small constant if needed)

            # Set the new coordinates for the text to be perfectly aligned vertically in the center
            canvas.coords(text_to_update, canvas.winfo_width() // 2, canvas_center_y + vertical_offset)



    def on_canvas_resize(self, event):

        """Adjust elements when the window resizes."""
        width = event.width
        height = event.height

        # Resize the background bar to fill the entire canvas
        self.canvas.coords(self.bar_background, 0, 0, width, height)

        # Resize progress bar (keep full width initially)
        self.canvas.coords(self.bar, 0, 0, width, height)

        # Recenter the time text
        self.canvas.coords(self.time_text, width // 2, height // 2)


    def render_contest_standings_window(self):

        window_title = self.get_contest_title_by_contest_type()

        # Create a new window
        self.state_window = self.ui.create_window(
            title=f'Contest State {window_title}',
            is_toplevel=True,
            width=800,
            height=800,
            resizable=(True, True),
            position="bl"
        )
        self.state_window.configure(bg="lightblue")

        # Prevent the window from closing
        self.ui.block_window(self.state_window)

        # Create the frame inside the window
        self.state_frame = self.ui.create_frame(
            'state_frame',
            self.state_window,
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="nsew",
            bg=Config.COLORS["gray"]
        )

        # Update the content dynamically
        self.update_display_window_contest()

    def generate_dynamic_routes(self):
        if self.dynamic_routes_number == 0:
            return

        self.dynamic_routes = [f"T{i+1}" for i in range(self.dynamic_routes_number)]

    def generate_qualifiers_groups(self):
        total_competitors = len(self.contest_competitors)
        mid_index = total_competitors // 2

        # If the total number of competitors is odd, the first group will have one extra competitor
        self.group_A = self.contest_competitors[:mid_index + (total_competitors % 2)]  # First half
        self.group_B = self.contest_competitors[mid_index + (total_competitors % 2):]  # Second half

        # 🟡 Split routes for each group
        total_routes = self.dynamic_routes_number
        mid_routes = total_routes // 2

        # Adjust to give the first group (A) one extra route if the total number of routes is odd
        if total_routes % 2 == 1:
            route_count = mid_routes + 1
        else:
            route_count = mid_routes

        self.routes_A = self.dynamic_routes[:route_count]
        self.routes_B = self.dynamic_routes[route_count:]


    def generate_semifinals_finals_contest_competitors(self):
        self.all_routes = self.contest_competitors[:]


    # Updated method to update transit status for dynamic routes
    def update_transit_status(self):

        logging.debug(f"Competitors status before transit {self.contest_competitors}")

        # Update transit status based on the dynamic routes
        for comp in self.contest_competitors:
            if self.contest_type == "qualifiers":
                if comp in self.group_A and comp["state"] == self.routes_A[-1] or comp["state"] == "Concurs":
                    logging.debug(f"Transit if Group A: {comp['name']}")
                    comp["state"] = "Concurs"
                    comp["transit_status"] = False
                    continue
                elif comp in self.group_B and comp["state"] == self.routes_B[-1] or comp["state"] == "Concurs":
                    logging.debug(f"Transit if Group B: {comp['name']}")
                    comp["state"] = "Concurs"
                    comp["transit_status"] = False
                    continue
            else:
                if comp["state"] == self.dynamic_routes[-1] or comp["state"] == "Concurs":
                    logging.debug(f"Transit if")
                    comp["state"] = "Concurs"
                    comp["transit_status"] = False
                    continue

            if comp.get("state") and comp["state"].startswith("T"):
                logging.debug(f"Transit elif")
                comp["state"] = 'izolare2'
                comp["transit_status"] = True if self.timer.transit else False
            else:
                logging.debug(f"Transit else")
                comp["transit_status"] = False

        self.isolation2_contest = [comp["name"] for comp in self.contest_competitors if "izolare2" in (comp.get("state") or "")]

        logging.debug(f"Competitors status after transit {self.contest_competitors}")

    def update_display_window_contest(self):

        if getattr(self, 'is_crb_mode', False):
            logging.debug("CRB mode activ: nu se actualizează display window contest.")
            return
        logging.debug(f"Updating display window for contest type: {self.contest_type}")
        if not hasattr(self, 'current_round'):
            self.current_round = 'Runda 1'

        if self.run_contest_finish() and self.timer.preview_completed:
            self.current_round = 'Runda 2'
        elif self.timer.running and not self.timer.preview_completed:
            self.current_round = 'Runda x'

        # Ensure we have dynamic routes generated
        if not hasattr(self, 'dynamic_routes') or not self.dynamic_routes:
            return  # Exit early if routes are not available

        # 🟡 UPDATE CLASS VARIABLES FOR DISPLAY
        if self.contest_type == "qualifiers":
 
            # 🟡 Display Call Zone with Groups (show only next 3 competitors)
            visible_A = [comp["name"] for comp in self.group_A if comp.get("state") == 'Call_zone'][:3]
            visible_B = [comp["name"] for comp in self.group_B if comp.get("state") == 'Call_zone'][:3]
            txt_iz1_A = "Grupa A:\n" + "\n".join(visible_A) if visible_A else "Grupa A:\n - "
            txt_iz1_B = "Grupa B:\n" + "\n".join(visible_B) if visible_B else "Grupa B:\n - "
            txt_iz1 = f"{txt_iz1_A}\n\n{txt_iz1_B}"

            # 🟡 Display Routes (Trasee) split into Grupa A & Grupa B
            trasee_text = "Grupa A:\n"
            trasee_text = f"{self.current_round}\n\n" + trasee_text
            for route in self.routes_A:
                occupant = next((comp["name"] for comp in self.contest_competitors if comp["state"] == route), None)
                transit_status = next((comp["transit_status"] for comp in self.contest_competitors if comp["state"] == route), False)
                trasee_text += f"{route}: {occupant or 'Liber'}\n"

            trasee_text += "\nGrupa B:\n"

            for route in self.routes_B:
                occupant = next((comp["name"] for comp in self.contest_competitors if comp["state"] == route), None)
                transit_status = next((comp["transit_status"] for comp in self.contest_competitors if comp["state"] == route), False)

                trasee_text += f"{route}: {occupant or 'Liber'}\n"

            # 🟡 Display Isolation 2 (Izolare 2) with Groups
            txt_iz2_A = "Grupa A:\n" + "\n".join([comp["name"] for comp in self.group_A if "izolare2" in (comp.get("state") or "")])
            txt_iz2_B = "Grupa B:\n" + "\n".join([comp["name"] for comp in self.group_B if "izolare2" in (comp.get("state") or "")])
            txt_iz2 = f"{txt_iz2_A}\n\n{txt_iz2_B}"

        else:
 
            # 🟡 Display Call Zone for Semifinale (show only next 3 competitors)
            visible_competitors = [comp["name"] for comp in self.all_routes if comp.get("state") == 'Call_zone'][:3]
            txt_iz1 = "\n".join(visible_competitors) if visible_competitors else "-"

            # 🟡 Display Routes (Trasee)
            trasee_text = ""
            for route in self.dynamic_routes:
                occupant = next((comp["name"] for comp in self.contest_competitors if comp["state"] == route), None)
                transit_status = next((comp["transit_status"] for comp in self.contest_competitors if comp["state"] == route), False)
                trasee_text += f"{route}: {occupant or 'Liber'}\n"

            # Informații pentru Izolare 2

            logging.debug(f"Izolation 2 on window update: {self.isolation2_contest}")
            txt_iz2 = "\n".join(self.isolation2_contest)

        # Contest ended change text
        if self.run_contest_finish():
            trasee_text = f"Pauzǎ între traseee!"


        # 🟡 Ensure empty sections still occupy space
        txt_iz1 = txt_iz1 if txt_iz1.strip() else " "  # Single space to prevent collapse
        trasee_text = trasee_text if trasee_text.strip() else " "
        txt_iz2 = txt_iz2 if txt_iz2.strip() else " "  # Single space to hold width

        # Render all cells at once
        self.ui.create_section(self.state_frame, 0, 0, "Call Zone", txt_iz1, self.izolare_font)
        self.ui.create_section(self.state_frame, 0, 1, "Trasee", trasee_text, self.trasee_font, bg_color=Config.COLORS["blue_light"])
        self.ui.create_section(self.state_frame, 0, 2, "Izolare 2", txt_iz2, self.izolare_font)

        # 🟡 Configure the grid (Applies to all contest types)
        self.ui.configure_grid(self.state_frame, 'row', positions=[0], weights=[1])
        self.ui.configure_grid(self.state_frame, 'col', positions=[0, 1, 2], weights=[1, 1, 1])
        self.state_frame.columnconfigure(0, minsize=150)  # Minimum width for column 0
        self.state_frame.columnconfigure(1, minsize=150)  # Minimum width for column 1
        self.state_frame.columnconfigure(2, minsize=150)  # Minimum width for column 2

    def run_contest_finish(self):
        """
        This method checks if all competitors are in the 'Concurs' state, and if so, ends the contest.
        """

        # Extract the names of competitors who are in the "Concurs" state
        contest_finished_competitors = [comp["name"] for comp in self.contest_competitors if comp.get("state") == "Concurs"]

        # If the number of competitors in "Concurs" is equal to the total number of competitors, end the contest
        if len(contest_finished_competitors) == len(self.contest_competitors):
            logging.debug("All competitors are in 'Concurs' state. Ending the contest.")
            if self.timer.preview_completed:
                # Dacă runda a doua a început, oprim timer-ul.
                self.timer.stop_timer()
            else:
                # Altfel, înseamnă că runda 1 s-a terminat și pornim pauza între runde.
                self.timer.start_pause_between_rounds()
            return True
        return False# Contest is still ongoing

    # pornesc pe trasee concurentii check
    def run_competitor_logic_general(self):

        if self.run_contest_finish():
            return

        # 🟡 Ensure rotation counter exists
        if not hasattr(self, 'rotation_contest'):
            self.rotation_contest = 0

        if self.contest_type == "finals":
            self.run_competitor_logic(self.dynamic_routes, self.contest_competitors)
        elif self.contest_type== "semifinals":
            self.run_competitor_logic(self.dynamic_routes, self.contest_competitors)
        elif self.contest_type == "qualifiers":
            self.run_competitor_logic(self.routes_A, self.group_A)
            self.run_competitor_logic(self.routes_B, self.group_B)

        self.isolation1_contest = [comp["name"] for comp in self.contest_competitors if comp.get('state') == 'Call_zone']
        self.isolation2_contest = [comp["name"] for comp in self.contest_competitors if comp.get('state') == 'izolare2']

        self.rotation_contest += 1

    def on_pause_finished(self):
        logging.debug("[Contest Logic] Pauza între runde terminată. Începe Runda 2.")

        # Inversează automat grupurile
        self.group_A, self.group_B = self.group_B, self.group_A

        # Resetăm stările concurenților pentru Runda 2
        for comp in self.contest_competitors:
            comp["state"] = 'Call_zone'
            comp["transit_status"] = False
            comp["start"] = None

        # Setați timerul pentru Runda 2
        self.timer.preview_completed = True
        self.timer.remaining_time = self.timer.initial_time
        self.timer.running = True

        # Schimbă textul din canvas la „Runda 2”
        self.canvas.itemconfig(self.time_text, text="Runda 2")

        # Anulează orice apelare programată a timerului (after_id)
        if self.timer.after_id is not None:
            self.master.after_cancel(self.timer.after_id)
            self.timer.after_id = None

        # Reinițializare rotații
        self.rotation_contest = 0

        # Pornește cronometru Runda 2 (4min)
        self.timer.countdown("4min")

        # Rulează logica inițială pentru concurenți (Runda 2)
        self.run_competitor_logic_general()

        # Actualizează interfața
        self.update_display_window_contest()

    def run_competitor_logic(self, routes = [], competitors = []):

        # 🟡 Assign START to the next competitor (one per rotation)
        for comp in competitors:
            if comp.get("start") is None:
                comp["start"] = self.rotation_contest
                break  # Only one competitor per rotation

        # 🟡 Update competitor states
        for comp in competitors:
            if comp.get("start") is None:
                continue  # Skip competitors not started

            delta = self.rotation_contest - comp["start"]  # Time since starting
            # Use 4 for finals, 2 for semifinals (adjust based on contest type)
            rounds_per_move = 4 if self.contest_type == "finals" else 2
            route_index = delta // rounds_per_move  # Move to next route every 2 or 4 rounds

            if route_index < len(routes):
                comp["state"] = routes[route_index]  # Update state based on the route

            # 🔹 Check if competitor should move to Concurs
            if route_index >= len(routes) - 1 and (delta % rounds_per_move >= 1):
                comp["state"] = "Concurs"
                continue  # If they've reached the final route, they go to Concurs

            # 🔹 Handle Izolare2 but don't override Concurs!
            # For semifinals, competitors stay in Izolare2 for only the first round (round 1).
            if self.contest_type in ["semifinals", "qualifiers"] and delta % rounds_per_move == 1 and comp["state"] not in ["Concurs"]:
                comp["state"] = "izolare2"
                continue  # Move on to the next competitor

            # For finals, competitors stay in Izolare2 for rounds 1, 2, and 3
            if self.contest_type == "finals" and 1 <= delta % rounds_per_move <= 3 and comp["state"] not in ["Concurs"]:
                comp["state"] = "izolare2"

    def get_contest_title_by_contest_type(self):
        """Returns the label (Calificări, Semifinale, Finală) based on contest_type."""
        return {v: k for k, v in self.contest_types.items()}.get(self.contest_type, "Calificări")
 
    def update_competitors_from_listbox(self):
        updated_list = []
        for line in self.competitors_listbox.get(0, tk.END):
            parts = line.split("|")
            name = parts[0].strip()
            club = parts[1].strip() if len(parts) > 1 else ""
            updated_list.append({"name": name, "club": club})

        if not self.contest_competitors:
            messagebox.showinfo("Update Competitors", "Concursul nu a fost pornit încă!")
            return

        if len(updated_list) != len(self.contest_competitors):
            messagebox.showerror("Error", "Numărul concurenților nu corespunde.")
            return

        for i in range(len(self.contest_competitors)):
            self.contest_competitors[i]["name"] = updated_list[i]["name"]

        # Update competitor manager with full structured list
        self.cm.set_competitors(updated_list)

        # Refresh contest display
        self.update_display_window_contest()
    
    def create_timer_canvas(self, parent_canvas):
                parent_canvas.create_text(
                    800, 600,
                    text="00:00",
                    font=self.timer_clock_font,
                    fill=self.white_color,
                    tag="time",
                    anchor="center"
    )
    
    
    def create_timer_duplicate_window(self):
        duplicate = tk.Toplevel(self.master)
        duplicate.title("Timer Duplicate")
        duplicate.geometry("800x600")

        canvas = tk.Canvas(duplicate, bg="black", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        self.create_timer_canvas(canvas)
        self.timer.external_timer_displays.append(canvas)
            
            


    def create_state_duplicate_window(self):
        print(">>> Duplicate Contest State window called (to be implemented)")

def run_app():
    warmup_audio()  # Încălzește buffer-ul audio pentru a evita întârzierile la primul sunet
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()
