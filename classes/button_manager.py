# button_manager.py

import tkinter as tk
import logging
import customtkinter as ctk

# Configurare logging: nivelul poate fi schimbat (ex. DEBUG, INFO, WARNING, etc.)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ButtonManager:

    def __init__(self, parent):
        self.parent = parent
        self.buttons = {}

    

    # Renders a button on the specific frame and stores it in a dictionary
    def render_button(self, frame, text, row, column, command, **kwargs):

        # Check and handle background color and text color logic
        bg = kwargs.get('bg', None)  # Get the background color from kwargs, default to None
        bg_hover = kwargs.get('bg_hover', None)  # Get the background color from kwargs, default to None

        if bg is None or bg == "":
            text_color = 'white'  # Default text color when no background is provided
        else:
            text_color = 'white'

        # Now, ensure the text_color is passed to kwargs so it's used in the button

        # Handle internal padding from kwargs (if provided)
        padx = kwargs.pop('padx', 10)  # Internal horizontal padding
        pady = kwargs.pop('pady', 10)  # Internal vertical padding
        width = kwargs.pop('width', 10)  # Button width
        sticky = kwargs.pop('sticky', None)  # Grid sticky
        font = kwargs.pop('font', self.parent.button_font)  # Default font if not provided

        # Remove bg from kwargs before passing it to tk.Button
        kwargs.pop('bg', None)

        # Create the button using CTkButton from customtkinter
        hover_color = kwargs.get('hover_color', bg if bg else "#2b898e")
        kwargs.setdefault("text_color", text_color)
        button = ctk.CTkButton(
            master=frame,
            text=text,
            command=command,
            font=font,
            fg_color=bg if bg else "#2e6183",
            hover_color=hover_color,
            corner_radius=10,
            **kwargs
        )

        # CTkButton handles padding internally; hover events removed.

        # Filter valid kwargs for grid() (excluding invalid options like `width`, `bg`, etc.)
        valid_kwargs = {key: value for key, value in kwargs.items() if key in ['padx', 'pady', 'row', 'column', 'sticky', 'columnspan', 'rowspan']}

        # Place the button on the grid (grid options remain unchanged)
        button.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky, **valid_kwargs)

        # Store the button reference by text (or any other unique identifier)
        self.buttons[text] = {
            'button': button,
            'row': row,
            'column': column,
            'kwargs': kwargs  # Store all kwargs for later reference
        }

        return button

    # Hides a button by its name
    def hide_button(self, button_name):
        """Hides a specific button by its name."""
        if button_name in self.buttons:
            button = self.buttons[button_name]['button']
            if button.winfo_exists():  # Check if the button still exists in the layout
                button.grid_forget()  # Remove the button from the grid
            else:
                logging.warning(f"Button {button_name} already forgotten or destroyed.")
        else:
            logging.warning(f"Button {button_name} not found in the buttons dictionary.")

    # Shows a button
    def show_button(self, button_name):
        """Shows a specific button by its name."""
        if button_name in self.buttons:
            button = self.buttons[button_name]['button']
            row = self.buttons[button_name]['row']
            column = self.buttons[button_name]['column']
            padx = self.buttons[button_name]['padx']
            pady = self.buttons[button_name]['pady']

            button.grid(row=row, column=column, padx=padx, pady=pady)

    def toggle_button(self, buttonName, enabled=True):

        # Check if the button exists in the self.buttons dictionary
        if buttonName not in self.buttons:
            return  # If button doesn't exist, exit the function

        self.buttons[buttonName]['button'].configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def alter_button(self, buttonName, text=None, command=None, text_color=None):
        """
        Alters the specified button's text and command.

        Args:
            buttonName (str): The name of the button to modify.
            text (str, optional): The new text to set for the button.
            command (function, optional): The new command to set for the button.
        """
        # Check if the button exists in the dictionary
        if buttonName not in self.buttons:
            logging.warning(f"Button '{buttonName}' not found in buttons dictionary.")
            return  # If button doesn't exist, exit the method

        # Alter button text if newText is provided
        if text is not None:
            self.buttons[buttonName]['button'].configure(text=text)

        # Alter button command if newCommand is provided
        if command is not None:
            self.buttons[buttonName]['button'].configure(command=command)
        
        # Colors the transformed buttons
        if text_color is not None:
            self.buttons[buttonName]['button'].configure(text_color=text_color)
        
