# Profit & Loss Calendar

# What it does

This is a desktop app coded in Python using the Tkinter library that helps traders track their daily profit and loss on a calendar.

- Calendar desktop app
- Click on any date to enter the days profit or loss (positive or negative)
- Each box that has a value will either be colored in with green or red
  - Green = Profits
  - Red = Losses
  - Gray = no p&l logged
- Displays win rate and average p&l for the days logged in the month so far.
  - Win rate is calculated by the amount of winning days divided by the total about of traded days for the month
  - Average p&l is the overall average across all traded days for the month with wins and losses combined
 - Data is saved to local pnl_data.json file
   
# Requirements

- Python 3.x (Tkinter is included with standard python installs)
- No external packages
