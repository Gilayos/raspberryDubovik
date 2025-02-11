import random
import time
import threading

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ------------------------------------------------------------------------------
# Global states for Generator
# ------------------------------------------------------------------------------
generator_running = False
generator_paused = False
generator_start_time = 0
generator_elapsed_time = 0
generator_total_working_hours = 0.0  # in hours

# Generator power cycles among [50, 75, 100]
generator_power = 50
# Always show temperature as "UnAvailable"
generator_temperature = "UnAvailable"

generator_status = "Idle"

# Define each option's total run time in seconds
GENERATOR_TIME_OPTIONS = {
    "4cyl_under_250k": 3600,        # 1 hour
    "over_4cyl_or_over_250k": 5400, # 1.5 hours
    "over_4cyl_and_over_250k": 7200,# 2 hours
    "manual": 0                     # manual run
}

# Human-friendly Hebrew labels
GENERATOR_TIME_LABELS = {
    "4cyl_under_250k": "שעה",
    "over_4cyl_or_over_250k": "שעה וחצי",
    "over_4cyl_and_over_250k": "שעתיים",
    "manual": "ידני"
}

chosen_run_time = 0
chosen_run_time_label = ""

# ------------------------------------------------------------------------------
# Global states for Evaporate
# ------------------------------------------------------------------------------
evaporate_running = False
evaporate_paused = False
evaporate_start_time = 0
evaporate_elapsed_time = 0
evaporate_total_working_hours = 0.0
evaporate_temperature = "UnAvailable"
evaporate_status = "Idle"

# ------------------------------------------------------------------------------
# Background thread to update elapsed times every 1 second
# ------------------------------------------------------------------------------
def update_elapsed_times():
    global generator_running, generator_paused, generator_start_time, generator_elapsed_time
    global evaporate_running, evaporate_paused, evaporate_start_time, evaporate_elapsed_time

    while True:
        time.sleep(1)
        # Generator
        if generator_running and not generator_paused:
            generator_elapsed_time = time.time() - generator_start_time

        # Evaporate
        if evaporate_running and not evaporate_paused:
            evaporate_elapsed_time = time.time() - evaporate_start_time

threading.Thread(target=update_elapsed_times, daemon=True).start()

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.route('/')
def index():
    """Home page with buttons to Generator / Evaporate / Settings."""
    return render_template('index.html')

# ------------------------------------------------------------------------------
# Generator
# ------------------------------------------------------------------------------
@app.route('/generator', methods=['GET', 'POST'])
def generator():
    global generator_running, generator_paused, generator_start_time, generator_elapsed_time
    global generator_total_working_hours, generator_power, generator_temperature
    global generator_status, chosen_run_time, chosen_run_time_label

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'choose_time_option':
            chosen_option = request.form.get('time_option')
            chosen_run_time = GENERATOR_TIME_OPTIONS[chosen_option]
            chosen_run_time_label = GENERATOR_TIME_LABELS[chosen_option]

        elif action == 'start':
            if not generator_running:
                generator_running = True
                generator_paused = False
                generator_status = "Started"
                generator_start_time = time.time() - generator_elapsed_time
            elif generator_paused:
                generator_paused = False
                generator_status = "Started"

        elif action == 'pause':
            if generator_running and not generator_paused:
                generator_paused = True
                generator_status = "Paused"

        elif action == 'stop':
            if generator_running:
                # Accumulate hours
                generator_total_working_hours += generator_elapsed_time / 3600.0
                generator_running = False
                generator_paused = False
                generator_status = "Idle"
                generator_elapsed_time = 0
                chosen_run_time = 0
                chosen_run_time_label = ""

        elif action == 'change_power':
            # Cycle power among [50 -> 75 -> 100 -> 50]
            if generator_power == 50:
                generator_power = 75
            elif generator_power == 75:
                generator_power = 100
            else:
                generator_power = 50

        # Temperature is always "UnAvailable", so do nothing else

    # Auto-stop if time is up
    if chosen_run_time > 0 and generator_elapsed_time >= chosen_run_time:
        generator_total_working_hours += chosen_run_time / 3600.0
        generator_running = False
        generator_paused = False
        generator_status = "Idle"
        generator_elapsed_time = 0
        chosen_run_time = 0
        chosen_run_time_label = ""

    return render_template('generator.html',
                           # Jinja2 variables inserted into HTML
                           elapsed_time=int(generator_elapsed_time),
                           total_hours=round(generator_total_working_hours, 2),
                           power=generator_power,
                           temperature=generator_temperature,
                           status=generator_status,
                           chosen_run_time=int(chosen_run_time),
                           chosen_run_time_label=chosen_run_time_label)

@app.route('/generator_status')
def generator_status_api():
    """
    JSON with:
      - elapsed_time
      - chosen_run_time
      - chosen_run_time_label
      - status
    """
    global generator_elapsed_time, chosen_run_time, chosen_run_time_label, generator_status
    return jsonify({
        'elapsed_time': int(generator_elapsed_time),
        'chosen_run_time': chosen_run_time,
        'chosen_run_time_label': chosen_run_time_label,
        'status': generator_status
    })

# ------------------------------------------------------------------------------
# Evaporate
# ------------------------------------------------------------------------------
@app.route('/evaporate', methods=['GET', 'POST'])
def evaporate():
    global evaporate_running, evaporate_paused, evaporate_start_time, evaporate_elapsed_time
    global evaporate_total_working_hours, evaporate_temperature, evaporate_status

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            if not evaporate_running:
                evaporate_running = True
                evaporate_paused = False
                evaporate_status = "Started"
                evaporate_start_time = time.time() - evaporate_elapsed_time
            elif evaporate_paused:
                evaporate_paused = False
                evaporate_status = "Started"

        elif action == 'pause':
            if evaporate_running and not evaporate_paused:
                evaporate_paused = True
                evaporate_status = "Paused"

        elif action == 'stop':
            if evaporate_running:
                evaporate_total_working_hours += evaporate_elapsed_time / 3600.0
                evaporate_running = False
                evaporate_paused = False
                evaporate_status = "Idle"
                evaporate_elapsed_time = 0

        # Temperature is "UnAvailable"

    return render_template('evaporate.html',
                           elapsed_time=int(evaporate_elapsed_time),
                           total_hours=round(evaporate_total_working_hours, 2),
                           temperature=evaporate_temperature,
                           status=evaporate_status)

@app.route('/evaporate_status')
def evaporate_status_api():
    global evaporate_elapsed_time, evaporate_status
    return jsonify({
        'elapsed_time': int(evaporate_elapsed_time),
        'status': evaporate_status
    })

# ------------------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------------------
@app.route('/settings')
def settings():
    global generator_total_working_hours, evaporate_total_working_hours
    total_generator_hours = round(generator_total_working_hours, 2)
    total_evaporate_hours = round(evaporate_total_working_hours, 2)
    return render_template('settings.html',
                           generator_hours=total_generator_hours,
                           evaporate_hours=total_evaporate_hours)

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
