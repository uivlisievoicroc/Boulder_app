# athentication.py

import hashlib
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import logging
import math

# Configurare logging: nivelul poate fi schimbat (ex. DEBUG, INFO, WARNING, etc.)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Authentication:

    def __init__(self, parent):
        self.parent = parent
        self.master = self.parent.master
        self.password = 'a8c234f3319333b7bec9d0d239a968b7'
        self.is_user_logged_in = False
        self.callback = False

    def authenticate_user(self, callback=None):
        """Check if the user entered the correct password. If not, show password prompt."""

        self.callback = callback  # Store the callback for later execution
        self.prompt_password()  # Show password prompt

    def check_password(self):
        """Check if the entered password is correct and return True/False."""
        if not hasattr(self, "password_entry"):  # If no password window exists
            return False

        logging.debug("Check password run")
        entered_password = str(self.password_entry.get()).strip()

        logging.debug(f"Entered pass {entered_password}")

        if not entered_password:
            logging.debug("No password entered")
            return False  # Prevent empty submissions

        hashed_entered_password = hashlib.md5(entered_password.encode()).hexdigest()

        if hashed_entered_password == self.password:
            logging.debug("Password correct!")

            self.is_user_logged_in = True  # ✅ Set user as authenticated
            self.destroy_pass_window()  # Close password window

            if callable(self.callback):
                self.callback()

            return True  # Return success
        else:
            logging.debug("Incorrect password!")
            # Temporarily allow messagebox to be on top
            self.password_window.attributes('-topmost', 0)  # Disable topmost for password window
            messagebox.showerror("Eroare", "Parolă greșită! Pare ca nu esti un admin.")
            self.password_window.attributes('-topmost', 1)  # Restore topmost for password window

            self.password_entry.delete(0, tk.END)  # Clear input field
            return False  # Return failure

    def prompt_password(self, callback=None):
        """Prompt the user for the password before allowing actions."""

        # If the password window already exists, no need to create a new one.
        if hasattr(self, 'password_window') and self.password_window is not None:
            logging.debug("Password window is already open. No need to prompt again.")
            return

        # Center the window on master
        master_x, master_y = self.master.winfo_rootx(), self.master.winfo_rooty()
        master_width, master_height = self.master.winfo_width(), self.master.winfo_height()

        window_width, window_height = 300, 150
        x_pos = master_x + (master_width // 2) - (window_width // 2)
        y_pos = master_y + (master_height // 2) - (window_height // 2)

        # Create a new top-level window for password input
        self.password_window = tk.Toplevel(self.master)
        self.password_window.title("Enter Password")
        self.password_window.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

        # Set this window to always stay on top of others
        self.password_window.attributes('-topmost', 1)  # This keeps the window on top

        self.password_label = tk.Label(self.password_window, text="Enter admin password")
        self.password_label.pack(pady=10)

        # Create the password entry field
        self.password_entry = tk.Entry(self.password_window, show="*")
        self.password_entry.pack(pady=10)
        self.password_entry.focus_set()

        # Create the Submit button and bind it to check_password
        self.submit_button = tk.Button(self.password_window, text="Submit", command=self.check_password)
        self.submit_button.pack(pady=10)

        self.password_window.bind("<Return>", lambda event: self.check_password())

        # Ensure that when the window is closed, we reset the reference to None
        self.password_window.protocol("WM_DELETE_WINDOW", self.destroy_pass_window)

    def destroy_pass_window(self):
        """Reset reference when password window is closed."""
        logging.debug("Destroying the window")
        self.password_window.destroy()
        self.password_window = None
