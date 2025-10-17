# timer.py

import time
import logging
import threading
import numpy as np
import sounddevice as sd
import math
from tkinter import messagebox
from helpers.decorators import catch_exceptions, log_method_call

# Dicționar pentru configurarea timpilor de beep
BEEP_TIMINGS = {
    60: 1.0,    # La 60 secunde rămase, beep de 1 sec
    3: 0.5,     # La 3 secunde rămase, beep de 0.5 sec
    2: 0.5,     # La 2 secunde rămase, beep de 0.5 sec
    1: 0.5      # La 1 secundă rămasă, beep de 0.5 sec
}

# Configurare logging: nivelul poate fi schimbat (ex. DEBUG, INFO, WARNING, etc.)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Timer:

    def __init__(self, parent, ui, button_manager, authentication):
        self.parent = parent
        self.button_manager = button_manager
        self.ui = ui
        self.authentication = authentication

        # Setări pentru cronometru
        self.running = False
        self.transit = False
        self.manual_adjustment = False

        # Setări temporale folosind constantele definite
        self.initial_time = 4 * 60          # 4 minute = 240 secunde
        self.transit_time = 15              # 15 secunde
        self.remaining_time = self.initial_time
        self.paused_time = 0  # Store paused time
        self.preview_time = 8 * 60
        self.preview_completed = False # if 
        self.after_id = None
        self.external_timer_displays = []

    #------------------------------


    # Timer și funcția de countdown
    def start_timer(self):

        if self.parent.contest_type is None:
            return

        # self.reset_timer()

        # change Start button text
        self.button_manager.alter_button('Start time', text="Pause", command=self.pause_timer)

        if not self.running:
            self.running = True

            # Set the start time when starting the timer
            self.start_time = time.time()  # Capture the current time when the timer starts

        if self.parent.contest_type == "crb":
            self.manual_adjustment = True
            self.remaining_time = self.remaining_time  # utilizează timpul deja setat manual
        elif self.manual_adjustment:
            self.remaining_time = self.paused_time
        else:
            if self.parent.contest_type == "qualifiers":
                self.remaining_time = self.initial_time  # 4-minute countdown
            else:
                self.remaining_time = self.preview_time  # 8-minute preview

        # If the contest is qualifiers, use 4min countdown directly
        if self.parent.contest_type == "qualifiers":
            self.countdown(countdown_type="4min")
        elif self.parent.contest_type == "crb":
            self.countdown(countdown_type="4min")
        else:
            self.countdown(countdown_type="8min")
        
        self.parent.toggle_button("Start global time sync", False)
        self.parent.toggle_button("Start time", True)

    def start_pause_between_rounds(self):
        if hasattr(self.parent, 'pause_duration'):
            pause_seconds = self.parent.pause_duration * 60
            self.remaining_time = pause_seconds
            self.parent.canvas.itemconfig(self.parent.time_text, text="Pauză între trasee")
            self.running = True
            logging.debug(f"Start pauză între runde: {self.remaining_time} secunde.")
            self.countdown(countdown_type="pause")
        else:
            logging.error("Durata pauzei nu este setată!")
    
    def stop_timer(self):
        self.running = False
        if self.after_id is not None:
            self.parent.master.after_cancel(self.after_id)
            self.after_id = None
        self.parent.canvas.itemconfig(self.parent.time_text, text="STOP!")
    
    # Pauses the timer and stores the state
    def pause_timer(self):
        logging.debug("Paused timer")

        if self.running:
            self.running = False  # Stop the timer

            # Save the remaining time and current position of the bar
            self.paused_time = self.remaining_time
            self.paused_position = self.parent.canvas.coords(self.parent.bar)[2]  # Save the current position on the bar

            # change Start button text
            self.button_manager.alter_button('Start time', text="Resume", command=self.resume_timer)

    # Resumes the timer and sets the time to the last modified position
    def resume_timer(self):
        logging.debug("Resume timer")
        #time.time() - (self.initial_time - self.paused_time)

        if not self.running:
            self.running = True  # Start the timer again

            # Update the remaining time when resuming
            self.remaining_time = self.paused_time

            self.button_manager.alter_button('Start time', text="Pause", command=self.pause_timer)

            # If the preview has been completed, start the 4-minute countdown
            if self.remaining_time <= self.transit_time and self.transit:
                logging.debug("Resuming in transit timer")
                self.countdown(countdown_type="transit")
            elif self.preview_completed:
                logging.debug("Resuming in 4 minutes timer")
                self.countdown(countdown_type="4min")  # Start 4-minute countdown
            else:
                logging.debug("Resuming in 8 minutes timer")
                self.countdown(countdown_type="8min")  # Call countdown_8_minute method

    def reset_timer(self):

        confirm = messagebox.askyesno("Confirm Reset", "Ești sigur că vrei să resetezi complet aplicația?")
        if not confirm:
            return

        self.is_user_logged_in = self.authentication.is_user_logged_in

        # If user is not logged in, start authentication
        if not self.is_user_logged_in:
            self.authentication.authenticate_user(self.reset_timer)
            return

        logging.debug(f"Timer has been Reset!")


        # ✅ Reset all competitors' states
        for comp in self.parent.contest_competitors:
            comp["state"] = 'Call_zone'  # Remove any assigned routes
            comp["transit_status"] = False  # Reset transit status if needed
            comp["start"] = None

        # Set state flags to ensure it's reset to an idle state
        self.running = False
        self.transit = False
        self.remaining_time = self.preview_time  # Set to 8 minutes for preview
        self.preview_completed = True  # Reset preview completion flag
        self.manual_adjustment = False
        self.parent.rotation_count = 0
        self.parent.rotation_semifinala = 0
        self.parent.rotation_contest = 0
        self.parent.contest_finished = []
        self.dynamic_routes_number = 0
        self.dynamic_routes = []
        self.routes_A = []
        self.routes_B = []
        self.group_A = []
        self.group_B = []
        self.parent.isolation1_contest = self.parent.contest_competitors
        self.parent.isolation2_contest = []
        self.parent.contest_finished = []

        # Clear the progress bar and reset to 100%
        self.parent.canvas.coords(self.parent.bar, 0, 0, self.parent.canvas.winfo_width(), int(self.parent.canvas.winfo_height()))
        self.parent.canvas.update_idletasks()

        # Change the color of the time text to white
        self.parent.canvas.itemconfig(self.parent.time_text, fill=self.parent.black_color)

        self.button_manager.alter_button('Start time', text="Start time", command=self.start_timer)

        # Update timer and bar to reflect reset state
        self.update_timer()
        self.update_bar()

        # Initialize the bar to full width for 8-minute countdown
        self.initialize_bar()

        # Redraw time canvas
        self.parent.canvas.itemconfig(self.parent.bar, fill=self.parent.blue_light_color)

        # Redraw content
        self.parent.update_display_window_contest()
        
        if hasattr(self.parent, 'route_scores'):
            self.parent.route_scores.clear()

        if hasattr(self.parent.ranking_manager, 'rankings_frame') and self.parent.ranking_manager.rankings_frame:
            self.parent.ranking_manager.rankings_frame.grid_forget()

    @catch_exceptions
    def countdown(self, countdown_type="4min"):

        # Check if countdown is running
        if not self.running:
            return

        start_time = time.time()  # Measure execution time for delay adjustment

        # Update timer display and progress bar
        self.update_timer()
        self.update_bar()

        # Determine the countdown duration and beep timings
        countdown_map = {
            "8min": self.preview_time,
            "4min": self.initial_time,
            "transit": self.transit_time
        }
        total_time = countdown_map.get(countdown_type, self.remaining_time)

        # Use the BEEP_TIMINGS dictionary to determine if a beep should occur
        if self.remaining_time in BEEP_TIMINGS:
            self.beep(BEEP_TIMINGS[self.remaining_time])

        # time ends here
        if self.remaining_time == 0:
            beep_duration = 1.0

            # CRB: fără tranzit, fără altă logică
            if self.parent.contest_type == "crb":
                self.beep(beep_duration)
                self.stop_timer()
                self.parent.canvas.itemconfig(self.parent.time_text, text="STOP!", fill=self.parent.red_color)
                logging.debug("CRB timer finished — Concurs încheiat.")
                return

            if countdown_type == "pause":
                logging.debug("Pauza între runde terminată. Timer calls parent logic for next round.")
                self.beep(beep_duration)
                self.parent.on_pause_finished()
 
            # the countdown type is 4 minutes means we already run this
            elif countdown_type == "4min":
                self.beep(beep_duration)
                self.transit = True
                self.remaining_time = self.transit_time
                self.countdown("transit")
 
                # update in transit status
                self.parent.update_transit_status()
 
                # Redraw content
                self.parent.update_display_window_contest()
 
            else:
                self.beep(beep_duration)
                self.transit = False
                self.remaining_time = self.initial_time
                self.preview_completed = True
                self.countdown("4min")
 
                # run finals logic before transit state is over
                self.parent.run_competitor_logic_general()
 
                # Redraw content
                self.parent.update_display_window_contest()

        else:
            # When the remaining time reaches 3 seconds during the 4-minute countdown
            if countdown_type == "4min":
                self.parent.canvas.itemconfig(self.parent.bar, fill=self.parent.green_color)

                # Change the color of the time text to white
                self.parent.canvas.itemconfig(self.parent.time_text, fill=self.parent.white_color)

                # flassh the background
                if self.remaining_time == 3:
                    self.flash_bar_background_color(BEEP_TIMINGS[self.remaining_time])

            if countdown_type == "transit":

                # Change the bar's background color
                self.parent.canvas.itemconfig(self.parent.bar, fill=self.parent.blue_light_color)

                # Change the color of the time text to white
                self.parent.canvas.itemconfig(self.parent.time_text, fill=self.parent.black_color)

            self.remaining_time -= 1

            # Ensure remaining time doesn't go below 0
            if self.remaining_time < 0:
                self.remaining_time = 0

            # Calculate elapsed time and adjust the delay to maintain a 1-second interval
            elapsed_time = time.time() - start_time
            delay = max(1000 - int(elapsed_time * 1000), 1)  # Adjust delay for 1-second interval
            if self.after_id is not None:
                self.parent.master.after_cancel(self.after_id)
            self.after_id = self.parent.master.after(delay, self.countdown, countdown_type)  # Call countdown recursively with the same type

    def beep(self, duration_sec):
        # Redăm sunetul pe un thread separat pentru a nu bloca interfața
        def play_sound():
            fs = 44100
            t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
            data = np.sin(2 * np.pi * 440 * t)
            sd.play(data, fs)
        threading.Thread(target=play_sound, daemon=True).start()

    def adjust_time(self, new_time):
        # During transition, ensure the time is not set to more than 15 seconds
        if self.transit:
            new_time = min(new_time, self.transit_time)  # Ensure it's within the transition period

        self.paused_time = new_time
        self.remaining_time = new_time  # Update remaining_time based on the new time
        self.manual_adjustment = True  # Set flag indicating manual adjustment

        self.update_timer()  # Show updated time on screen
        self.update_bar()  # Show updated progress bar

    def on_bar_click(self, event):
        new_time = self.get_time_from_bar(event.x)  # Calculate time from bar
        self.adjust_time(new_time)  # Use the common method to adjust time

    def on_bar_drag(self, event):
        new_time = self.get_time_from_bar(event.x)  # Calculate time from bar
        self.paused_position = event.x  # Store the current position of the bar during drag
        self.adjust_time(new_time)  # Use the common method to adjust time

    def get_time_from_bar(self, x_position):
        bar_width = self.parent.canvas.winfo_width()
        ratio = x_position / bar_width
        total = self.get_total_time()

        # Calculate the time based on the ratio, but ensure it doesn't exceed the maximum time
        new_time = int(max(0, min(total, total * ratio)))

        return new_time

    # Updates display timer and its label
    def update_timer(self):
        minutes = math.floor(self.remaining_time // 60)  # Use math.floor to ensure int
        seconds = math.floor(self.remaining_time % 60)   # Use math.floor to ensure int

        # Format the time string
        time_text = f"{minutes:02d}:{seconds:02d}"

        # Update the CONTROL TIMER text
        self.parent.control_timer_var.set(time_text)

        # Update timer text on timer canvas
        self.parent.canvas.itemconfig(self.parent.time_text, text=time_text)  # Update the canvas text
        for display in self.external_timer_displays:
            if display and display.winfo_exists():
                display.itemconfig("time", text=f"{minutes:02}:{seconds:02}")

    # Update time progress bar
    def update_bar(self):
        total = self.get_total_time()
        ratio = self.remaining_time / total if total > 0 else 0
        current_width = int(self.parent.canvas.winfo_width())
        new_width = int(current_width * ratio)

        self.parent.canvas.coords(self.parent.bar, 0, 0, new_width, int(self.parent.canvas.winfo_height()))
        self.parent.canvas.update_idletasks()  # ← Force redraw

    # Determine total time based on phase
    def get_total_time(self):
        if self.transit:
            total = self.transit_time
        elif not self.preview_completed:
            total = self.preview_time  # Use 8-minute preview total
        else:
            total = self.initial_time  # Use 4-minute total after preview

        return total
    
    #set manual time for crb
    def set_manual_timer(self, total_seconds):
        self.remaining_time = total_seconds
        self.manual_adjustment = True
        self.update_timer()
        self.update_bar()

    def initialize_bar(self):
        """Set the bar to 100% at the start, before countdown."""

        # Ensure the canvas layout is fully initialized and the width is available
        self.parent.master.after(100, lambda: self._initialize_and_update_bar())

    def _initialize_and_update_bar(self):
        """Update the bar's position based on the current width of the canvas."""

        # Wait for the canvas to be fully initialized and then get its width
        current_width = int(self.parent.canvas.winfo_width())

        if current_width > 0:
            total = self.get_total_time()

            # Set the progress bar to the full width (100%)
            self.parent.canvas.coords(self.parent.bar, 0, 0, current_width, int(self.parent.canvas.winfo_height()))

            # Update timer text position in canvas on TIMER WINDOW
            self.parent.update_text_position(self.parent.canvas, self.parent.time_text)

            # Force the canvas to redraw immediately
            self.parent.canvas.update_idletasks()
        else:
            # If the width is still 0 (likely because the canvas hasn't been laid out), retry after a short delay
            self.parent.timer_window.after(100, self._initialize_and_update_bar)

    def flash_bar_background_color(self, beep_duration):
        """
        This method flashes the bar color based on the beep duration.
        The number of flashes is calculated by dividing the remaining time by the flash duration (0.1 seconds).
        The interval between flashes is fixed as 0.1 seconds.
        """
        flash_duration = 0.2  # Duration of each flash (in seconds)
        flashes = int(self.remaining_time / flash_duration)
        interval = flash_duration * 1000

        def toggle_color(count):

            if count == 0:
                return  # Stop flashing

            # Alternate the color of the bar
            current_color = self.parent.canvas.itemcget(self.parent.bar_background, 'fill')
            new_color = self.parent.red_color if current_color != self.parent.red_color else 'lightgray'

            # Change the bar's background color
            self.parent.canvas.itemconfig(self.parent.bar_background, fill=new_color)

            # Reschedule the next flash after the calculated interval
            self.parent.timer_window.after(int(interval), toggle_color, count - 1)  # Recursively decrease count

        # Run the flashing in a separate thread to avoid blocking the UI
        threading.Thread(target=toggle_color, args=(flashes,), daemon=True).start()

        # After flashing is done, reset the color to red (keep the color red until the next flash)
        self.parent.timer_window.after(int(flashes * interval), lambda: self.parent.canvas.itemconfig(self.parent.bar_background, fill=self.parent.red_color))




