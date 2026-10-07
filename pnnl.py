# P&L Calendar
# tkinter GUI for tracking daily profit and loss
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import date
import calendar
import json
import os

DATA_FILE = "pnl_data.json" # Store P&L data in a JSON file

# Add gradient colors for win/loss/empty
COLOR_WIN = "#8fd19e"
COLOR_LOSS = "#f2a6a6"
COLOR_EMPTY = "#e6e6e6"
COLOR_WIN_STRONG = "#2e9e4f"
COLOR_LOSS_STRONG = "#d94a4a"
def blend(light_hex, strong_hex, t):
    """Blend between two hex colors. t=0 gives light, t=1 gives strong."""
    t = max(0.0, min(1.0, t))
    l = [int(light_hex[i:i+2], 16) for i in (1, 3, 5)]
    s = [int(strong_hex[i:i+2], 16) for i in (1, 3, 5)]
    r, g, b = (round(l[i] + (s[i] - l[i]) * t) for i in range(3))
    return f"#{r:02x}{g:02x}{b:02x}"
class PnLCalendar:      
    def __init__(self, root):
        self.root = root
        self.root.title("P&L Calendar")

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

        self.grid_frame = tk.Frame(root)        # Build the calendar grid frame
        self.grid_frame.pack(padx=10, pady=10, fill="both", expand=True) # Configure the grid frame to expand and fill the available space

        for col in range(7):
            self.grid_frame.grid_columnconfigure(col, weight=1) 
        for row in range(1, 7):
            self.grid_frame.grid_rowconfigure(row, weight=1)
            
        calendar.setfirstweekday(calendar.SUNDAY)

        self.stats_lbl = tk.Label(root, text="", font=("Arial", 11))    # Build the statistics label to display win rate and average P&L for the current month
        self.stats_lbl.pack(pady=(0, 10))

        self.render_calendar() # Render the calendar for the current month

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

    def next_month(self):   # Navigate to the next month and refresh the calendar
        self.cur_month += 1
        if self.cur_month == 13:
            self.cur_month = 1
            self.cur_year += 1
        self.refresh()

    def refresh(self):  # Refresh the calendar display and update the title label
        self.title_lbl.config(text=self.month_title())
        self.render_calendar()

    def render_calendar(self):  # Render the calendar grid for the current month displaying P&L values 
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

         # Weekday headers (row 0)
        weekdays = ["Sun","Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for col, name in enumerate(weekdays):
            tk.Label(self.grid_frame, text=name, width=8,
                     font=("Arial", 10, "bold")).grid(row=0, column=col, padx=2, pady=2)

        days = calendar.monthcalendar(self.cur_year, self.cur_month) 
        prefix = f"{self.cur_year}-{self.cur_month:02d}"
        month_vals = [v for k, v in self.data.items() if k.startswith(prefix)]
        max_abs = max((abs(v) for v in month_vals), default=1) or 1
        for row, week in enumerate(days, start=1):
            for col, day in enumerate(week):       # Loop through each week and day in the month creating a label for each day with the corresponding P&L value and color coding based on win/loss/empty
                if day == 0:
                    continue
                key = self.key_for(self.cur_year, self.cur_month, day)  
                value = self.data.get(key)

                if value is None:   # If no value is recorded for the day set the background color to empty and display only the day number
                    bg = COLOR_EMPTY
                    text = str(day)
                else:
                    intensity = abs(value) / max_abs
                    if value > 0:
                        bg = blend(COLOR_WIN, COLOR_WIN_STRONG, intensity)
                    elif value < 0:
                        bg = blend(COLOR_LOSS, COLOR_LOSS_STRONG, intensity)
                    else:
                        bg = COLOR_EMPTY
                    text = f"{day}\n{value:+.0f}"
                    
                is_today = (self.cur_year == self.today.year and         #Highlight the current day
                            self.cur_month == self.today.month and
                            day == self.today.day)
                
                btn = tk.Label(self.grid_frame, text=text, width=8, height=3,
                               bg=bg, relief="solid",
                               borderwidth=3 if is_today else 1,
                               highlightthickness=2 if is_today else 0,
                               highlightbackground="#1a73e8")
                btn.grid(row=row, column=col, padx=2, pady=2)
                btn.bind("<Button-1>", lambda e, d=day: self.edit_day(d))
        self.update_stats()     # Update the statistics label with the win rate and average P&L for the current month

    def edit_day(self, day):    # Open a text box to edit the value for the selected day and update the data
        key = self.key_for(self.cur_year, self.cur_month, day)
        current = self.data.get(key, "")
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

        self.stats_lbl.config(text=f"Win rate: {win_rate:.1f}%   Avg: {avg:+.2f}   Total: {total:+.2f}")  # Update the statistics label with the calculated win rate and average P&L for the current month

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
       
        
        
if __name__ == "__main__":  # Run the P&L Calendar application
    root = tk.Tk()
    app = PnLCalendar(root)
    root.mainloop()