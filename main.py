from lg_classes import Lineup, Player
from predictor import Predictor
from threading import Thread
import customtkinter as ctk
from typing import Any
from PIL import Image
import apa_client
import sys
import ctypes
import json

if sys.platform == "win32":
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

apa = apa_client.APA()

class GenieFrame(ctk.CTkFrame):
    def __init__(self, master: Any, rows: int = 1, columns: int = 1, **kwargs):
        super().__init__(master, **kwargs)

        self.rows = rows
        self.columns = columns

        for r in range(rows):
            self.rowconfigure(r, weight=1)
        for c in range(columns):
            self.columnconfigure(c, weight=1)

class GenieLabel(ctk.CTkLabel):
    def __init__(self, master: Any, text: str, text_color: str, **kwargs):
        super().__init__(master, text=text, text_color=text_color, **kwargs)

        self.text = text
        self.color = text_color

    def config_text(self, text: str, color: str):
        self.text = text
        self.color = color
        self.configure(text=text, text_color=color)

class GenieEntry(ctk.CTkEntry):
    def __init__(self, master: Any, text: str | None = None, **kwargs):
        self.text = ctk.StringVar(value=text)
        super().__init__(master, textvariable=self.text, **kwargs)

class GenieApp(ctk.CTk):
    def __init__(self, rows, columns):
        super().__init__()

        self.genie_img = ctk.CTkImage(
            light_image=Image.open("assets/genie.png"),
            dark_image=Image.open("assets/genie.png"),
            size=(281, 300)
        )

        self.MAX_ROWS = rows
        self.MAX_COLS = columns

        for c in range(self.MAX_COLS):
            self.columnconfigure(c, weight=1)
        for r in range(self.MAX_ROWS):
            self.rowconfigure(r, weight=1)

        self.DEFAULT_PADX = 5
        self.DEFAULT_PADY = 5
        self.DEFAULT_STICKY = "nsew"

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.TAB_COLORS = ctk.CTkButton(self).cget("fg_color")
        self.inactive_color = "#9C9C9C"

        self.title("APA Lineup Genie")
        self.geometry("550x400")
        self.resizable(False, False) 
        self.iconbitmap("assets/genie.ico") 

        self.create_widgets()

        # Extra
        self.keep = set()
        self.status_created = False

    def grid(self, widget: ctk.CTkBaseClass, **kwargs: Any) -> None:
        """Intercepts grid parameters from kwargs to keep them within boundaries."""
        
        row = kwargs.pop('row', 0)
        column = kwargs.pop('column', 0)
        rowspan = kwargs.pop('rowspan', 1)
        columnspan = kwargs.pop('columnspan', 1)

        padx = kwargs.pop('padx', self.DEFAULT_PADX)
        pady = kwargs.pop('pady', self.DEFAULT_PADY)
        sticky = kwargs.pop('sticky', self.DEFAULT_STICKY)

        parent = widget.master

        max_rows = getattr(parent, "rows", self.MAX_ROWS)
        max_columns = getattr(parent, "columns", self.MAX_COLS)

        if (row + rowspan) > max_rows:
            raise ValueError(f"Rows + Span exceeds max_rows ({max_rows})")
        if (column + columnspan) > max_columns:
            raise ValueError(f"Cols + Span exceeds max_columns ({max_columns})")

        if row < 0:
            raise ValueError("Row cannot be a negative number")
        if column < 0:
            raise ValueError("column cannot be a negative number")

        widget.grid(
            row=row,
            column=column,
            rowspan=rowspan,
            columnspan=columnspan,
            padx=padx,
            pady=pady,
            sticky=sticky,
            **kwargs
        )

    def clean(self, frame: ctk.CTkFrame) -> None:
        """Recursively destroys unlisted widgets and hides widgets in 'keep'."""
        
        def _recursive_clean(widget):
            if widget in self.keep:
                widget.pack_forget()
                widget.grid_forget()
                widget.place_forget()
                return
            
            if hasattr(widget, "winfo_children"):
                for child in widget.winfo_children():
                    _recursive_clean(child)
            
            if not hasattr(widget, "winfo_children") or not widget.winfo_children():
                widget.destroy()

        for top_widget in frame.winfo_children():
            _recursive_clean(top_widget)

    def modify_label(self, widget: ctk.CTkLabel, text: str, color: str):
        widget.configure(text=text, color=color)

    # ABOUT
    def about(self):
        image_label = ctk.CTkLabel(
            self.content_frame,
            image=self.genie_img,
            text=""
        )
        self.grid(
            image_label,
            row=0,
            column=0,
            rowspan=10,
            columnspan=self.content_frame.columns//2
        )

        header = ctk.CTkLabel(
            self.content_frame,
            text="Lineup Genie",
            font=("Trebuchet MS", 26, "bold", "italic"),
            justify="left",
            anchor="nw",
            wraplength=230
        )
        self.grid(
            header,
            row=0,
            column=5,
            columnspan=self.content_frame.columns//2,
            pady=0
        )

        about = ctk.CTkLabel(
            self.content_frame,
            text="Lineup Genie is a pool lineup optimizer.\n\nIt uses player skill levels, matchup statistics, and a whole lot of permutations to find lineup options that give you the best chance of winning.\n\nThe captain shouldn't say \"trust me bro\" because it isn't a lineup strategy.",
            font=("Trebuchet MS", 16),
            justify="left",
            anchor="nw",
            wraplength=230
        )
        self.grid(
            about,
            row=1,
            column=5,
            rowspan=9,
            columnspan=self.content_frame.columns//2,
            pady=0
        )

    # SEARCH
    def get_matches(self, player: dict, alias_id: int, player_level: int) -> tuple[str, str]: 
        matches = apa.get_player_matches(
            alias_id=alias_id,
            days=365,
            same_sl_only=True,
            target_sl=player_level
        )

        name = f"{player['firstName']} {player['lastName']}"
        return name, apa.get_skill_level(matches, player_level)

    def sp_button(self, name: str, status_widget: GenieLabel) -> None:
        def worker():
            self.search_player_button.configure(state="disabled")

            status_widget.config_text("Fetching Player!", "yellow")
            players = apa.search_player(name)

            if not players:
                status_widget.config_text("No Player Found!", "red")
                return
            try:
                player = players[0]
                alias_id = player["aliases"][-1]["id"]

                found_name = f"{player['firstName']} {player['lastName']}"

                team_data = apa.get_teams(alias_id)
                current_teams = team_data["alias"].get("currentTeams", [])

                player_level = next(
                    record["skillLevel"]
                    for record in current_teams
                    if record["__typename"] == "EightBallPlayer"
                )

                status_widget.config_text(f"{found_name} Found!", "green")
            except:
                status_widget.config_text("No Player Found!", "red")
                return

            def worker():
                name, skill_level = self.get_matches(
                    player,
                    alias_id,
                    player_level
                )

                self.after(0, lambda: status_widget.config_text(f"{name}, {skill_level}", "green"))
                self.after(0, lambda: self.search_player_button.configure(state="normal"))

            Thread(target=worker, daemon=True).start()
        Thread(target=worker, daemon=True).start()
        
    def search(self):
        def _text_switcher():
            if self.switch.get() == 0:
                self.switch.configure(text="Friendly")
            else:
                self.switch.configure(text="Opponent")
                
        if not self.status_created:
            self.status_container = GenieFrame(self.content_frame, rows=1, columns=4, fg_color="transparent")
            self.status_val = GenieLabel(self.status_container, text="___", text_color="yellow", anchor="w", font=("Trebuchet MS", 15, "bold"))
            self.switch = ctk.CTkSwitch(
                self.content_frame,
                text="Ally",
                command=_text_switcher
            )
            self.search_player = GenieEntry(
                self.content_frame,
                justify="center"
            )

            self.keep.add(self.status_container)
            self.keep.add(self.status_val)
            self.keep.add(self.switch)
            self.keep.add(self.search_player)

            self.status_created = True

        self.grid(self.status_container, row=0, column=0, columnspan=10, sticky="")
        self.grid(self.switch, row=0, column=0, columnspan=2)

        status = ctk.CTkLabel(self.status_container, text="Status: ", anchor="e", font=("Trebuchet MS", 15, "bold"))

        self.grid(status, row=0, column=2)
        self.grid(self.status_val, row=0, column=3)
        self.grid(self.search_player, row=1, column=0, columnspan=5)

        self.search_player_button = ctk.CTkButton(
            self.content_frame,
            text="🔍 Search Player",
            command=lambda: self.sp_button(self.search_player.get(), self.status_val)
        )
        self.grid(self.search_player_button, row=1, column=5, columnspan=5)

        filler = GenieFrame(self.content_frame, 1, 1, fg_color="transparent")
        self.grid(filler, row=3, column=0, rowspan=7, columnspan=10)

    def lineups(self):
        pass

    def play(self):
        pass

    def tree(self):
        pass

    def switch_tab(self, tab: str) -> None:
        self.active_tab = tab

        buttons = {
            'about': (self.a_button, self.about),
            'search': (self.s_button, self.search),
            'lineups': (self.lp_button, self.lineups),
            'play': (self.p_button, self.play),
            'tree': (self.pt_button, self.tree),
        }

        for name, (button, page) in buttons.items():
            if name == tab:
                button.configure(fg_color=self.TAB_COLORS[1])
                self.clean(self.content_frame)
                page()
            else:
                button.configure(fg_color=self.inactive_color)

    def create_widgets(self) -> None:
        """All buttons, labels, and text boxes go here."""
        self.master_frame = GenieFrame(self, rows=10, columns=10, fg_color="#363636")
        self.grid(self.master_frame, row=0, column=0, rowspan=10, columnspan=10)

        self.tabs_frame = GenieFrame(self.master_frame, rows=1, columns=5, fg_color="transparent")
        self.grid(self.tabs_frame, row=0, column=0, columnspan=10)

        self.content_frame = GenieFrame(self.master_frame, rows=10, columns=10, fg_color="transparent")
        self.grid(self.content_frame, row=1, column=0, rowspan=9, columnspan=10)

        # TABS
        button_font = ("Arial", 15, "bold")
        self.a_button = ctk.CTkButton(self.tabs_frame, text="About", font=button_font, command=lambda: self.switch_tab("about"))
        self.grid(self.a_button, row=0, column=0)

        self.s_button = ctk.CTkButton(self.tabs_frame, text="Search", font=button_font, command=lambda: self.switch_tab("search"))
        self.grid(self.s_button, row=0, column=1)

        self.lp_button = ctk.CTkButton(self.tabs_frame, text="Players", font=button_font, command=lambda: self.switch_tab("lineups"))
        self.grid(self.lp_button, row=0, column=2)

        self.p_button = ctk.CTkButton(self.tabs_frame, text="Play", font=button_font, command=lambda: self.switch_tab("play"))
        self.grid(self.p_button, row=0, column=3)

        self.pt_button = ctk.CTkButton(self.tabs_frame, text="Perm Tree", font=button_font, command=lambda: self.switch_tab("tree"))
        self.grid(self.pt_button, row=0, column=4)

        self.switch_tab("about")

if __name__ == "__main__":
    app = GenieApp(10, 10)
    app.mainloop()