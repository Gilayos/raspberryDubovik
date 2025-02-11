# app.py
import random
import time
import threading

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Global states
generator_running = False
generator_paused = False
generator_start_time = 0
generator_elapsed_time = 0
generator_total_working_hours = 0.0  # in hours
generator_power = 50
generator_temperature = 25  # just a dummy value
generator_status = "Idle"

# For start-time options
GENERATOR_TIME_OPTIONS = {
    "4cyl_under_250k": 60 * 60,       # 1 hour in seconds
    "over_4cyl_or_over_250k": 60 * 90,# 1.5 hours
    "over_4cyl_and_over_250k": 60 * 120, # 2 hours
    "manual": 0                       # manual run
}

chosen_run_time = 0

evaporate_running = False
evaporate_paused = False
evaporate_start_time = 0
evaporate_elapsed_time = 0
evaporate_total_working_hours = 0.0
evaporate_temperature = 25
evaporate_status = "Idle"

# ------------------------------------------------------------------------------
# Helper function to update elapsed times for generator & evaporator 
# in background, so the UI updates in near-real time
# ------------------------------------------------------------------------------
def update_elapsed_times():
    global generator_running, generator_paused, generator_start_time, generator_elapsed_time
    global evaporate_running, evaporate_paused, evaporate_start_time, evaporate_elapsed_time

    while True:
        time.sleep(1)  # update every second

        # Update generator time
        if generator_running and not generator_paused:
            generator_elapsed_time = time.time() - generator_start_time
        
        # Update evaporate time
        if evaporate_running and not evaporate_paused:
            evaporate_elapsed_time = time.time() - evaporate_start_time

# Start background thread
threading.Thread(target=update_elapsed_times, daemon=True).start()

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.route('/')
def index():
    """Main page with the three buttons."""
    return render_template('index.html')

# ------------------------------------------------------------------------------
@app.route('/generator', methods=['GET', 'POST'])
def generator():
    """
    גנרטור Page:
    - Displays elapsed time
    - Start/Stop/Pause
    - Power (50%/100%)
    - Temperature
    - Running Status
    - 4 start-time options
    """
    global generator_running, generator_paused, generator_start_time, generator_elapsed_time
    global generator_total_working_hours, generator_power, generator_temperature
    global generator_status, chosen_run_time

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'choose_time_option':
            chosen_option = request.form.get('time_option')
            chosen_run_time = GENERATOR_TIME_OPTIONS[chosen_option]

        elif action == 'start':
            # If not currently running, start the clock
            if not generator_running:
                generator_running = True
                generator_paused = False
                generator_status = "Started"
                generator_start_time = time.time() - generator_elapsed_time
                
                # [Demo] "Toggle pins"
                print(f"[Generator] Start pressed. Setting GPIO pins ON randomly. Value={random.randint(0,1)}")

            # If was paused, unpause
            elif generator_paused:
                generator_paused = False
                generator_status = "Started"
                print(f"[Generator] Resume pressed. Setting GPIO pins randomly. Value={random.randint(0,1)}")

        elif action == 'pause':
            if generator_running and not generator_paused:
                generator_paused = True
                generator_status = "Paused"
                print(f"[Generator] Pause pressed. Setting GPIO pins OFF randomly. Value={random.randint(0,1)}")

        elif action == 'stop':
            if generator_running:
                # Update total working hours
                # Convert seconds to hours
                generator_total_working_hours += generator_elapsed_time / 3600.0
                generator_running = False
                generator_paused = False
                generator_status = "Idle"
                
                # Reset elapsed time or keep it zeroed
                generator_elapsed_time = 0
                chosen_run_time = 0

                print(f"[Generator] Stop pressed. Setting GPIO pins OFF. Value={random.randint(0,1)}")

        elif action == 'change_power':
            generator_power = 100 if generator_power == 50 else 50

        # Update temperature indicator randomly for demonstration
        generator_temperature = random.randint(25, 90)

    # Handle auto-stop if chosen_run_time reached
    if chosen_run_time > 0 and generator_elapsed_time >= chosen_run_time:
        # Stop automatically
        generator_total_working_hours += chosen_run_time / 3600.0
        generator_running = False
        generator_paused = False
        generator_status = "Idle"
        generator_elapsed_time = 0
        chosen_run_time = 0

        print("[Generator] Auto-stopped after chosen run time.")

    return render_template('generator.html',
                           elapsed_time=int(generator_elapsed_time),
                           total_hours=round(generator_total_working_hours, 2),
                           power=generator_power,
                           temperature=generator_temperature,
                           status=generator_status,
                           chosen_run_time=int(chosen_run_time))

# ------------------------------------------------------------------------------
@app.route('/evaporate', methods=['GET', 'POST'])
def evaporate():
    """
    אידוי Page:
    - Displays elapsed time
    - Start/Stop/Pause
    - Temperature
    - Running Status
    """
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
                
                # [Demo] "Toggle pins"
                print(f"[Evaporate] Start pressed. Setting GPIO pins ON randomly. Value={random.randint(0,1)}")

            elif evaporate_paused:
                evaporate_paused = False
                evaporate_status = "Started"
                print(f"[Evaporate] Resume pressed. Setting GPIO pins randomly. Value={random.randint(0,1)}")

        elif action == 'pause':
            if evaporate_running and not evaporate_paused:
                evaporate_paused = True
                evaporate_status = "Paused"
                print(f"[Evaporate] Pause pressed. GPIO pins OFF randomly. Value={random.randint(0,1)}")

        elif action == 'stop':
            if evaporate_running:
                evaporate_total_working_hours += evaporate_elapsed_time / 3600.0
                evaporate_running = False
                evaporate_paused = False
                evaporate_status = "Idle"
                evaporate_elapsed_time = 0

                print(f"[Evaporate] Stop pressed. Setting GPIO pins OFF. Value={random.randint(0,1)}")

        # Update temperature randomly for demonstration
        evaporate_temperature = random.randint(25, 90)

    return render_template('evaporate.html',
                           elapsed_time=int(evaporate_elapsed_time),
                           total_hours=round(evaporate_total_working_hours, 2),
                           temperature=evaporate_temperature,
                           status=evaporate_status)

# ------------------------------------------------------------------------------
@app.route('/settings')
def settings():
    """Settings Page: show total working hours for both generator and evaporation."""
    global generator_total_working_hours, evaporate_total_working_hours
    total_generator_hours = round(generator_total_working_hours, 2)
    total_evaporate_hours = round(evaporate_total_working_hours, 2)
    return render_template('settings.html',
                           generator_hours=total_generator_hours,
                           evaporate_hours=total_evaporate_hours)

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run in debug for local testing. 
    # On production or after stable, set debug=False or use a production server like gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)
