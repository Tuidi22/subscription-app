from flask import Flask, render_template, request, redirect
import csv
from datetime import datetime, timedelta
import calendar
import uuid

app = Flask(__name__)
CSV_FILE = "subscriptions.csv"

def load_subscriptions():
    subs = []
    try:
        with open(CSV_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure each subscription has a unique ID
                if 'id' not in row or not row['id']:
                    row['id'] = str(uuid.uuid4())
                day = int(row["day"])
                cost = float(row["cost"])
                today = datetime.now()

                # Calculate next renewal date
                last_day_this_month = calendar.monthrange(today.year, today.month)[1]
                renewal_day = min(day, last_day_this_month)
                next_renewal = today.replace(day=renewal_day)

                if next_renewal < today:
                    month = today.month + 1
                    year = today.year
                    if month > 12:
                        month = 1
                        year += 1
                    last_day_next_month = calendar.monthrange(year, month)[1]
                    renewal_day_next_month = min(day, last_day_next_month)
                    next_renewal = next_renewal.replace(year=year, month=month, day=renewal_day_next_month)

                row["day"] = day
                row["cost"] = cost
                row["next_renewal"] = next_renewal
                subs.append(row)
    except FileNotFoundError:
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id','name','cost','day'])
            writer.writeheader()
    return subs

def save_subscriptions(subs):
    with open(CSV_FILE, 'w', newline='') as f:
        fieldnames = ['id','name','cost','day']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sub in subs:
            writer.writerow({'id': sub['id'], 'name': sub['name'], 'cost': sub['cost'], 'day': sub['day']})

@app.route("/", methods=["GET", "POST"])
def index():
    subs = load_subscriptions()
    sort_by = request.args.get("sort", "next_renewal")
    direction = request.args.get("direction", "asc")

    if request.method == "POST":
        # Adding subscription
        if "add" in request.form:
            name = request.form["name"]
            cost = request.form["cost"]
            day = request.form["day"]
            if name and cost and day:
                subs.append({"id": str(uuid.uuid4()), "name": name, "cost": float(cost), "day": int(day)})
                save_subscriptions(subs)
            return redirect("/")

        # Editing subscription
        elif "edit" in request.form:
            sub_id = request.form["id"]
            for s in subs:
                if s['id'] == sub_id:
                    s['name'] = request.form["name"]
                    s['cost'] = float(request.form["cost"])
                    s['day'] = int(request.form["day"])
                    break
            save_subscriptions(subs)
            return redirect("/")

    reverse = True if direction == "desc" else False
    if sort_by == "cost":
        subs.sort(key=lambda x: x["cost"], reverse=reverse)
    elif sort_by == "alphabetical":
        subs.sort(key=lambda x: x["name"].lower(), reverse=reverse)
    else:
        subs.sort(key=lambda x: x["next_renewal"], reverse=reverse)

    total_cost = sum(sub["cost"] for sub in subs)
    for sub in subs:
        sub["alert"] = sub["next_renewal"] <= datetime.now() + timedelta(days=7)

    return render_template("index.html", subscriptions=subs, total_cost=total_cost,
                           sort_by=sort_by, direction=direction)

@app.route("/delete/<sub_id>")
def delete_subscription(sub_id):
    subs = load_subscriptions()
    subs = [s for s in subs if s['id'] != sub_id]
    save_subscriptions(subs)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
