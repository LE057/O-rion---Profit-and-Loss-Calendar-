import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
from datetime import date, datetime
import calendar
import json
import csv
import os
from urllib.parse import quote
import webbrowser
import darkdetect
import shutil
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pnl_data.json") # Store P&L data in a JSON file
CRYPTO_ALIASES = {
    "aave": "AAVE",
    "ada": "ADA",
    "avalanche": "AVAX",
    "avax": "AVAX",
    "bitcoin cash": "BCH",
    "bitcoin": "BTC",
    "bch": "BCH",
    "btc": "BTC",
    "bonk": "BONK",
    "cardano": "ADA",
    "chainlink": "LINK",
    "comp": "COMP",
    "compound": "COMP",
    "doge": "DOGE",
    "dogecoin": "DOGE",
    "etc": "ETC",
    "ethereum": "ETH",
    "ethereum classic": "ETC",
    "eth": "ETH",
    "link": "LINK",
    "litecoin": "LTC",
    "ltc": "LTC",
    "pepe": "PEPE",
    "ripple": "XRP",
    "shib": "SHIB",
    "shiba inu": "SHIB",
    "shiba": "SHIB",
    "sol": "SOL",
    "solana": "SOL",
    "stellar": "XLM",
    "stellar lumens": "XLM",
    "tezos": "XTZ",
    "uni": "UNI",
    "uniswap": "UNI",
    "usdc": "USDC",
    "usd coin": "USDC",
    "xrp": "XRP",
    "xlm": "XLM",
    "xtz": "XTZ",
}

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

def compute_stats(items):
    """items: list of (date_str, pnl) pairs. Returns a dict of stats, or None if empty."""
    items = sorted(items)
    if not items:
        return None
    vals = [v for _, v in items]
    wins = [v for v in vals if v > 0]
    losses = [v for v in vals if v < 0]

    gross_win = sum(wins)
    gross_loss = abs(sum(losses))

    # Streaks (flat days, i.e. exactly 0, break a streak)
    best_win_streak = best_loss_streak = run = 0
    for v in vals:
        if v > 0:
            run = run + 1 if run > 0 else 1
            best_win_streak = max(best_win_streak, run)
        elif v < 0:
            run = run - 1 if run < 0 else -1
            best_loss_streak = max(best_loss_streak, -run)
        else:
            run = 0
    current_streak = run  # + = win streak, - = loss streak

    # Max drawdown on the cumulative P&L curve (starts from 0)
    cum = peak = max_dd = 0
    for v in vals:
        cum += v
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)

    best = max(items, key=lambda x: x[1])
    worst = min(items, key=lambda x: x[1])

    return {
        "days": len(vals),
        "total": sum(vals),
        "win_rate": len(wins) / len(vals) * 100,
        "avg_day": sum(vals) / len(vals),
        "avg_win": gross_win / len(wins) if wins else 0,
        "avg_loss": -gross_loss / len(losses) if losses else 0,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "best": best,
        "worst": worst,
        "best_win_streak": best_win_streak,
        "best_loss_streak": best_loss_streak,
        "current_streak": current_streak,
        "max_drawdown": max_dd,
    }


