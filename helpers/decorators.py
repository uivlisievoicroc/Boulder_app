# helpers/decorators.py

import logging
from functools import wraps
from tkinter import messagebox

def catch_exceptions(func):
    """
    Decorator pentru a captura excepțiile și a le înregistra.
    Evită oprirea neașteptată a aplicației.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Eroare în {func.__name__}: {e}")
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
    return wrapper

def validate_competitor_and_route(func):
    """
    Decorator pentru a verifica dacă competitorul și ruta sunt valide.
    """
    @wraps(func)
    def wrapper(self, competitor, route, *args, **kwargs):
        if competitor not in self.app.route_scores:
            self.app.route_scores[competitor] = {}
        if not hasattr(self.app, 'dynamic_routes') or route not in self.app.dynamic_routes:
            logging.warning(f"Ruta '{route}' nu este validă pentru competitorul {competitor}")
            messagebox.showwarning("Rută invalidă", f"Ruta '{route}' nu este validă.")
            return
        return func(self, competitor, route, *args, **kwargs)
    return wrapper

def log_method_call(func):
    """
    Decorator care loghează apelul unei funcții.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.debug(f"[CALL] {func.__name__} args={args[1:]}, kwargs={kwargs}")
        return func(*args, **kwargs)
    return wrapper