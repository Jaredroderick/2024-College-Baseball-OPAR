# Importing Libraries
from flask import Flask, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)

# Load the Excel data
EXCEL_FILE = "NCAA_Baseball_Data.xlsx"
df = pd.read_excel(EXCEL_FILE, sheet_name='All Batters')

# Filter and prepare the data
OP_info = ["Name", "School", "PA", "OBP", "wOBA", "ISO", "BB%", "K%", "BABIP", "wRC+", "HR/PA"]
filtered_OP_df = df[OP_info]
filtered_OP_df = filtered_OP_df[filtered_OP_df["PA"] >= 50]  # Filter for players with at least 50 plate appearances
filtered_OP_df = filtered_OP_df.dropna(subset=["School"])  # Remove rows with missing team names

# Create the "OnBase_Ability" column
filtered_OP_df["OnBase_Ability"] = (
    .0628 / (.0628 + .0801 + .0805) * filtered_OP_df["OBP"] + 
    .0801 / (.0628 + .0801 + .0805) * filtered_OP_df["wOBA"] +
    .0805 / (.0628 + .0801 + .0805) * filtered_OP_df["BABIP"]
)

# Create the "Power" column
filtered_OP_df["Power"] = (
    .236 / (.236 + .0474) * filtered_OP_df["ISO"] + 
    .0474 / (.236 + .0474) * filtered_OP_df["HR/PA"] 
)

# Create the "OP" (Offensive Production) column
filtered_OP_df["OP"] = (
    0.1098 * filtered_OP_df["OnBase_Ability"] +
    0.1049 * filtered_OP_df["Power"] +
    0.0273 * filtered_OP_df["BB%"] -
    0.0127 * filtered_OP_df["K%"] 
)

# Create the "OPAR" (Offensive Production Above Replacement) column
op_median = filtered_OP_df["OP"].median()
filtered_OP_df["OPAR"] = filtered_OP_df["OP"] - op_median

# Debug: Save filtered data and print unique teams
filtered_OP_df.to_csv("filtered_data_debug.csv", index=False)
print("Filtered data saved to 'filtered_data_debug.csv'")
print("Filtered DataFrame (with OP and OPAR):")
print(filtered_OP_df.head())

# Route for the main page
@app.route('/')
def home():
    teams = filtered_OP_df["School"].unique()  # Get unique team names
    print("Teams passed to template:", teams)  # Debugging
    return render_template('OPARIndex.html', teams=teams)

# API route to fetch data for a specific team
@app.route('/api/teams/<team_name>/statistics', methods=['GET'])
def get_team_statistics(team_name):
    team_data = filtered_OP_df[filtered_OP_df["School"] == team_name]
    players = team_data.to_dict(orient='records')
    return jsonify({'players': players})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))  # Use PORT from environment variable, or default to 5001 for local
    app.run(host='0.0.0.0', port=5001, debug=True)