class PnLCalendar:      
    def __init__(self, root):
        self.root = root
        self.root.title("P&L Calendar")
        self.root.geometry("900x650")
        self.root.minsize(600, 450)
        self.today = date.today()           # Get today's date
        self.cur_year = self.today.year     # Current year and month viewed
        self.cur_month = self.today.month
        self.root.bind("<Left>", lambda e: self.prev_month())
        self.root.bind("<Right>", lambda e: self.next_month())

        self.data = {}
        self.day_details = {}
        self.load_data()    # Load existing P&L data from JSON file

        self.header = tk.Frame(root)    # Build the header with month navigation buttons
        self.header.pack(fill="x", pady=8)     
        tk.Button(self.header, text="<", command=self.prev_month).pack(side="left", padx=10)
        self.title_btn = tk.Button(
            self.header,
            text=self.month_title(),
            font=("Arial", 14, "bold"),
            command=self.open_month_picker,
            relief="flat",
        )
        self.title_btn.pack(side="left", padx=10)
        tk.Button(self.header, text=">", command=self.next_month).pack(side="left", padx=10)
        tk.Button(self.header, text="Clear Month", command=self.clear_month).pack(side="right", padx=10)
        tk.Button(self.header, text="Today" , command=self.go_today).pack(side="left", padx=10)

        self.grid_frame = tk.Frame(root)        # Build the calendar grid frame
        self.grid_frame.pack(padx=10, pady=10, fill="both", expand=True) # Configure the grid frame to expand and fill the available space

        for col in range(8):
            self.grid_frame.grid_columnconfigure(col, weight=1, uniform = "day") 
        
        calendar.setfirstweekday(calendar.SUNDAY)

        self.footer = tk.Frame(root)
        self.footer.pack(fill="x", padx=10, pady=(0, 10))
        self.stats_lbl = tk.Label(
            self.footer,
            text="",
            font=("Arial", 11),
            anchor="w",
        )
        self.stats_lbl.pack(side="left")
        tk.Button(
            self.footer,
            text="Graph",
            command=self.show_graph,
        ).pack(side="right", padx=(0, 6))
        tk.Button(
            self.footer,
            text="Stats",
            command=self.show_stats,
        ).pack(side="right", padx=(0, 6))
        tk.Button(
            self.footer,
            text="Export",
            command=self.export_csv,
        ).pack(side="right", padx=(0, 6))
        tk.Button(
            self.footer,
            text="Trade",
            command=self.prompt_robinhood_trade,
        ).pack(side="right")
        self.day_font = ("Arial", 10)
        self.render_calendar() # Render the calendar for the current month
        # This will update the theme in real time if you change between dark/light mode when the program i running.
        self.dark_mode = darkdetect.isDark()
        self.root.after(1000, self.check_theme)
        self.grid_frame.bind("<Configure>", self.on_resize)

    def load_data(self):        # Load P&L data from JSON file if it exists
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r") as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("Data file is not a dictionary")
            day_details = loaded.pop("_day_details", {})
            if not isinstance(day_details, dict):
                raise ValueError("Day details are not a dictionary")
            for details in day_details.values():
                if (not isinstance(details, dict)
                        or not isinstance(details.get("notes", ""), str)
                        or not isinstance(details.get("tags", ""), str)
                        or not isinstance(details.get("ticker", ""), str)):
                    raise ValueError("Day details have an invalid format")
            self.data = loaded
            self.day_details = day_details
        except Exception:
            # Keep a copy of the bad file so nothing is lost
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = f"{DATA_FILE}.{stamp}.bak"
            shutil.copy2(DATA_FILE, backup)
            self.data = {}
            messagebox.showwarning(
                "Data file problem",
                f"Couldn't read your saved data. A copy of the file was saved as:\n{backup}")

    def save_data(self):    # Save P&L data to JSON file safely
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({**self.data, "_day_details": self.day_details}, f, indent=2)
        os.replace(tmp, DATA_FILE)

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

    def open_month_picker(self):
        window = tk.Toplevel(self.root)
        window.title("Go to month")
        window.transient(self.root)
        window.grab_set()

        form = tk.Frame(window, padx=12, pady=12)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Month").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        month_picker = ttk.Combobox(
            form,
            values=calendar.month_name[1:],
            state="readonly",
            width=12,
        )
        month_picker.current(self.cur_month - 1)
        month_picker.grid(row=0, column=1, sticky="ew", pady=4)

        tk.Label(form, text="Year").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        year_picker = tk.Spinbox(form, from_=1, to=9999, width=8)
        year_picker.delete(0, "end")
        year_picker.insert(0, str(self.cur_year))
        year_picker.grid(row=1, column=1, sticky="w", pady=4)

        def go_to_month():
            try:
                year = int(year_picker.get())
                if not 1 <= year <= 9999:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid year", "Enter a year from 1 to 9999.", parent=window)
                return

            self.cur_year = year
            self.cur_month = month_picker.current() + 1
            self.refresh()
            window.destroy()

        buttons = tk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(8, 0))
        tk.Button(buttons, text="Cancel", command=window.destroy).pack(side="right", padx=(6, 0))
        tk.Button(buttons, text="Go", command=go_to_month).pack(side="right")
        window.bind("<Return>", lambda _event: go_to_month())
        window.bind("<Escape>", lambda _event: window.destroy())
        year_picker.focus_set()

    def next_month(self):   # Navigate to the next month and refresh the calendar
        self.cur_month += 1
        if self.cur_month == 13:
            self.cur_month = 1
            self.cur_year += 1
        self.refresh()

    def refresh(self):  # Refresh the calendar display and update the title label
        self.title_btn.config(text=self.month_title())
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
                key = self.key_for(d.year, d.month, d.day)
                details = self.day_details.get(key, {})
                has_details = bool(details.get("notes") or details.get("tags") or details.get("ticker"))

                cell = tk.Frame(self.grid_frame, bg=bg)
                cell.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)

                # Day number, top-left (blue badge for today)
                day_lbl = tk.Label(cell, text=f"{d.day}{' *' if has_details else ''}", bg=bg, fg=fg,
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

    def edit_day(self, day):    # Edit the P&L, notes, and tags for a day
        key = self.key_for(self.cur_year, self.cur_month, day)
        details = self.day_details.get(key, {})
        current = self.data.get(key, "")
        window = tk.Toplevel(self.root)
        window.title(f"Day Details - {self.cur_month}/{day}/{self.cur_year}")
        window.transient(self.root)
        window.grab_set()

        form = tk.Frame(window, padx=12, pady=12)
        form.pack(fill="both", expand=True)
        tk.Label(form, text="P&L ($)").grid(row=0, column=0, sticky="w", pady=4)
        pnl_entry = tk.Entry(form, width=32)
        pnl_entry.grid(row=0, column=1, sticky="ew", pady=4)
        if current != "":
            pnl_entry.insert(0, f"{current:g}")

        tk.Label(form, text="Ticker").grid(row=1, column=0, sticky="w", pady=4)
        ticker_entry = tk.Entry(form, width=32)
        ticker_entry.grid(row=1, column=1, sticky="ew", pady=4)
        ticker_entry.insert(0, details.get("ticker", ""))

        tk.Label(form, text="Tags (comma-separated)").grid(row=2, column=0, sticky="w", pady=4)
        tags_entry = tk.Entry(form, width=32)
        tags_entry.grid(row=2, column=1, sticky="ew", pady=4)
        tags_entry.insert(0, details.get("tags", ""))

        tk.Label(form, text="Notes").grid(row=3, column=0, sticky="nw", pady=4)
        notes_text = tk.Text(form, width=32, height=6, wrap="word")
        notes_text.grid(row=3, column=1, sticky="ew", pady=4)
        notes_text.insert("1.0", details.get("notes", ""))
        form.grid_columnconfigure(1, weight=1)

        def save_day():
            pnl_value = pnl_entry.get().strip()
            if pnl_value:
                try:
                    self.data[key] = float(pnl_value)
                except ValueError:
                    messagebox.showerror("Error", "Enter a number please", parent=window)
                    return
            else:
                self.data.pop(key, None)

            notes = notes_text.get("1.0", "end-1c").strip()
            tags = ", ".join(tag.strip() for tag in tags_entry.get().split(",") if tag.strip())
            ticker = ticker_entry.get().strip()
            if notes or tags or ticker:
                self.day_details[key] = {"notes": notes, "tags": tags, "ticker": ticker}
            else:
                self.day_details.pop(key, None)

            self.save_data()
            window.destroy()
            self.render_calendar()

        buttons = tk.Frame(form)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(8, 0))
        tk.Button(
            buttons,
            text="Open TradingView chart",
            command=lambda: self.open_chart(ticker_entry.get(), window),
        ).pack(side="left", padx=(0, 6))
        tk.Button(buttons, text="Cancel", command=window.destroy).pack(side="right", padx=(6, 0))
        tk.Button(buttons, text="Save", command=save_day).pack(side="right")
        window.bind("<Escape>", lambda _event: window.destroy())
        pnl_entry.focus_set()

    def prompt_robinhood_trade(self):
        ticker = simpledialog.askstring(
            "Trade on Robinhood",
            "Enter a ticker symbol:",
            parent=self.root,
        )
        if ticker is not None:
            self.open_robinhood_stock(ticker, self.root)

    def open_robinhood_stock(self, ticker, parent):
        ticker = ticker.strip()
        if not ticker:
            messagebox.showwarning("Ticker required", "Enter a ticker symbol first.", parent=parent)
            return
        crypto_symbol = CRYPTO_ALIASES.get(ticker.casefold())
        if crypto_symbol:
            robinhood_url = f"https://robinhood.com/crypto/{crypto_symbol}"
        else:
            robinhood_url = f"https://robinhood.com/stocks/{quote(ticker, safe='')}"
        if not webbrowser.open(robinhood_url):
            messagebox.showerror(
                "Could not open Robinhood",
                "Your default browser could not be opened.",
                parent=parent,
            )

    def open_chart(self, ticker, parent):
        ticker = ticker.strip()
        if not ticker:
            messagebox.showwarning("Ticker required", "Enter a ticker symbol first.", parent=parent)
            return
        chart_url = f"https://www.tradingview.com/chart/?symbol={quote(ticker, safe='')}"
        if not webbrowser.open(chart_url):
            messagebox.showerror("Could not open chart", "Your default browser could not be opened.", parent=parent)

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
        keys_to_delete = {
            key for key in (*self.data, *self.day_details) if key.startswith(prefix)
        }
        if not keys_to_delete:
            messagebox.showinfo("Info", "No trades to clear for this month.")
            return
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to clear all trades for {self.month_title()}?")
        if confirm:
            for k in keys_to_delete:
                self.data.pop(k, None)
                self.day_details.pop(k, None)
            self.save_data()
            self.render_calendar()
    def check_theme(self):
        current_mode = darkdetect.isDark()

        if current_mode != self.dark_mode:
            self.dark_mode = current_mode
            update_colors()
            self.render_calendar()

        self.root.after(1000, self.check_theme)
        
    def export_csv(self):
        keys = sorted(set(self.data) | set(self.day_details))
        if not keys:
            messagebox.showinfo("Info", "No data to export yet.")
            return

        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export P&L to CSV",
            defaultextension=".csv",
            initialfile=f"pnl_export_{date.today().isoformat()}.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:  # user cancelled
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "P&L", "Ticker", "Tags", "Notes"])
                for key in keys:
                    details = self.day_details.get(key, {})
                    writer.writerow([
                        key,
                        self.data.get(key, ""),
                        details.get("ticker", ""),
                        details.get("tags", ""),
                        details.get("notes", ""),
                    ])
        except OSError as e:
            messagebox.showerror("Export failed", f"Couldn't write the file:\n{e}")
            return

        messagebox.showinfo("Exported", f"Saved {len(keys)} days to:\n{path}")
        
    def show_stats(self):
        window = tk.Toplevel(self.root)
        window.title("Trading Stats")
        window.transient(self.root)

        scope = tk.StringVar(value="month")
        body = tk.Frame(window, padx=16, pady=12)

        top = tk.Frame(window)
        top.pack(fill="x", padx=16, pady=(12, 0))
        tk.Radiobutton(top, text=self.month_title(), variable=scope,
                       value="month", command=lambda: draw()).pack(side="left")
        tk.Radiobutton(top, text="All Time", variable=scope,
                       value="all", command=lambda: draw()).pack(side="left", padx=10)
        body.pack(fill="both", expand=True)

        def draw():
            for w in body.winfo_children():
                w.destroy()

            prefix = f"{self.cur_year}-{self.cur_month:02d}"
            items = [(k, v) for k, v in self.data.items()
                     if scope.get() == "all" or k.startswith(prefix)]
            s = compute_stats(items)
            if s is None:
                tk.Label(body, text="No trades logged for this period.").pack()
                return

            pf = f"{s['profit_factor']:.2f}" if s["profit_factor"] is not None else "n/a"
            streak = s["current_streak"]
            if streak > 0:
                cur = f"{streak} win{'s' if streak != 1 else ''}"
            elif streak < 0:
                cur = f"{-streak} loss{'es' if streak != -1 else ''}"
            else:
                cur = "none"

            rows = [
                ("Trading days", str(s["days"])),
                ("Total P&L", fmt_money(s["total"], 2)),
                ("Win rate", f"{s['win_rate']:.1f}%"),
                ("Avg day", fmt_money(s["avg_day"], 2)),
                ("Avg win", fmt_money(s["avg_win"], 2)),
                ("Avg loss", fmt_money(s["avg_loss"], 2)),
                ("Profit factor", pf),
                ("Best day", f"{fmt_money(s['best'][1], 2)}  ({s['best'][0]})"),
                ("Worst day", f"{fmt_money(s['worst'][1], 2)}  ({s['worst'][0]})"),
                ("Current streak", cur),
                ("Longest win streak", str(s["best_win_streak"])),
                ("Longest loss streak", str(s["best_loss_streak"])),
                ("Max drawdown", fmt_money(-s["max_drawdown"], 2)),
            ]
            for i, (label, value) in enumerate(rows):
                tk.Label(body, text=label, anchor="w").grid(row=i, column=0, sticky="w", pady=2)
                tk.Label(body, text=value, anchor="e", font=("Arial", 11, "bold")
                         ).grid(row=i, column=1, sticky="e", padx=(24, 0), pady=2)
            body.grid_columnconfigure(1, weight=1)

        draw()
        window.bind("<Escape>", lambda _e: window.destroy())  
        
    def show_graph(self):
        window = tk.Toplevel(self.root)
        window.title("P&L Graph")
        window.geometry("820x480")

        view = tk.StringVar(value="curve")
        scope = tk.StringVar(value="month")

        controls = tk.Frame(window)
        controls.pack(fill="x", padx=10, pady=(8, 0))
        tk.Radiobutton(controls, text="Equity Curve", variable=view,
                       value="curve", command=lambda: draw()).pack(side="left")
        tk.Radiobutton(controls, text="Daily P&L", variable=view,
                       value="bars", command=lambda: draw()).pack(side="left", padx=(0, 20))
        tk.Radiobutton(controls, text=self.month_title(), variable=scope,
                       value="month", command=lambda: draw()).pack(side="left")
        tk.Radiobutton(controls, text="All Time", variable=scope,
                       value="all", command=lambda: draw()).pack(side="left")

        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        def draw():
            ax.clear()
            prefix = f"{self.cur_year}-{self.cur_month:02d}"
            items = sorted(
                (datetime.strptime(k, "%Y-%m-%d"), v)
                for k, v in self.data.items()
                if scope.get() == "all" or k.startswith(prefix)
            )

            if not items:
                ax.text(0.5, 0.5, "No trades logged for this period",
                        ha="center", va="center", transform=ax.transAxes)
                canvas.draw_idle()
                return

            dates = [d for d, _ in items]
            vals = [v for _, v in items]
            period = self.month_title() if scope.get() == "month" else "All Time"

            if view.get() == "curve":
                cum, total = [], 0
                for v in vals:
                    total += v
                    cum.append(total)
                line_color = COLOR_WIN_STRONG if cum[-1] >= 0 else COLOR_LOSS_STRONG
                ax.plot(dates, cum, color=line_color, linewidth=2, marker="o", markersize=4)
                ax.fill_between(dates, cum, 0, where=[c >= 0 for c in cum],
                                color=COLOR_WIN_STRONG, alpha=0.2, interpolate=True)
                ax.fill_between(dates, cum, 0, where=[c < 0 for c in cum],
                                color=COLOR_LOSS_STRONG, alpha=0.2, interpolate=True)
                ax.set_title(f"Equity Curve - {period}  ({fmt_money(cum[-1])})")
                ax.set_ylabel("Cumulative P&L")
            else:
                ax.bar(dates, vals, width=0.8,
                       color=[COLOR_WIN_STRONG if v > 0 else COLOR_LOSS_STRONG for v in vals])
                ax.set_title(f"Daily P&L - {period}")
                ax.set_ylabel("P&L")

            ax.axhline(0, color="black", linewidth=0.8)
            ax.grid(alpha=0.25)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt_money(x)))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            fig.autofmt_xdate()
            fig.tight_layout()
            canvas.draw_idle()

        draw()

if __name__ == "__main__":  # Run the P&L Calendar application
    root = tk.Tk()
    app = PnLCalendar(root)
    root.mainloop()