from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
from datetime import datetime, timedelta
from geopy.distance import geodesic
import urllib.parse
import time
from itertools import combinations
from ortools.sat.python import cp_model
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)

# Load dataset
xls = pd.ExcelFile('Dataset.xlsx')
students_df = pd.read_excel(xls, 'Students')
destinations_df = pd.read_excel(xls, 'Places')

# Vehicle capacity
CAR_CAPACITY = 5
BIKE_CAPACITY = 2
AVG_SPEED = 40  # km/h

# Email credentials - use project Gmail/app password
EMAIL_USER = "smart.travel.agent.planner@gmail.com"
EMAIL_PASSWORD = "gvmi hrsr adoc wtvf"

def dist(p1, p2):
    return geodesic(p1, p2).km

def get_destination_coords(name):
    row = destinations_df[destinations_df['Destination_place'] == name]
    if not row.empty:
        return (row.iloc[0]['Latitude'], row.iloc[0]['Longitude'])
    else:
        raise ValueError(f"Destination {name} not found")

def total_route_distance(sequence, destination_coords):
    dist_total = 0
    current = (sequence[0]['Latitude'], sequence[0]['Longitude'])
    points = [(p['Latitude'], p['Longitude']) for p in sequence[1:]] + [destination_coords]
    for pt in points:
        dist_total += dist(current, pt)
        current = pt
    return dist_total

def generate_google_maps_url(group, destination_coords):
    base_url = "https://www.google.com/maps/dir/?api=1"
    start = f"{group[0]['Latitude']},{group[0]['Longitude']}"
    waypoints = "|".join([f"{p['Latitude']},{p['Longitude']}" for p in group[1:]])
    destination = f"{destination_coords[0]},{destination_coords[1]}"
    params = {
        "origin": start,
        "destination": destination,
        "travelmode": "driving",
    }
    if waypoints:
        params["waypoints"] = waypoints
    url = base_url + "&" + urllib.parse.urlencode(params, safe='|')
    return url

def enumerate_groups(students, destination_coords):
    groups = []
    for idx, driver in students.iterrows():
        if driver['Car'] == True:
            cap = CAR_CAPACITY
        elif driver['Bike'] == True:
            cap = BIKE_CAPACITY
        else:
            continue
        possible_passengers = students.drop(idx)
        for r in range(0, cap):
            for subset in combinations(possible_passengers.to_dict('records'), r):
                group = [driver.to_dict()] + list(subset)
                base_cost = total_route_distance(group, destination_coords)
                if driver['Car']:
                    detour_penalty = 0.2 * base_cost * (len(group) - 1)
                elif driver['Bike']:
                    detour_penalty = 0.01 * base_cost * (len(group) - 1)
                else:
                    detour_penalty = 0

                group_cost = base_cost + detour_penalty
                groups.append({
                    'driver': driver.to_dict(),
                    'members': group,
                    'cost': group_cost,
                })
    return groups

def send_trip_email(to_email, subject, html_body):
    msg = EmailMessage()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content('This email requires an HTML-supporting email client.')
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
        smtp.send_message(msg)

