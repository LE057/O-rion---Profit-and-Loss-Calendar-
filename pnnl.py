import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import date
import calendar
import json
import os
import darkdetect

DATA_FILE = "pnl_data.json" # Store P&L data in a JSON file

# Add gradient colors for win/loss/empty
# if darkdetect.isDark(): # This adjust the buttons to adapt if the operating system is in dark mode or light mode 
#     COLOR_WIN = "#3d7a4a"
#     COLOR_LOSS = "#7a3d3d"
#     COLOR_EMPTY = "#333333"
#     COLOR_WIN_STRONG = "#4caf50"
#     COLOR_LOSS_STRONG = "#f44336"
#     COLOR_TEXT = "#ffffff"
# else:
#     COLOR_WIN = "#8fd19e"
#     COLOR_LOSS = "#f2a6a6"
#     COLOR_EMPTY = "#e6e6e6"
#     COLOR_WIN_STRONG = "#2e9e4f"
#     COLOR_LOSS_STRONG = "#d94a4a"
#     COLOR_TEXT = "#000000"
def update_colors():
    global COLOR_WIN, COLOR_LOSS, COLOR_EMPTY
    global COLOR_WIN_STRONG, COLOR_LOSS_STRONG, COLOR_TEXT
    global COLOR_HEADER, COLOR_GRID, COLOR_OUTSIDE, COLOR_DIM
    if darkdetect.isDark(): #This adjust the buttons to adapt if the operating system is in dark mode or light mode 
        COLOR_WIN = "#3d7a4a"
        COLOR_LOSS = "#7a3d3d"
        COLOR_EMPTY = "#333333"
        COLOR_WIN_STRONG = "#4caf50"
        COLOR_LOSS_STRONG = "#f44336"
        COLOR_TEXT = "#ffffff"
        COLOR_HEADER = "#2a2a2a"
        COLOR_GRID = "#555555"
        COLOR_OUTSIDE = "#222222"
        COLOR_DIM = "#777777"
    else:
        COLOR_WIN = "#8fd19e"
        COLOR_LOSS = "#f2a6a6"
        COLOR_EMPTY = "#e6e6e6"
        COLOR_WIN_STRONG = "#2e9e4f"
        COLOR_LOSS_STRONG = "#d94a4a"
        COLOR_TEXT = "#000000"
        COLOR_HEADER = "#d9d9d9"
        COLOR_GRID = "#b0b0b0"
        COLOR_OUTSIDE = "#f4f4f4"
        COLOR_DIM = "#a0a0a0"
update_colors()  # Initialize colors based on the current theme

def blend(light_hex, strong_hex, t):
    """Blend between two hex colors. t=0 gives light, t=1 gives strong."""
    t = max(0.0, min(1.0, t))
    l = [int(light_hex[i:i+2], 16) for i in (1, 3, 5)]
    s = [int(strong_hex[i:i+2], 16) for i in (1, 3, 5)]
    r, g, b = (round(l[i] + (s[i] - l[i]) * t) for i in range(3))
    return f"#{r:02x}{g:02x}{b:02x}"

def fmt_money(value, decimals=0):
    """Format a number as +$1,250 or -$1,250."""
    rounded = round(abs(value), decimals)
    if rounded == 0:
        return f"${0:,.{decimals}f}"
    sign = "+" if value > 0 else "-"
    return f"{sign}${rounded:,.{decimals}f}"

