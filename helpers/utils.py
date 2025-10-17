
import tkinter as tk
import logging
import csv


# Configurare logging: nivelul poate fi schimbat (ex. DEBUG, INFO, WARNING, etc.)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def get_selected_value(selector_var, mapping=None):
    """Fetch the actual value (not label) from a combobox.

    - If `mapping` is provided and the selected label exists in it, return the mapped value.
    - If the value is a digit, return it as an integer.
    - Otherwise, return the original string or None.
    """
    selected_label = selector_var.get().strip()  # Get the selected label from combobox

    # If a mapping dictionary is provided and the selected label exists, return the mapped value
    if mapping and isinstance(mapping, dict):
        return mapping.get(selected_label, None)  # Return mapped value or None

    # If it's a digit, return it as an integer
    if selected_label.isdigit():
        return int(selected_label)

    return selected_label if selected_label else None  # Return the original string or None

import csv

def load_competitors_from_csv(filepath):
    competitors = []
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        # Detectează separatorul corect (virgulă, tab sau punct și virgulă)
        sample = csvfile.read(1024)
        csvfile.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        reader = csv.DictReader(csvfile, dialect=dialect)

        for row in reader:
            name = row.get("name") or row.get("Name") or list(row.values())[0]
            club = row.get("club") or row.get("Club") or ""
            competitors.append({"name": name.strip(), "club": club.strip()})

    return competitors