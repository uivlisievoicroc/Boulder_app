# ui.py

import tkinter as tk
from tkinter import ttk
import logging
from tkinter import PhotoImage
import os
from PIL import Image, ImageTk

# Configurare logging: nivelul poate fi schimbat (ex. DEBUG, INFO, WARNING, etc.)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Ui:

    def __init__(self, parent):
        self.parent = parent
        self.master = self.parent.master

    def create_frame(self, frame_name, window=None, row=0, column=0, padx=5, pady=5, sticky="nsew", **kwargs):
        """
        Creates a frame in the specified window (or self.master if not provided) and stores it in the app_frames dictionary.
        This version uses grid layout instead of pack.

        Args:
        - frame_name (str): The name of the frame to store in the app_frames dictionary.
        - window (tk.Widget, optional): The parent window (could be self.master or a Toplevel window). Defaults to self.master if not provided.
        - row (int): The row position in the grid (default: 0).
        - column (int): The column position in the grid (default: 0).
        - padx (int): Horizontal padding for the frame (default: 5).
        - pady (int): Vertical padding for the frame (default: 5).
        - sticky (str): The sticky parameter for the grid (default: "nsew").
        - kwargs (dict): Any additional arguments to configure the frame (e.g., `bg`, `padx`).

        Returns:
        - frame (tk.Frame): The created frame.
        """
        # Use self.master if no window is provided
        if window is None:
            window = self.parent

        # Create the frame in the specified window, passing additional keyword arguments
        frame = tk.Frame(window, **kwargs)

        # Use grid layout to place the frame
        frame.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)

        # Adjust row and column weights for resizing
        window.grid_rowconfigure(row, weight=1)
        window.grid_columnconfigure(column, weight=1)

        # Store the frame in the app_frames dictionary
        self.parent.app_frames[frame_name] = frame

        return frame

    # Hide a frame
    def hide_frame(self, frame_name):
        """Hides the specified frame."""
        if frame_name in self.parent.app_frames:
            self.parent.app_frames[frame_name].grid_forget()
        else:
            logging.warning(f"Frame {frame_name} not found in app_frames dictionary.")

    # Show a frame
    def show_frame(self, frame_name, row=0, column=0, padx=5, pady=5, sticky="nsew"):
        """Shows the specified frame."""
        if frame_name in self.parent.app_frames:
            self.parent.app_frames[frame_name].grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)
        else:
            logging.warning(f"Frame {frame_name} not found in app_frames dictionary.")


    def render_text(self, message, frame, row=2, column=0, columnspan=2, sticky="nsew", **kwargs):
        """
        Renders a text message within the specified frame, with customizable options for color, layout, and behavior.

        Args:
        - message (str): The message text to display.
        - frame (tk.Widget): The parent frame to render the message within.
        - row (int): The row where the message label will be placed.
        - column (int): The column where the message label will be placed.
        - columnspan (int): The number of columns the label should span.
        - font (tuple): The font settings (e.g., ("Arial", 12, "bold")).
        - color (str): Foreground color (text color), replaced `fg`.
        - bg (str): Background color.
        - sticky (str): Sticky alignment for the grid (e.g., "nsew" for centering).
        - wraplength (int, optional): The maximum width of the text before it wraps. If not provided, the text will not wrap.

        Returns:
        - message_label (tk.Label): The label widget displaying the message.
        """

        # Extract color, font, background, and wraplength from kwargs, or use default values if not provided
        color = kwargs.get('color', 'black')  # Default to black if no color is provided
        font = kwargs.get('font', self.parent.small_font)  # Default to Arial font with size 12
        bg = kwargs.get('bg', None)  # Default to white background if no bg is provided
        wraplength = kwargs.get('wraplength', None)  # Default to None if not provided

        # Create the label with the provided message and attributes
        label_kwargs = {
            'text': message,
            'fg': color,  # Text color
            'font': font,  # Font style
            'bg': bg  # Background color
        }

        # Check if the message is a StringVar or a regular string
        if isinstance(message, tk.StringVar):
            label_kwargs['textvariable'] = message  # Use textvariable if it's a StringVar
        else:
            label_kwargs['text'] = message  # Use text if it's a normal string


        # Only include wraplength if it's provided
        if wraplength is not None:
            label_kwargs['wraplength'] = wraplength

        # Create the label widget
        message_label = tk.Label(frame, **label_kwargs)

        # Place the label in the grid with specified options
        message_label.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            padx=5,
            pady=5,
            sticky=sticky  # Use sticky for proper alignment
        )

        return message_label  # Return the label in case it's needed for further manipulation

    def create_window(self, title, is_toplevel=False, width=800, height=600, resizable=(True, True), **kwargs):
        """
        This method can create both the main window (master) and any Toplevel windows.

        :param title: The title for the window
        :param width: The width of the window
        :param height: The height of the window
        :param bg_color: The background color of the window
        :param resizable: Tuple to set window resizing options
        :param is_toplevel: Boolean to decide if the window is a Toplevel or the main window
        :param kwargs: Additional arguments (e.g., position)
        """

        # Get position argument from kwargs (default to None)
        position = kwargs.get("position", None)

        if is_toplevel:
            self.window = tk.Toplevel(self.master)
        else:
            self.window = self.master

        self.window.title(title)
        self.window.geometry(f"{width}x{height}")

        # Get screen size
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Default center position
        pos_x = (screen_width - width) // 2
        pos_y = (screen_height - height) // 2

        # Define positioning logic
        if position == "tl":  # Top-left
            pos_x, pos_y = 0, 0
        elif position == "tr":  # Top-right
            pos_x, pos_y = screen_width - width, 0
        elif position == "bl":  # Bottom-left
            pos_x, pos_y = 0, screen_height - height
        elif position == "br":  # Bottom-right
            pos_x, pos_y = screen_width - width, screen_height - height
        elif position == "c":  # Centered (default)
            pass  # Already set to center

        # Apply final geometry
        self.window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        # Set resizable options
        self.window.resizable(resizable[0], resizable[1])

        # Apply background color if provided
        if "bg" in kwargs:
            self.window.configure(bg=kwargs["bg"])

        return self.window

    def close_window(self, window):
        if window:
            window.destroy()
            window = None

    def block_window(self, window):

        # Prevent closing
        window.protocol("WM_DELETE_WINDOW", self.prevent_close)

        # Append 'fereastra blocata' to the window title
        window.title(f"{window.title()} - fereastra blocata")

    def unblock_window(self, window):
        """Unblocks the window, allowing it to be closed again and restores the original title."""

        # Restore the original title
        original_title = window.title().replace(" - fereastra blocata", "")
        window.title(original_title)

        # Allow the window to be closed normally
        window.protocol("WM_DELETE_WINDOW", window.quit)


    def clear_frame(self, frame):
        if frame is not None:
            for widget in frame.winfo_children():
                widget.destroy()
        else:
            logging.error("Provided frame is None, cannot clear it!")

    # Use a helper function to create labels and details for each section
    def create_section(self, frame, row, column, label_text, details_text, font, section_name="", bg_color="lightblue", sticky="nsew", columnspan=1):

        self.render_text(details_text,frame,row, column,columnspan,sticky=sticky,padx=40,pady=40,font=font,bg=bg_color)

        self.render_text(label_text,frame,row+1,column,columnspan,sticky=sticky,padx=40,pady=40,
            font=(self.parent.font_face, 16, 'bold'),bg=bg_color)

    def configure_grid(self, widget, grid_type, positions=[], weights=[], uniform=False):
        """
        Dynamically configures row or column grid layout of a widget.

        :param widget: The parent widget (e.g., self.master, self.some_frame)
        :param grid_type: 'row' to configure rows, 'col' to configure columns.
        :param positions: List of row/column indices to configure.
        :param weights: Corresponding weight values for each row/column.
        :param uniform: Boolean, if True applies uniform="equal".
        """
        for index, weight in zip(positions, weights):
            if grid_type == 'row':
                widget.grid_rowconfigure(index, weight=weight, uniform="equal" if uniform else None)
            else:
                widget.grid_columnconfigure(index, weight=weight, uniform="equal" if uniform else None)

    def prevent_close(self):
        """Custom handler to prevent the window from closing."""
        pass


    # renders app logo
    def render_logo(self, parent):
        """Render the logo inside the given parent frame."""
        logo_path = os.path.join(os.getcwd(), "resources/images/logo.jpeg")

        try:
            img = Image.open(logo_path)  # Open image using PIL
            img = img.resize((215, 300))  # Resize image if needed
            logo = ImageTk.PhotoImage(img)  # Convert to Tkinter format

            # Create label inside parent frame
            logo_label = tk.Label(parent, image=logo, bg="white")
            logo_label.image = logo  # Keep reference to avoid garbage collection
            logo_label.grid(row=0, column=0, columnspan=3, pady=(10, 20), sticky="n")

        except FileNotFoundError:
            logging.error(f"Image '{logo_path}' not found. Please check the path.")
        except Exception as e:
            logging.error(f"Error loading image: {e}")

    def create_dropdown(self, parent, variable, values, row, column, callback=None, font=None, width=None):
        """
        Creates a reusable dropdown (combobox) in a given parent frame.

        :param parent: The parent widget (frame)
        :param variable: The Tkinter StringVar for tracking the selection
        :param values: List of values to display in the dropdown
        :param row: Row position in the grid
        :param column: Column position in the grid
        :param callback: Function to call when selection changes (optional)
        :param font: Font for the dropdown text (optional)
        :param width: Width of the dropdown (optional)
        :return: The created combobox widget
        """
        dropdown = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state='readonly',
            font=font or self.parent.selector_font,  # Default font if not provided
            width=width
        )

        # Place the dropdown in the grid
        dropdown.grid(row=row, column=column, padx=5, pady=5, sticky='ew')

        # Bind the callback function if provided
        if callback:
            dropdown.bind("<<ComboboxSelected>>", callback)

        return dropdown  # Return the dropdown widget
