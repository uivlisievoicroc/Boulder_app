# competitor_manager.py

import tkinter as tk
import logging
import math
from helpers.utils import *
import tkinter.simpledialog as simpledialog
from helpers.decorators import log_method_call

# Configurare logging: nivelul poate fi schimbat (ex. DEBUG, INFO, WARNING, etc.)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CompetitorManager:

    def __init__(self, parent, ui, button_manager, authentication):
        self.parent = parent
        self.ui = ui
        self.button_manager = button_manager
        self.authentication = authentication
        self.master = self.parent.master
        self.dragged_item_index = None
        self.dragged_item = None
        self.highlight_label = None
        self.highlighted_index = None
        self.new_competitor_names = []
        self.competitor_count = 0

        self.toggle_button = self.button_manager.toggle_button

    @log_method_call
    def add_competitor(self):
        self.competitors_listbox = self.parent.competitors_listbox
        competitors = self.get_competitors()
 
        # Extract only properly formatted names (C<number>)
        numbered_competitors = [
            int(name[1:]) for name in competitors if name.startswith('C') and name[1:].isdigit()
        ]
 
        # Determine the next available index
        current_index = max(numbered_competitors, default=0) + 1
 
        # Always auto-generate name (no Entry field)
        name = f"C{current_index}"

        # Add competitor to list
        competitors.append(name)
        parsed = []
        for c in competitors:
            parts = c.split("|")
            name = parts[0].strip()
            club = parts[1].strip() if len(parts) > 1 else ""
            parsed.append({"name": name, "club": club})
        self.set_competitors(parsed)

        # Increment competitor count
        self.competitor_count += 1  # Track added competitor

        self.competitors_listbox.insert(tk.END, name)  # Add to the ListBox
        index = self.competitors_listbox.get(0, tk.END).index(name)
        if index % 2 == 0:
            self.competitors_listbox.itemconfig(index, {'bg': '#f0f0f0'})
        else:
            self.competitors_listbox.itemconfig(index, {'bg': '#ffffff'})

        # Save competitors to CSV
        self.write_competitors_to_csv(competitors)

        self.button_manager.toggle_button('Delete list', True)

    """
    Allows inline editing of a selected Listbox item dynamically.
    """
    def enable_inline_edit(self, listbox, font, update_callback=None):
        # Get the index of the selected item in the Listbox
        index = listbox.curselection()

        if not index:
            return  # If no selection, exit

        index = index[0]
        current_name = listbox.get(index)  # Get the current name of the competitor

        # Get the position of the selected item to place the entry box
        x, y, width, height = listbox.bbox(index)

        # Create an Entry widget at the same position
        entry_editor = tk.Entry(listbox, font=font)
        entry_editor.insert(0, current_name)  # Pre-fill with existing name
        entry_editor.place(x=0, y=y, relwidth=1, height=height)

        # Select all text when entering edit mode
        entry_editor.select_range(0, tk.END)

        # Function to save the edited name
        def save_edit(event=None):
            new_name = entry_editor.get().strip()  # Get the new name

            if new_name:
                listbox.delete(index)  # Delete the old name
                listbox.insert(index, new_name)  # Insert the new name

                # Update the backend competitors list
                competitors = self.get_competitors()
                competitors[index] = new_name  # Update in backend list
                self.set_competitors(competitors)  # Update the backend list

                # Call the update callback to sync with backend
                if update_callback:
                    updated_list = list(listbox.get(0, tk.END))  # Get updated list from Listbox
                    logging.debug(f"Updated list: {updated_list}")
                    update_callback(updated_list)  # Call the update callback to save the updated list

                # Update competitor's name in CSV as well
                self.edit_competitor_from_csv(current_name, new_name)

                self.parent.update_display_window_contest()
            entry_editor.destroy()  # Destroy the editor after saving

        # Handle keyboard actions for selection
        def select_all_text(event=None):
            entry_editor.select_range(0, tk.END)

        # Bind actions
        entry_editor.bind("<Return>", save_edit)
        entry_editor.bind("<FocusOut>", save_edit)
        entry_editor.bind("<Control-a>", select_all_text)  # Ctrl+A to select all
        entry_editor.bind("<Shift-Left>", lambda event: entry_editor.select_range(0, entry_editor.index(tk.INSERT)))
        entry_editor.bind("<Shift-Right>", lambda event: entry_editor.select_range(0, entry_editor.index(tk.INSERT)))
        entry_editor.bind("<Shift-Up>", lambda event: entry_editor.select_range(0, entry_editor.index(tk.INSERT)))
        entry_editor.bind("<Shift-Down>", lambda event: entry_editor.select_range(0, entry_editor.index(tk.INSERT)))

        entry_editor.focus_set()  # Focus on input field

    def delete_competitor(self, event):
        # Get the competitors list from the backend
        competitors = self.get_competitors()

        # Get the selected indices from the Listbox
        selected_indices = self.competitors_listbox.curselection()

        if selected_indices:
            # Loop through selected indices and remove corresponding competitors
            for idx in selected_indices:
                competitor_to_delete = self.competitors_listbox.get(idx)

                # Delete from Listbox
                self.competitors_listbox.delete(idx)

                # Remove competitor from the backend list
                if competitor_to_delete in competitors:
                    competitors.remove(competitor_to_delete)
                    self.set_competitors(competitors)  # Update the backend list

                    # Also remove the competitor from the CSV
                    self.write_competitors_to_csv(competitors)  # Call this method after the deletion

                    logging.debug(f"Competitor {competitor_to_delete} has been deleted from the Listbox and backend.")
                else:
                    logging.warning(f"Competitor {competitor_to_delete} not found in backend list.")

        # no competitors left, disable delete button
        if not self.get_competitors():
            self.button_manager.toggle_button('Delete list', False)


    def on_competitor_press(self, event):
        """Start dragging an item."""
        self.competitors_listbox = self.parent.competitors_listbox

        # Ensure dragging only works if more than 1 item is present
        if len(self.competitors_listbox.get(0, tk.END)) < 2:
            return

        # Get the selected item
        self.dragged_item_index = self.competitors_listbox.nearest(event.y)
        if self.dragged_item_index is not None:
            self.dragged_item = self.competitors_listbox.get(self.dragged_item_index)

            # Set the background color of the selected item to blue (for visual feedback)
            self.competitors_listbox.itemconfig(self.dragged_item_index, {
                'bg': self.parent.blue_light_color,
                'fg': self.parent.black_color
            })


    def on_competitor_motion(self, event):
        """Update visual feedback while dragging."""
        if self.dragged_item is None:
            return

        self.competitors_listbox = self.parent.competitors_listbox
        nearest_index = self.competitors_listbox.nearest(event.y)

        # Ensure the movement updates dynamically without jumps
        if nearest_index == self.dragged_item_index:
            return  # Ignore if no change

        # Remove the dragged item from its old position
        items = list(self.competitors_listbox.get(0, tk.END))
        if self.dragged_item in items:
            items.remove(self.dragged_item)

        # Insert the dragged item at the new position
        items.insert(nearest_index, self.dragged_item)

        # Clear and update the listbox
        self.competitors_listbox.delete(0, tk.END)
        for i, item in enumerate(items):
            self.competitors_listbox.insert(tk.END, item)

            # Highlight the currently dragged item
            if i == nearest_index:
                self.competitors_listbox.itemconfig(i, {'bg': self.parent.blue_light_color, 'fg': self.parent.black_color})
            else:
                self.competitors_listbox.itemconfig(i, {'bg': '', 'fg': ''})

        # Update indices for tracking movement direction
        self.highlighted_index = nearest_index

    def on_competitor_release(self, event):
        """Finalize the drag-and-drop action."""
        if self.dragged_item is None or self.highlighted_index is None:
            return

        # Get current items
        competitors = list(self.competitors_listbox.get(0, tk.END))

        # Update backend list of competitors
        self.set_competitors(competitors)

        # Reset state
        self.dragged_item = None
        self.dragged_item_index = None
        self.highlighted_index = None

        # Check if the dragged item index is valid before calling itemconfig
        if self.dragged_item_index is not None and isinstance(self.dragged_item_index, int):
            try:
                self.competitors_listbox.itemconfig(self.dragged_item_index, {'bg': '', 'fg': ''})
            except Exception as e:
                logging.error(f"Error removing highlight: {e}")

    def get_competitors(self):
        return self.new_competitor_names

    def set_competitors(self, competitors):
        parsed_data = []
        for c in competitors:
            if isinstance(c, dict):
                parsed_data.append(c)
            elif isinstance(c, str):
                parts = c.split(",")
                name = parts[0].strip()
                club = parts[1].strip() if len(parts) > 1 else ""
                parsed_data.append({"name": name, "club": club})
            else:
                logging.warning(f"Format necunoscut pentru competitor: {c}")
        self.competitor_data = parsed_data
        self.new_competitor_names = [c["name"] for c in parsed_data]

    def delete_competitors(self, element):

        # Check if the Listbox already has competitors
        current_competitors = list(element.get(0, tk.END))

        # bail early
        if len(current_competitors) == 0:
            return

        if element is not None:
            element.delete(0, tk.END)
        self.set_competitors([])

    # Load competitors from csv
    def load_competitors(self, element, file_name):
        competitors = self.read_competitors_from_csv(file_name)

        if not competitors:
            logging.warning(f"No competitors found in {file_name}.")
            if element is not None:
                element.insert(tk.END, "No competitors available")
            return False

        current_competitors = self.get_competitors()

        if current_competitors:
            new_competitors = [comp for comp in competitors if comp not in current_competitors]

            if not new_competitors:
                logging.info("All competitors are already loaded in the Listbox.")
                return True

            current_competitors.extend(new_competitors)
        else:
            current_competitors = competitors

        self.set_competitors(current_competitors)
        if element is not None:
            element.delete(0, tk.END)
            self.populate_competitors_listbox(element, current_competitors)
        self.button_manager.toggle_button('Delete list', True)

        logging.debug(f"Updated competitors list: {current_competitors}")

        return True


    def populate_competitors_listbox(self, element, competitors):
        """Populate the Listbox with competitor names."""
        for index, competitor in enumerate(competitors):
            if isinstance(competitor, dict):
                name = competitor.get("name", "").strip()
                club = competitor.get("club", "").strip()
            else:
                name, club = competitor.split(",", 1) if "," in competitor else (competitor, "")
                name = name.strip()
                club = club.strip()
            display_text = f"{name} | {club}"
            if element is not None:
                element.insert(tk.END, display_text)
            if index % 2 == 0:
                element.itemconfig(index, {'bg': '#d3d3d3'})  # light gray for even rows
            else:
                element.itemconfig(index, {'bg': '#ffffff'})  # white for odd rows

    def write_competitors_to_csv(self, competitors, file_name="db/competitors-list.csv"):
        """
        Write the list of competitors to a CSV file.
        """
        try:
            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['name'])  # Writing header
                for competitor in competitors:
                    writer.writerow([competitor])
            logging.info(f"Competitors have been written to {file_name}")
        except Exception as e:
            logging.error(f"Error writing to CSV: {e}")

    def read_competitors_from_csv(self, file_name="db/competitors-list.csv"):
        """
        Read competitors from a CSV file and return them as a list.
        """
        competitors = []
        try:
            with open(file_name, mode='r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                for row in reader:
                    if len(row) >= 2:
                        competitors.append({"name": row[0].strip(), "club": row[1].strip()})
                    elif len(row) == 1:
                        competitors.append({"name": row[0].strip(), "club": ""})
        except FileNotFoundError:
            logging.warning(f"{file_name} not found, returning empty list.")
        except Exception as e:
            logging.error(f"Error reading from CSV: {e}")
        return competitors


    def edit_competitor_from_csv(self, old_name, new_name, file_name="db/competitors-list.csv"):
        """
        Edit a competitor's name in the CSV file.
        """
        try:
            competitors = self.read_competitors_from_csv(file_name)

            # Find the competitor to edit
            if old_name in competitors:
                competitors[competitors.index(old_name)] = new_name
                self.write_competitors_to_csv(competitors, file_name)
                print(f"Competitor name changed from {old_name} to {new_name}.")
            else:
                print(f"Competitor {old_name} not found.")
        except Exception as e:
            print(f"Error editing competitor from CSV: {e}")
