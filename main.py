from lg_classes import Lineup, Player
from predictor import Predictor
import customtkinter as ctk
from typing import Any
from PIL import Image
import apa_client

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
        for widget in frame.winfo_children():
            widget.destroy()

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
    def sp_button(self, name: str, status_widget: ctk.CTkLabel):
        players = apa.search_player(name)
        
        if not players:
            status_widget.configure(text="No Player Found!", text_color="red")
            return

        status_widget.configure(text=f"{name} Found!", text_color="green")

        player = players[0]
        alias_id = player["aliases"][-1]["id"]

        status_widget.configure(text=f"Fetching Teams!", text_color="yellow")

        team_data = apa.get_teams(alias_id)
        current_teams = team_data["alias"].get("currentTeams", [])
        
        player_level = next(
            record["skillLevel"]
            for record in current_teams
            if record["__typename"] == "EightBallPlayer"
        )
    
        matches = apa.get_player_matches(
            alias_id=alias_id,
            days=365,
            same_sl_only=True,
            target_sl=player_level
        )

        print(f"{player['firstName']} {player['lastName']}")
        print(apa.get_skill_level(matches, player_level))

    def st_button(self, name: str, status_widget: ctk.CTkLabel):
        team = apa.find_team(name)
        
        if not team:
            status_widget.configure(text="No Team Found!", text_color="red")
            return

        print(team)

        status_widget.configure(text=f"{name} Found!", text_color="green")
        
    def search(self):
        status_container = GenieFrame(self.content_frame, rows=1, columns=2, fg_color="transparent")
        self.grid(status_container, row=0, column=0, columnspan=10, sticky="")

        status = ctk.CTkLabel(status_container, text="Status: ", anchor="e", font=("Trebuchet MS", 20, "bold"))
        status_val = ctk.CTkLabel(status_container, text="___", text_color="yellow", anchor="w", font=("Trebuchet MS", 20, "bold"))

        self.grid(status, row=0, column=0)
        self.grid(status_val, row=0, column=1)

        search_player_box = ctk.CTkEntry(
            self.content_frame,
            placeholder_text="Player Name",
            justify="center"
        )
        self.grid(search_player_box, row=1, column=0, columnspan=5)

        search_player_button = ctk.CTkButton(
            self.content_frame,
            text="🔍 Search Player",
            command=lambda: self.sp_button(search_player_box.get(), status_val)
        )
        self.grid(search_player_button, row=1, column=5, columnspan=5)


        search_team_box = ctk.CTkEntry(
            self.content_frame,
            placeholder_text="Team Name",
            justify="center"
        )
        self.grid(search_team_box, row=2, column=0, columnspan=5)

        search_team_button = ctk.CTkButton(
            self.content_frame,
            text="🔍 Search Team",
            command=lambda: self.st_button(search_team_box.get(), status_val)
        )
        self.grid(search_team_button, row=2, column=5, columnspan=5)

        filler = GenieFrame(self.content_frame, 1, 1)
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