def plan_trips(selected_rollnos, destination_name, desired_arrival_str):
    trip_students = students_df.loc[students_df['Roll_No'].isin(selected_rollnos)].copy()
    destination_coords = get_destination_coords(destination_name)
    groups = enumerate_groups(trip_students, destination_coords)

    model = cp_model.CpModel()
    x = {}
    for i, g in enumerate(groups):
        x[i] = model.NewBoolVar(f"group_{i}")

    for _, s in trip_students.iterrows():
        student_id = s['Roll_No']
        model.Add(sum(x[i] for i, g in enumerate(groups) if any(m['Roll_No'] == student_id for m in g['members'])) == 1)

    objective_terms = []
    for i, g in enumerate(groups):
        cost_int = int(g['cost'] * 1000)
        objective_terms.append(cost_int * x[i])
    model.Minimize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = False

    solver.Solve(model)

    chosen_groups = [groups[i] for i in range(len(groups)) if solver.BooleanValue(x[i])]

    now = datetime.now()
    hour, minute = map(int, desired_arrival_str.split(':'))
    desired_arrival = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if desired_arrival < now:
        desired_arrival += timedelta(days=1)

    results = []
    name_to_email = students_df.set_index('Names')['Mails'].to_dict()  # Build name-email map once here

    for g in chosen_groups:
        dist_km = total_route_distance(g['members'], destination_coords)
        eta_hours = dist_km / AVG_SPEED
        start_time_dt = desired_arrival - timedelta(hours=eta_hours)
        maps_url = generate_google_maps_url(g['members'], destination_coords)
        group_names = [m['Names'] for m in g['members']]
        driver_name = g['driver']['Names']
        vehicle_type = 'Car' if g['driver']['Car'] else 'Bike'
        start_time = start_time_dt.strftime("%H:%M")
        eta_min = round(eta_hours * 60)
        distance = round(dist_km, 2)

        res_obj = {
            'vehicle_type': vehicle_type,
            'driver_name': driver_name,
            'group_names': group_names,
            'distance': distance,
            'eta_min': eta_min,
            'start_time': start_time,
            'maps_url': maps_url
        }
        results.append(res_obj)

        # Send emails properly matched by name and email
        for name in group_names:
            mail = name_to_email.get(name)
            if not mail:
                continue

            if name.strip().lower() == driver_name.strip().lower():
                subject = f"[Trip Plan] 🚗 You're the driver for your {vehicle_type} group"
                html_body = f"""
                <div style="font-family:Inter,sans-serif;background:#f5f7fa;padding:24px;border-radius:12px;color:#111;">
                  <h2 style="color:#FF1A1A;font-size:1.5em;margin-bottom:8px;">🚗 Hi <b>{driver_name}</b>,</h2>
                  <p style="font-size:1.07em;">You are <b style="color:#FF1A1A;">the designated <i>driver</i></b> for your <span style="color:#FF1A1A;">{vehicle_type}</span> group trip to <b>{destination_name}</b>.</p>
                  <ul style="margin:16px 0;padding:0 0 0 22px;">
                    <li><b>Pickup sequence:</b> <span style="color:#FF1A1A;">{', '.join(group_names)}</span></li>
                    <li><b>Google Maps route:</b> <a href="{maps_url}" style="color:#4F8EF7;text-decoration:underline;" target="_blank">Click to open route</a></li>
                    <li><b>Distance:</b> <span style="color:#2b8a3e;">{distance} km</span></li>
                    <li><b>Estimated travel time:</b> <span style="color:#F50;">{eta_min} mins</span></li>
                    <li><b>Recommended start time:</b> <span style="color:#c9460b">{start_time}</span></li>
                  </ul>
                  <p>🚦 <b style="color:#FF1A1A;">Driver Tips:</b> Please coordinate with your group if you need adjustments, and confirm you can drive.<br>
                  <span style="font-style:italic;color:#7F7F7F;">Let your group know of any delay or change!</span></p>
                  <hr style="margin:18px 0;border:0;height:1px;background:#eee;">
                  <p style="font-size:1.08em;color:#111;">
                    Safe travels,<br>
                    <span style="font-family:DotGothic16,monospace;font-size:1.2em;color:#FF1A1A;">Smart Travel Agent Planner</span>
                  </p>
                </div>
                """
            else:
                subject = f"[Trip Plan] 🧑‍💼 Your ride group assignment"
                html_body = f"""
                <div style="font-family:Inter,sans-serif;background:#f9fafc;padding:24px;border-radius:12px;color:#111;">
                  <h2 style="color:#2B8A3E;font-size:1.45em;margin-bottom:10px;">🧑‍💼 Hi <b>{name}</b>,</h2>
                  <p style="font-size:1.07em;">
                    You are assigned as a <b style="color:#2B8A3E;font-style:italic;">passenger</b> in the following ride:
                  </p>
                  <ul style="margin:16px 0;padding-left:22px;">
                    <li><b>Driver:</b> <span style="color:#FF1A1A;">{driver_name}</span> (<span style="color:#F50;">{vehicle_type}</span>)</li>
                    <li><b>Pickup sequence:</b> <span style="color:#FF1A1A;">{', '.join(group_names)}</span></li>
                    <li><b>Google Maps route:</b> <a href="{maps_url}" style="color:#4F8EF7;text-decoration:underline;" target="_blank">Click to open route</a></li>
                    <li><b>Distance:</b> <span style="color:#2b8a3e;">{distance} km</span></li>
                    <li><b>Estimated travel time:</b> <span style="color:#F50;">{eta_min} mins</span></li>
                    <li><b>Recommended start time:</b> <span style="color:#c9460b">{start_time}</span></li>
                  </ul>
                  <p>⏰ <b style="color:#2B8A3E;">Passenger Tips:</b> Be ready and coordinate with your group for a smooth journey.<br>
                  <span style="font-style:italic;color:#7F7F7F;">Enjoy your ride and let your driver know if you have any concerns!</span></p>
                  <hr style="margin:16px 0;border:0;height:1px;background:#eee;">
                  <p style="font-size:1.08em;color:#111;">
                    Enjoy your ride,<br>
                    <span style="font-family:DotGothic16,monospace;font-size:1.2em;color:#2B8A3E;">Smart Travel Agent Planner</span>
                  </p>
                </div>
                """
            
            try:
                send_trip_email(mail, subject, html_body)
            except Exception as e:
                print(f"Failed to send email to {mail}: {e}")

    first_to_start = min(results, key=lambda x: x['start_time'])
    return results, first_to_start

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/destination', methods=['GET', 'POST'])
def destination():
    if request.method == 'POST':
        dest_name = request.form.get('destination')
        arrival_time = request.form.get('arrival_time')
        return redirect(url_for('select_students', destination=dest_name, arrival=arrival_time))
    destinations_list = destinations_df['Destination_place'].dropna().unique()
    return render_template('destination.html', destinations=destinations_list)

@app.route('/select_students', methods=['GET', 'POST'])
def select_students():
    destination = request.args.get('destination')
    arrival = request.args.get('arrival')

    if request.method == 'POST':
        selected_names = request.form.getlist('students')
        selected_rollnos = students_df[students_df['Names'].isin(selected_names)]['Roll_No'].tolist()
        time.sleep(2)
        results, first_to_start = plan_trips(selected_rollnos, destination, arrival)
        return render_template('results.html', results=results, first=first_to_start)
    students_list = students_df['Names'].dropna().unique()
    return render_template('select_students.html', students=students_list, destination=destination, arrival=arrival)

if __name__ == '__main__':
    app.run(debug=True)
