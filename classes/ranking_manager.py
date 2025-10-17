import tkinter as tk
from tkinter import messagebox, filedialog
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app.config import Config
from app.classes.ranking_controller import RankingController
from helpers.decorators import validate_competitor_and_route, log_method_call
from tkinter import simpledialog
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("FreeSans", "resources/fonts/FreeSans.ttf"))
import openpyxl

class RankingManager:
    def __init__(self, app):
        self.app = app
        self.rankings_frame = None
        self.rankings_widgets = {}
        self.rankings_window = None
        self.rankings_inner_frame = None
        # Definește fonturi consistente
        self.fonts = {
            "header": Config.FONTS["ranking_header"],
            "cell": Config.FONTS["ranking_cell"],
            "button": Config.FONTS["ranking_button"]
        }

    def _calculate_totals(self, competitors):
        """Returnează dict {competitor: total_puncte}."""
        return {
            comp: sum(
                self.app.route_scores[comp].get(r, 0)
                if isinstance(self.app.route_scores[comp].get(r, 0), (int, float))
                else 0
                for r in self.app.dynamic_routes
            )
            for comp in competitors
        }

    def _rank_with_ties(self, competitors, totals):
        """
        Returnează (sorted_list, rank_map) unde
        rank_map[competitor] = loc (cu egalități: 1,1,3…)
        """
        # sortează descendent după puncte
        sorted_comps = sorted(competitors, key=lambda c: totals[c], reverse=True)
        rank_map = {}
        prev_score = None
        current_rank = 0
        for position, comp in enumerate(sorted_comps, start=1):
            if totals[comp] != prev_score:  # scor nou → loc nou
                current_rank = position
                prev_score = totals[comp]
            rank_map[comp] = current_rank
        return sorted_comps, rank_map

    def show_rankings(self):
        """
        Afișează sau ascunde clasamentul integrat în panoul de control.
        """
        if self.rankings_frame and self.rankings_frame.winfo_exists():
            if not hasattr(self, 'category_dropdown_shown') or not self.category_dropdown_shown:
                self.category_dropdown_shown = True
                label = tk.Label(self.app.competitors_frame, text="Select competitors/category", font=self.app.input_font, bg="lightgray")
                label.grid(row=9, column=0, padx=10, pady=5, sticky="w")
                self.rankings_dropdown_label = label

                self.category_var_ranking = tk.StringVar(value="Load competitors/category")
                dropdown = tk.OptionMenu(
                    self.app.competitors_frame,
                    self.category_var_ranking,
                    *["Seniori", "Senioare", "U21B", "U21F", "U19B", "U19F", "U15B", "U15F", "U13B", "U13F", "U11B", "U11F"],
                command=lambda selected: self.load_secondary_rankings(f"db/{selected}.csv")
                )
                dropdown.config(font=self.app.input_font)
                dropdown.grid(row=9, column=1, padx=10, pady=5, sticky="w")
                self.rankings_dropdown_menu = dropdown
            return

        competitors = self.app.cm.get_competitors()
        if not competitors:
            messagebox.showinfo("Rankings", "Nu există concurenți încărcați.")
            return

        self.rankings_frame = tk.Frame(self.app.competitors_frame, bg=Config.COLORS["red"])
        self.rankings_frame.grid(row=8, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.rankings_frame.grid_rowconfigure(0, weight=1)
        self.rankings_frame.grid_columnconfigure(0, weight=1)

        canvas_widget = tk.Canvas(self.rankings_frame, bg="lightgrey")
        canvas_widget.grid(row=0, column=0, columnspan=2, sticky="nsew")
        scrollbar = tk.Scrollbar(self.rankings_frame, orient="vertical", command=canvas_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="nsew")
        canvas_widget.configure(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas_widget, bg="lightgrey")
        canvas_widget.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas_widget.configure(scrollregion=canvas_widget.bbox("all"))
        inner_frame.bind("<Configure>", on_frame_configure)

        header_font = self.app.input_font
        tk.Label(inner_frame, text="Rank", bg="lightgray", font=header_font).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(inner_frame, text="Competitor", bg="lightgray", font=header_font).grid(row=0, column=1, padx=5, pady=5)
        num_routes = len(self.app.dynamic_routes) if hasattr(self.app, 'dynamic_routes') else 0
        for j in range(num_routes):
            tk.Label(inner_frame, text=self.app.dynamic_routes[j], bg="lightgray", font=header_font).grid(row=0, column=2+j, padx=5, pady=5)
        tk.Label(inner_frame, text="Total Points", bg="lightgray", font=header_font).grid(row=0, column=2+num_routes, padx=5, pady=5)

        if not hasattr(self.app, 'route_scores'):
            self.app.route_scores = {}
        for competitor in competitors:
            if competitor not in self.app.route_scores:
                self.app.route_scores[competitor] = {}

        self.rankings_widgets = {}
        # 1) calculează punctajele totale
        totals = self._calculate_totals(competitors)
        # 3) afişează rând cu rând
        for row, competitor in enumerate(competitors, start=1):
            # coloana Rank
            tk.Label(inner_frame, text=str(row), bg="lightgray") \
            .grid(row=row, column=0, padx=5, pady=5)
            # coloana Competitor
            tk.Label(inner_frame, text=competitor, bg="lightgray") \
            .grid(row=row, column=1, padx=5, pady=5)
            # butoane pe trasee
            for col, route in enumerate(self.app.dynamic_routes):
                current = self.app.route_scores[competitor].get(route, route)
                btn = tk.Button(inner_frame, text=str(current))
                btn.config(command=(lambda comp=competitor, r=route, b=btn:
                                    self.open_route_popup(comp, r, b, score_dict=self.app.route_scores)))
                btn.grid(row=row, column=2+col, padx=5, pady=5)
                self.rankings_widgets.setdefault(competitor, {})[route] = btn
            # Coloana Total Points:
            total_lbl = tk.Label(inner_frame, text=str(totals[competitor]), bg="lightgray")
            total_lbl.grid(row=row, column=2+len(self.app.dynamic_routes), padx=5, pady=5)
            # Stochezi referința
            self.rankings_widgets.setdefault(competitor, {})['total'] = total_lbl

        open_window_button = tk.Button(self.rankings_frame, text="Deschide Clasament", command=self.show_rankings_window, font=self.fonts["button"])
        open_window_button.grid(row=len(competitors)+2, column=0, padx=10, pady=5, sticky="w")
        
        export_button = tk.Button(self.rankings_frame, text="Export PDF", command=self.export_rankings_to_pdf, font=self.fonts["button"])
        export_button.grid(row=len(competitors)+2, column=1, padx=10, pady=5, sticky="e")
        export_excel_button = tk.Button(
            self.rankings_frame,
            text="Export Excel",
            command=self.export_rankings_to_excel,
            font=self.fonts["button"]
        )
        export_excel_button.grid(row=len(competitors)+2, column=2, padx=10, pady=5, sticky="e")

    def load_secondary_rankings(self, filepath):
    # Clear previous widgets from row 9
        if hasattr(self, 'rankings_dropdown_label'):
            self.rankings_dropdown_label.grid_forget()
        if hasattr(self, 'rankings_dropdown_menu'):
            self.rankings_dropdown_menu.grid_forget()

        from helpers.utils import load_competitors_from_csv

        competitor_data = load_competitors_from_csv(filepath)
        self.secondary_competitor_data = competitor_data
        competitors = [c["name"] for c in competitor_data]
        if not competitors:
            messagebox.showinfo("Rankings", "Nu există concurenți în fișierul selectat.")
            return

        self.secondary_route_scores = {}
        for comp in competitors:
            self.secondary_route_scores[comp] = {}
        
        sorted_competitors = sorted(
            competitors,
            key=lambda c: sum(self.secondary_route_scores.get(c, {}).get(r, 0) for r in self.app.dynamic_routes),
            reverse=True
        )

        self.secondary_rankings_frame = tk.Frame(self.app.competitors_frame, bg=Config.COLORS["red"])
        self.secondary_rankings_frame.grid(row=9, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.secondary_rankings_frame.grid_columnconfigure(0, weight=1)
        self.secondary_rankings_frame.grid_columnconfigure(1, weight=1)

        canvas_widget = tk.Canvas(self.secondary_rankings_frame, bg="lightgrey")
        canvas_widget.grid(row=0, column=0, columnspan=2, sticky="nsew")
        scrollbar = tk.Scrollbar(self.secondary_rankings_frame, orient="vertical", command=canvas_widget.yview)
        scrollbar.grid(row=0, column=2, sticky="ns")
        canvas_widget.configure(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas_widget, bg="lightgrey")
        canvas_widget.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas_widget.configure(scrollregion=canvas_widget.bbox("all"))
        inner_frame.bind("<Configure>", on_frame_configure)

        header_font = self.app.input_font
        tk.Label(inner_frame, text="Rank", bg="lightgray", font=header_font).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(inner_frame, text="Competitor", bg="lightgray", font=header_font).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(inner_frame, text="Club", bg="lightgray", font=header_font).grid(row=0, column=2, padx=5, pady=5)
        num_routes = len(self.app.dynamic_routes) if hasattr(self.app, 'dynamic_routes') else 0
        for j in range(num_routes):
            tk.Label(inner_frame, text=self.app.dynamic_routes[j], bg="lightgray", font=header_font).grid(row=0, column=2+j, padx=5, pady=5)
        tk.Label(inner_frame, text="Total Points", bg="lightgray", font=header_font).grid(row=0, column=2+num_routes, padx=5, pady=5)

        totals = self._calculate_totals(competitors)
        sorted_comps, rank_map = self._rank_with_ties(competitors, totals)

        for competitor in sorted_comps:
            rank = rank_map[competitor]
            total = totals[competitor]
            # folosește rank și total când scrii în PDF/Excel
        
        export_pdf_btn = tk.Button(inner_frame, text="Export PDF", command=lambda: self.export_rankings_to_pdf(self.secondary_competitor_data), font=self.fonts["button"])
        export_pdf_btn.grid(row=len(sorted_competitors)+2, column=0, padx=10, pady=10, sticky="w")

        export_excel_btn = tk.Button(inner_frame, text="Export Excel", command=self.export_rankings_to_excel, font=self.fonts["button"])
        export_excel_btn.grid(row=len(sorted_competitors)+2, column=1, padx=10, pady=10, sticky="e")
        open_window_button = tk.Button(inner_frame, text="Deschide Clasament", command=self.show_rankings_window, font=self.fonts["button"])
        open_window_button = tk.Button(inner_frame, text="Deschide Clasament", command=self.show_secondary_rankings_window, font=self.fonts["button"])
        open_window_button.grid(row=len(competitors)+3, column=0, padx=10, pady=5, sticky="w")

    def show_rankings_window(self):
        if self.rankings_window and self.rankings_window.winfo_exists():
            self.rankings_window.lift()
            return

        self.rankings_window = tk.Toplevel(self.app.master)
        self.rankings_window.title("Clasament Live")
        # Obține dimensiunea ecranului curent (inclusiv TV dacă e mutată acolo)
        screen_width = self.rankings_window.winfo_screenwidth()
        screen_height = self.rankings_window.winfo_screenheight()
        self.rankings_window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        self.rankings_window.configure(bg="black")

        # Setare eveniment închidere fereastră
        self.rankings_window.protocol("WM_DELETE_WINDOW", self.close_rankings_window)

        # Crearea unui frame pentru a conține canvas și scrollbar
        self.rankings_frame = tk.Frame(self.rankings_window, bg="black")
        self.rankings_frame.pack(fill=tk.BOTH, expand=True)

        # Crearea canvas-ului pentru conținutul scrollabil
        canvas = tk.Canvas(self.rankings_frame, bg="black")
        self._auto_scroll_dir = 1  # 1 = în jos, -1 = în sus
        self._auto_scroll_canvas = canvas
       
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Crearea scrollbar-ului și plasarea lui în același frame
        scrollbar = tk.Scrollbar(self.rankings_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Crearea containerului interior
        self.rankings_inner_frame = tk.Frame(canvas, bg="black")
        canvas.create_window((0, 0), window=self.rankings_inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.rankings_inner_frame.bind("<Configure>", on_frame_configure)

        # Apelare metodă de update
        self.update_rankings_display()
        self.rankings_window.after(100, self._fractional_auto_scroll)

        # Setare actualizare automată a display-ului la fiecare 5 secunde
        self.rankings_window.after(5000, self.update_rankings_display)

    def _fractional_auto_scroll(self, delay=30, delta=0.001, top_delay=7000):
        cvs = self._auto_scroll_canvas
        top, bot = cvs.yview()
        # 1) Dacă suntem în sus și veneam din jos, schimbă direcția și așteaptă top_delay
        if top <= 0.0 and self._auto_scroll_dir < 0:
            self._auto_scroll_dir = 1
            self.rankings_window.after(top_delay, self._fractional_auto_scroll, delay, delta, top_delay)
            return

        # 2) Dacă suntem jos și venim din sus, inversează direcția
        if bot >= 1.0 and self._auto_scroll_dir > 0:
            self._auto_scroll_dir = -1

        # 3) Derulează puțin (delta) în direcția curentă
        new_top = min(max(top + self._auto_scroll_dir * delta, 0.0), 1.0)
        cvs.yview_moveto(new_top)

        # 4) Programează următorul pas rapid
        self.rankings_window.after(delay, self._fractional_auto_scroll, delay, delta, top_delay)

    def show_secondary_rankings_window(self):
        if hasattr(self, 'secondary_rankings_window') and self.secondary_rankings_window and self.secondary_rankings_window.winfo_exists():
            self.secondary_rankings_window.lift()
            return

        self.secondary_rankings_window = tk.Toplevel(self.app.master)
        self.secondary_rankings_window.title("Clasament secundar")
        screen_width = self.secondary_rankings_window.winfo_screenwidth()
        screen_height = self.secondary_rankings_window.winfo_screenheight()
        self.secondary_rankings_window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.secondary_rankings_window.configure(bg="black")

        frame = tk.Frame(self.secondary_rankings_window, bg="black")
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame, bg="black")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas, bg="black")
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        header_font = self.fonts["header"]
        text_font = self.fonts["cell"]

        tk.Label(inner_frame, text="Rank", font=header_font, bg="black", fg="white").grid(row=0, column=0)
        tk.Label(inner_frame, text="Competitor", font=header_font, bg="black", fg="white").grid(row=0, column=1)
        tk.Label(inner_frame, text="Club", font=header_font, bg="black", fg="white").grid(row=0, column=2)

        for j, route in enumerate(self.app.dynamic_routes):
            tk.Label(inner_frame, text=route, font=header_font, bg="black", fg="white").grid(row=0, column=3+j)
        tk.Label(inner_frame, text="Total", font=header_font, bg="black", fg="white").grid(row=0, column=3+len(self.app.dynamic_routes))

        if not hasattr(self, 'secondary_competitor_data'):
            return

        competitors = [c["name"] for c in self.secondary_competitor_data]
        sorted_competitors = sorted(
            competitors,
            key=lambda c: sum(self.app.route_scores.get(c, {}).get(r, 0) for r in self.app.dynamic_routes),
            reverse=True
        )
        
        print("Secondary data:", self.secondary_competitor_data)
        for i, comp in enumerate(sorted_competitors, start=1):
            club = next((c["club"] for c in self.secondary_competitor_data if c["name"] == comp), "")
            tk.Label(inner_frame, text=str(i), font=text_font, bg="black", fg="white").grid(row=i, column=0)
            tk.Label(inner_frame, text=comp, font=text_font, bg="black", fg="white").grid(row=i, column=1)
            tk.Label(inner_frame, text=club, font=text_font, bg="black", fg="white").grid(row=i, column=2)

            for j, route in enumerate(self.app.dynamic_routes):
                score = self.app.route_scores.get(comp, {}).get(route)
                canvas_box = tk.Canvas(inner_frame, width=50, height=40, highlightthickness=1, highlightbackground="gray")
                canvas_box.grid(row=i, column=3+j, padx=5, pady=5)

                if score is None:
                    continue
                elif score == 0:
                    canvas_box.create_rectangle(0, 0, 50, 40, fill="white")
                    canvas_box.create_text(25, 20, text="0.0", font=text_font)
                elif score >= 24:
                    canvas_box.create_rectangle(0, 0, 50, 40, fill=self.app.blue_light_color)
                    canvas_box.create_text(25, 20, text=f"{score:.1f}", font=text_font)
                else:
                    canvas_box.create_rectangle(0, 0, 25, 40, fill=self.app.blue_light_color)
                    canvas_box.create_text(25, 20, text=f"{score:.1f}", font=text_font)

            total = sum(self.app.route_scores.get(comp, {}).get(r, 0) for r in self.app.dynamic_routes)
            tk.Label(inner_frame, text=f"{total:.1f}", font=text_font, bg="black", fg="white").grid(row=i, column=3+len(self.app.dynamic_routes))
            


    def close_rankings_window(self):
        if self.rankings_window:
            self.rankings_window.destroy()
            self.rankings_window = None

    def update_rankings_display(self):
        for widget in self.rankings_inner_frame.winfo_children():
            widget.destroy()

        competitors = list(self.app.route_scores.keys())
        # Calculează totaluri și ranguri cu egalități pentru live ranking
        totals = self._calculate_totals(competitors)
        sorted_comps, rank_map = self._rank_with_ties(competitors, totals)

        header_font = self.fonts["header"]
        text_font = self.fonts["cell"]

        tk.Label(self.rankings_inner_frame, text="Rank", font=header_font, bg="black", fg="white").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(self.rankings_inner_frame, text="Competitor", font=header_font, bg="black", fg="white").grid(row=0, column=1, padx=10, pady=5)
        tk.Label(self.rankings_inner_frame, text="Club", font=header_font, bg="black", fg="white").grid(row=0, column=2, padx=10, pady=5)
        for j, route in enumerate(self.app.dynamic_routes):
            route_label = tk.Label(self.rankings_inner_frame, text=route, bg="black", fg="white")
            route_label.grid(row=0, column=3+j, sticky="nsew", padx=0, pady=0)
            self.rankings_inner_frame.grid_columnconfigure(3+j, weight=1)

            def adjust_font(event, label=route_label):
                height = event.height
                width = event.width
                font_size = min(int(height * 0.5), int(width / max(len(route), 1)))
                label.config(font=("Helvetica", font_size, "bold"))

            route_label.bind("<Configure>", adjust_font)
        tk.Label(self.rankings_inner_frame, text="Total Points", font=header_font, bg="black", fg="white").grid(row=0, column=3+len(self.app.dynamic_routes), padx=10, pady=5)

        for row, competitor in enumerate(sorted_comps, start=1):
            tk.Label(self.rankings_inner_frame, text=str(rank_map[competitor]), font=text_font, bg="black", fg="white").grid(row=row, column=0, padx=10, pady=5)
            tk.Label(self.rankings_inner_frame, text=competitor, font=text_font, bg="black", fg="white").grid(row=row, column=1, padx=10, pady=5)
            club = ""
            for comp in self.app.cm.competitor_data:
                if comp["name"] == competitor:
                    club = comp.get("club", "")
                    break
            tk.Label(self.rankings_inner_frame, text=club, font=text_font, bg="black", fg="white").grid(row=row, column=2, padx=10, pady=5)
            for j, route in enumerate(self.app.dynamic_routes):
                score = self.app.route_scores[competitor].get(route, None)
                canvas = tk.Canvas(self.rankings_inner_frame, width=50, height=40, highlightthickness=1, highlightbackground="gray")
                canvas.grid(row=row, column=3+j, padx=10, pady=5)
                
                if score is None:
                    continue  # Casetă complet goală
                elif score == 0:
                    # Fundal alb, text 0
                    canvas.create_rectangle(0, 0, 50, 40, fill="white", outline="")
                    canvas.create_text(25, 20, text="0.0", fill="black", font=text_font)
                elif score >= 24:
                    # Fundal complet albastru
                    canvas.create_rectangle(0, 0, 50, 40, fill=self.app.blue_light_color, outline="")
                    canvas.create_text(25, 20, text=f"{score:.1f}", fill="black", font=text_font)
                else:
                    # Fundal pe jumătate albastru
                    canvas.create_rectangle(0, 0, 25, 40, fill=self.app.blue_light_color, outline="")
                    canvas.create_text(25, 20, text=f"{score:.1f}", fill="black", font=text_font)
            total = sum(self.app.route_scores[competitor].get(r, 0) for r in self.app.dynamic_routes)
            tk.Label(self.rankings_inner_frame, text=f"{total:.1f}", font=text_font, bg="black", fg="white").grid(row=row, column=3+len(self.app.dynamic_routes), padx=10, pady=5)

        if self.rankings_window and self.rankings_window.winfo_exists():
            self.rankings_window.after(5000, self.update_rankings_display)

    def update_ranking_order(self):
        num_routes = len(self.app.dynamic_routes) if hasattr(self.app, 'dynamic_routes') else 0
        if self.rankings_window and self.rankings_window.winfo_exists():
            sorted_competitors = sorted(
                self.rankings_widgets.keys(),
                key=lambda comp: sum(self.app.route_scores[comp].get(r, 0) if isinstance(self.app.route_scores[comp].get(r, 0), (int, float)) else 0 for r in self.app.dynamic_routes),
                reverse=True
            )
        else:
            sorted_competitors = list(self.rankings_widgets.keys())
        for new_index, competitor in enumerate(sorted_competitors, start=1):
            if "rank" in self.rankings_widgets[competitor]:
                self.rankings_widgets[competitor]["rank"].config(text=str(new_index))
                self.rankings_widgets[competitor]["rank"].grid_configure(row=new_index)
            if "name" in self.rankings_widgets[competitor]:
                self.rankings_widgets[competitor]["name"].grid_configure(row=new_index)
            for route in self.app.dynamic_routes:
                if route in self.rankings_widgets[competitor]:
                    self.rankings_widgets[competitor][route].grid_configure(row=new_index)
            if "total" in self.rankings_widgets[competitor]:
                self.rankings_widgets[competitor]["total"].grid_configure(row=new_index)

    def update_total_points_for_competitor(self, competitor):
        total = sum(self.app.route_scores[competitor].get(r, 0) if isinstance(self.app.route_scores[competitor].get(r, 0), (int, float)) else 0 for r in self.app.dynamic_routes)
        if competitor in self.rankings_widgets and "total" in self.rankings_widgets[competitor]:
            self.rankings_widgets[competitor]["total"].config(text=f"{total:.1f}")

    @validate_competitor_and_route
    @log_method_call
    def open_route_popup(self, competitor, route, route_button, score_dict=None):
        score_dict = score_dict or self.app.route_scores
        popup = tk.Toplevel(self.app.master)
        popup.title(f"Scor pentru {route} - {competitor}")
       

        # Obține coordonatele cursorului și setează poziția popup-ului
        x = self.app.master.winfo_pointerx()
        y = self.app.master.winfo_pointery()
        popup.geometry(f"+{x}+{y}")
        
        
        label_zone = tk.Label(popup, text="Zone:")
        label_zone.grid(row=0, column=0, padx=10, pady=10)
        entry_zone = tk.Entry(popup)
        entry_zone.grid(row=0, column=1, padx=10, pady=10)
        
        label_top = tk.Label(popup, text="Top:")
        label_top.grid(row=1, column=0, padx=10, pady=10)
        entry_top = tk.Entry(popup)
        entry_top.grid(row=1, column=1, padx=10, pady=10)
        
        def confirm():
            top_val = entry_top.get().strip()
            zone_val = entry_zone.get().strip()
            score = 0
            use_top = False
            try:
                if top_val != "":
                    top_num = float(top_val)
                    if top_num == 0:
                        score = 0
                    else:
                        score = 25 - ((top_num - 1) / 10)
                        use_top = True
                elif zone_val != "":
                    zone_num = float(zone_val)
                    if zone_num == 0:
                        score = 0
                    else:
                        score = 10 - ((zone_num - 1) / 10)
                else:
                    score = 0
            except ValueError:
                messagebox.showerror("Eroare", "Introduceți o valoare numerică validă.")
                return
            
            score_dict[competitor][route] = score
            route_button.config(text=f"{score:.1f}")
            # 1) recalculezi totalul pentru acest competitor
            new_total = sum(
                self.app.route_scores[competitor].get(r, 0)
                if isinstance(self.app.route_scores[competitor].get(r, 0), (int, float))
                else 0
                for r in self.app.dynamic_routes
            )
            # 2) actualizezi eticheta deja existentă
            widgets = self.rankings_widgets.get(competitor, {})
            total_lbl = widgets.get('total')
            if total_lbl:
                total_lbl.config(text=str(new_total))
            
            if use_top:
                route_button.config(bg=self.app.blue_light_color)
            else:
                route_button.config(bg="#136173")
            popup.destroy()
            self.update_total_points_for_competitor(competitor)
        
        btn_ok = tk.Button(popup, text="OK", command=confirm)
        btn_ok.grid(row=2, column=0, columnspan=2, pady=10)
        
        entry_zone.bind("<Return>", lambda event: confirm())
        entry_top.bind("<Return>", lambda event: confirm())
        

    

    def export_rankings_to_pdf(self, competitor_data=None):
        """Export live rankings în PDF cu acelaşi stil FRAE: culori, font FreeSans şi logo."""
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        import os

        # 1) Titlu
        title = simpledialog.askstring("Titlu Clasament", "Introdu titlul pentru PDF:")
        if not title:
            return

        # 2) Unde salvez
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                filetypes=[("PDF Files", "*.pdf")])
        if not filepath:
            return

        # 3) Datele: principal sau secundar
        if competitor_data is None:
            competitor_data = self.app.cm.competitor_data
        competitors = [c["name"] for c in competitor_data]
        routes = self.app.dynamic_routes

        # 4) Calculează totaluri și ranguri cu egalități
        totals = self._calculate_totals(competitors)
        sorted_comps, rank_map = self._rank_with_ties(competitors, totals)

        # 5) Construieşte matricea pentru tabel
        data = [["Loc", "Concurent", "Club"] + [str(r) for r in routes] + ["Total"]]
        for comp in sorted_comps:
            club = next((c.get("club", "") for c in competitor_data if c["name"] == comp), "")
            scores = [self.app.route_scores.get(comp, {}).get(r, 0) for r in routes]
            total = totals[comp]
            row = [str(rank_map[comp]), comp, club] + [f"{s:.1f}" for s in scores] + [f"{total:.1f}"]
            data.append(row)

        # 6) Iniţializează PDF-ul
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=2*cm,
            bottomMargin=1*cm
        )
        elements = []

        # 7) Stiluri FreeSans
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='DejaVuTitle', fontName='FreeSans', fontSize=24, leading=28))
        styles.add(ParagraphStyle(name='DejaVuNormal', fontName='FreeSans', fontSize=10))

        # 8) Logo FRAE
        logo_path = os.path.join(os.getcwd(), "resources/images/frae-logo.png")
        if os.path.exists(logo_path):
            img = RLImage(logo_path, width=3.5*cm, height=3.5*cm)
            elements.append(img)

        # 9) Titlu şi spaţiu
        elements.append(Paragraph(title, styles["DejaVuTitle"]))
        elements.append(Spacer(1, 12))

        # 10) Creează tabelul cu stilurile din varianta veche
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'FreeSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        elements.append(table)

        # 11) Generează PDF-ul
        doc.build(elements)

        

    def export_rankings_to_excel(self):
        """Export live rankings la Excel cu acelaşi loc pentru punctaje egale."""
        filepath = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                filetypes=[('Excel files','*.xlsx')])
        if not filepath:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        # antet
        headers = ['Loc', 'Concurent'] + [str(r) for r in self.app.dynamic_routes] + ['Total']
        ws.append(headers)

        competitors = self.app.cm.get_competitors()
        totals = self._calculate_totals(competitors)
        sorted_comps, rank_map = self._rank_with_ties(competitors, totals)

        for comp in sorted_comps:
            row = [rank_map[comp], comp] \
                + [self.app.route_scores.get(comp, {}).get(route, 0)
                    for route in self.app.dynamic_routes] \
                + [totals[comp]]
            ws.append(row)
        wb.save(filepath)