class PnLCalendar:      
    def __init__(self, root):
        self.root = root
        self.root.title("P&L Calendar")
        self.root.geometry("900x650")
        self.root.minsize(600, 450)
        self.today = date.today()           # Get today's date
        self.cur_year = self.today.year     # Current year and month viewed
        self.cur_month = self.today.month

        self.data = {}
        self.load_data()    # Load existing P&L data from JSON file

        self.header = tk.Frame(root)    # Build the header with month navigation buttons
        self.header.pack(fill="x", pady=8)     
        tk.Button(self.header, text="<", command=self.prev_month).pack(side="left", padx=10)
        self.title_lbl = tk.Label(self.header, text=self.month_title(), font=("Arial", 14, "bold"))
        self.title_lbl.pack(side="left", padx=10)
        tk.Button(self.header, text=">", command=self.next_month).pack(side="left", padx=10)
        tk.Button(self.header, text="Clear Month", command=self.clear_month).pack(side="right", padx=10)
        tk.Button(self.header, text="Today" , command=self.go_today).pack(side="left", padx=10)

        self.grid_frame = tk.Frame(root)        # Build the calendar grid frame
        self.grid_frame.pack(padx=10, pady=10, fill="both", expand=True) # Configure the grid frame to expand and fill the available space

        for col in range(8):
            self.grid_frame.grid_columnconfigure(col, weight=1, uniform = "day") 
        
        calendar.setfirstweekday(calendar.SUNDAY)

        self.stats_lbl = tk.Label(root, text="", font=("Arial", 11))    # Build the statistics label to display win rate and average P&L for the current month
        self.stats_lbl.pack(pady=(0, 10))
        self.day_font = ("Arial", 10)
        self.render_calendar() # Render the calendar for the current month
        # This will update the theme in real time if you change between dark/light mode when the program i running.
        self.dark_mode = darkdetect.isDark()
        self.root.after(1000, self.check_theme)
        self.grid_frame.bind("<Configure>", self.on_resize)
    def load_data(self):        # Load P&L data from JSON file if it exists
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save_data(self):    # Save P&L data to JSON file
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def key_for(self, year, month, day):    # Generate a key for storing P&L data in the format: YYYY-MM-DD
        return f"{year}-{month:02d}-{day:02d}"

    def month_title(self):  # Return the title for the current month and year
        return f"{calendar.month_name[self.cur_month]} {self.cur_year}"

    def prev_month(self):   # Navigate to the previous month and refresh the calendar
        self.cur_month -= 1
        if self.cur_month == 0:
            self.cur_month = 12
            self.cur_year -= 1
        self.refresh()
        
    def go_today(self):
        self.cur_year = self.today.year
        self.cur_month = self.today.month
        self.refresh()

    def next_month(self):   # Navigate to the next month and refresh the calendar
        self.cur_month += 1
        if self.cur_month == 13:
            self.cur_month = 1
            self.cur_year += 1
        self.refresh()

    def refresh(self):  # Refresh the calendar display and update the title label
        self.title_lbl.config(text=self.month_title())
        self.render_calendar()

    def on_resize(self, event):
        cell_h = event.height // 7
        size = max(9, min(22, cell_h // 4))
        self.day_font = ("Arial", size)
        for lbl in self.pnl_labels:
            lbl.config(font=self.day_font)
        for lbl in self.day_labels:
            lbl.config(font=("Arial", max(8, size - 3), "bold"))

    def render_calendar(self):  # Render the calendar grid for the current month displaying P&L values 
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.day_labels = []
        self.pnl_labels = []
        self.grid_frame.config(bg=COLOR_GRID)   # shows through as grid lines

        # Weekday header bar
        weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT", "WEEK"]
        for col, name in enumerate(weekdays):
            tk.Label(self.grid_frame, text=name, font=("Arial", 10, "bold"),
                     bg=COLOR_HEADER, fg=COLOR_TEXT, pady=6
                     ).grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        # Includes days from the previous/next month to fill out the weeks
        weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(
            self.cur_year, self.cur_month)

        prefix = f"{self.cur_year}-{self.cur_month:02d}"
        month_vals = [v for k, v in self.data.items() if k.startswith(prefix)]
        max_abs = max((abs(v) for v in month_vals), default=1) or 1
        
        # Weekly totals (only counts days inside the viewed month)
        week_totals = []
        for week in weeks:
            vals = [self.data.get(self.key_for(d.year, d.month, d.day))
                for d in week if d.month == self.cur_month]
            vals = [v for v in vals if v is not None]
            week_totals.append(sum(vals) if vals else None)
        max_week_abs = max((abs(t) for t in week_totals if t is not None), default=1) or 1

        # Only the rows actually used should expand
        for r in range(1, 7):
            self.grid_frame.grid_rowconfigure(
                r, weight=1 if r <= len(weeks) else 0, uniform="week")

        for row, week in enumerate(weeks, start=1):
            for col, d in enumerate(week):
                in_month = (d.month == self.cur_month)
                value = self.data.get(self.key_for(d.year, d.month, d.day)) if in_month else None

                if not in_month:
                    bg = COLOR_OUTSIDE
                elif value is None or value == 0:
                    bg = COLOR_EMPTY
                elif value > 0:
                    bg = blend(COLOR_WIN, COLOR_WIN_STRONG, abs(value) / max_abs)
                else:
                    bg = blend(COLOR_LOSS, COLOR_LOSS_STRONG, abs(value) / max_abs)

                fg = COLOR_TEXT if in_month else COLOR_DIM
                is_today = (d == self.today)

                cell = tk.Frame(self.grid_frame, bg=bg)
                cell.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)

                # Day number, top-left (blue badge for today)
                day_lbl = tk.Label(cell, text=str(d.day), bg=bg, fg=fg,
                                   font=("Arial", 9, "bold"), anchor="nw")
                if is_today:
                    day_lbl.config(bg="#1a73e8", fg="#ffffff", padx=5)
                day_lbl.pack(anchor="nw", padx=5, pady=(4, 0))
                self.day_labels.append(day_lbl)

                # P&L value, centered in the remaining space
                pnl_text = fmt_money(value) if value is not None else ""
                pnl_lbl = tk.Label(cell, text=pnl_text, bg=bg, fg=fg,
                                   font=self.day_font)
                pnl_lbl.pack(expand=True)
                self.pnl_labels.append(pnl_lbl)

                if in_month:
                    for w in (cell, day_lbl, pnl_lbl):
                        w.bind("<Button-1>", lambda e, dd=d.day: self.edit_day(dd))
                        
            total = week_totals[row - 1]
            if total is None or total == 0:
                wbg = COLOR_EMPTY
            elif total > 0:
                wbg = blend(COLOR_WIN, COLOR_WIN_STRONG, abs(total) / max_week_abs)
            else:
                wbg = blend(COLOR_LOSS, COLOR_LOSS_STRONG, abs(total) / max_week_abs)

            wcell = tk.Frame(self.grid_frame, bg=wbg)
            wcell.grid(row=row, column=7, sticky="nsew", padx=1, pady=1)

            wk_lbl = tk.Label(wcell, text=f"Wk {row}", bg=wbg, fg=COLOR_DIM,
                              font=("Arial", 9, "bold"), anchor="nw")
            wk_lbl.pack(anchor="nw", padx=5, pady=(4, 0))
            self.day_labels.append(wk_lbl)

            wtotal_lbl = tk.Label(wcell, text=fmt_money(total) if total is not None else "",
                                  bg=wbg, fg=COLOR_TEXT, font=self.day_font)
            wtotal_lbl.pack(expand=True)
            self.pnl_labels.append(wtotal_lbl)

        self.update_stats()   

    def edit_day(self, day):    # Open a text box to edit the value for the selected day and update the data
        key = self.key_for(self.cur_year, self.cur_month, day)
        current = self.data.get(key, "")
        if current != "":
            current = f"{current:g}"
        val = simpledialog.askstring("Enter P&L", f"P&L for {self.cur_month}/{day}/{self.cur_year}:",initialvalue=str(current))
        if val is None:
            return
        val = val.strip()
        if val == "":
            self.data.pop(key, None)
        else:
            try:
                self.data[key] = float(val)
            except ValueError:
                messagebox.showerror("Error", "Enter a number please")  # Display an error message if the input is not a valid number
                return
        self.save_data()
        self.render_calendar()

    def update_stats(self):     # Update the statistics label with the win rate and average P&L for the current month
        prefix = f"{self.cur_year}-{self.cur_month:02d}"
        month_vals = [v for k, v in self.data.items() if k.startswith(prefix)]

        if not month_vals:  # If there are no trades logged for the current month display a message indicating that no trades have been logged yet
            self.stats_lbl.config(text="No trades logged yet")
            return

        wins = len([v for v in month_vals if v > 0])    # Count the number of winning trades for the current month
        win_rate = wins / len(month_vals) * 100         # Calculate the win rate as a percentage of winning trades to total trades for the current month
        avg = sum(month_vals) / len(month_vals)         # Calculate the average P&L for the current month by summing all P&L values and dividing by the total number of trades
        total = sum(month_vals) # Calculate the total P&L for the current month by summing all P&L values

        self.stats_lbl.config(text=f"Win rate: {win_rate:.1f}%   Avg: {fmt_money(avg, 2)}   Total: {fmt_money(total, 2)}")  # Update the statistics label with the calculated win rate and average P&L for the current month

    def clear_month(self):
        prefix = f"{self.cur_year}-{self.cur_month:02d}"
        keys_to_delete = [k for k in self.data if k.startswith(prefix)]
        if not keys_to_delete:
            messagebox.showinfo("Info", "No trades to clear for this month.")
            return
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to clear all trades for {self.month_title()}?")
        if confirm:
            for k in keys_to_delete:
                del self.data[k]
            self.save_data()
            self.render_calendar()
    def check_theme(self):
        current_mode = darkdetect.isDark()

        if current_mode != self.dark_mode:
            self.dark_mode = current_mode
            update_colors()
            self.render_calendar()

        self.root.after(1000, self.check_theme)
       
        
        
if __name__ == "__main__":  # Run the P&L Calendar application
    root = tk.Tk()
    app = PnLCalendar(root)
    root.mainloop()