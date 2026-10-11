from flask import Flask, render_template, Response
from pathlib import Path
import pandas as pd
import csv
import io
import os

app = Flask(__name__)

# --- AUTO CSV FINDER - Ekkada unna find chesthundi ---
BASE_DIR = Path(__file__).resolve().parent

def find_csv():
    possible_paths = [
        BASE_DIR / "dataset" / "zomato.csv",
        BASE_DIR / "zomato.csv",
        BASE_DIR.parent / "dataset" / "zomato.csv",
        BASE_DIR.parent / "zomato.csv",
        BASE_DIR / "dashboard" / "zomato.csv",
        Path("dataset/zomato.csv"),
        Path("zomato.csv"),
    ]
    for p in possible_paths:
        if p.exists():
            print(f"CSV Found at: {p}")
            return p
    # okavela dorakkapothe error lo anni paths chupisthundi
    raise FileNotFoundError(f"zomato.csv not found! Checked: {possible_paths}")

csv_file = find_csv()

def load_df():
    try:
        df = pd.read_csv(csv_file)
        if df.shape[1] == 1: # tab separated aithe
            df = pd.read_csv(csv_file, sep="\t")
    except:
        df = pd.read_csv(csv_file, sep="\t")
    return df

def get_data():
    df = load_df()
    df.columns = df.columns.str.strip()

    for col in ["Rating", "Votes", "Average_Cost_for_Two", "Average_Cost_for_two", "Average_Cost_for_Two"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Average_Cost_for_two" in df.columns and "Average_Cost_for_Two" not in df.columns:
        df["Average_Cost_for_Two"] = df["Average_Cost_for_two"]

    city_data = df.groupby("City").size().reset_index(name="Restaurant_Count").sort_values("Restaurant_Count", ascending=False).to_dict("records")
    top_restaurants = df.sort_values(["Rating", "Votes"], ascending=[False, False]).head(10).to_dict("records")
    all_restaurants = df.to_dict("records")

    if "Online_Delivery" in df.columns:
        delivery_data = df.groupby("Online_Delivery").size().reset_index(name="Restaurant_Count").to_dict("records")
    else:
        delivery_data = []

    rating_data = df.groupby("City")["Rating"].mean().round(2).reset_index(name="Average_Rating").sort_values("Average_Rating", ascending=False).to_dict("records")
    cost_data = df.groupby("City")["Average_Cost_for_Two"].mean().round(2).reset_index(name="Average_Cost").sort_values("Average_Cost", ascending=False).to_dict("records")

    total_restaurants = len(df)
    total_cities = df["City"].nunique()
    average_rating = round(df["Rating"].mean(), 2)
    average_cost = round(df["Average_Cost_for_Two"].mean(), 2)

    return city_data, top_restaurants, all_restaurants, delivery_data, rating_data, cost_data, total_restaurants, total_cities, average_rating, average_cost

@app.route("/")
def home():
    city_data, top_restaurants, all_restaurants, delivery_data, rating_data, cost_data, total_restaurants, total_cities, average_rating, average_cost = get_data()
    return render_template("index.html", city_data=city_data, top_restaurants=top_restaurants, all_restaurants=all_restaurants, delivery_data=delivery_data, rating_data=rating_data, cost_data=cost_data, total_restaurants=total_restaurants, total_cities=total_cities, average_rating=average_rating, average_cost=average_cost)

@app.route("/export")
def export_data():
    df = load_df()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(df.columns)
    writer.writerows(df.values.tolist())
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=zomato_restaurants.csv"
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)