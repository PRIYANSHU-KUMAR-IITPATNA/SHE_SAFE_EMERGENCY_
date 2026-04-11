from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from dotenv import load_dotenv
from twilio.rest import Client
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'yoursecretkey'

# ------------------ TWILIO CONFIG ------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ------------------ USER DATABASE ------------------
def load_users():
    try:
        with open('users.json', 'r') as file:
            return json.load(file)
    except:
        return {}

def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)

# ---------------- JOB DATABASE ----------------

def load_jobs():
    if not os.path.exists("jobs.json"):
        return {"jobs": []}
    
    with open("jobs.json", "r") as f:
        return json.load(f)


def save_jobs(data):
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=4)
# ------------------ ALERT DATABASE ------------------
def load_alerts():
    try:
        with open("alerts.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_alerts(alerts):
    with open("alerts.json", "w") as f:
        json.dump(alerts, f, indent=4)

# ------------------ ROUTES ------------------

@app.route('/')
def home():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template('index.html')
# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]["password"] == password:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return "❌ Invalid Username or Password"

    return render_template('login.html')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['POST'])
def register():
    users = load_users()
    username = request.form['username']
    password = request.form['password']

    if username in users:
        return "❌ User already exists"

    users[username] = {"password": password}
    save_users(users)

    return redirect(url_for('login'))

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ---------------- PAGES ----------------
@app.route('/product')
def product():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template('product.html')

@app.route('/solutions')
def solutions():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template('solutions.html')

@app.route('/community')
def community():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template('community.html')

@app.route('/resources')
def resources():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template('resources.html')

@app.route('/contact')
def contact():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/buddy')
def buddy():
    return render_template('buddy.html')

from datetime import datetime, timedelta

@app.route('/jobs')
def jobs():
    jobs = load_jobs()

    applied = False

    if 'applied_date' in session:
        applied_date = datetime.strptime(session['applied_date'], "%Y-%m-%d")
        if datetime.now() - applied_date < timedelta(days=30):
            applied = True
        else:
            session.pop('applied_date')  # reset after 30 days

    return render_template('jobs.html', jobs=jobs, applied=applied)

@app.route('/apply/<int:job_id>')
def apply(job_id):
    jobs = load_jobs()

    selected_job = None
    for job in jobs['jobs']:
        if job['id'] == job_id:
            selected_job = job
            break

    if not selected_job:
        return "Job not found"

    session['applied_date'] = datetime.now().strftime("%Y-%m-%d")
    session['applied_success'] = True

    return redirect(selected_job['apply_link'])

@app.route('/test_jobs')
def test_jobs():
    data = load_jobs()
    return data
# ------------------ TWILIO SOS ------------------
@app.route('/twilio', methods=['GET', 'POST'])
def twilio_page():
    if not session.get("user"):
        return redirect(url_for('login'))

    if request.method == 'POST':
        phone = request.form.get("user_number")
        lat = request.form.get("latitude")
        lon = request.form.get("longitude")
        username = session.get("user")

        location_link = f"https://maps.google.com/?q={lat},{lon}"
        sms_body = f"🚨 EMERGENCY ALERT!\nUser: {username}\nLive Location:\n{location_link}"

        try:
            # Send SMS
            client.messages.create(
                body=sms_body,
                from_=TWILIO_PHONE_NUMBER,
                to=phone
            )

            # Call
            client.calls.create(
                twiml=f"<Response><Say>Emergency alert from SheSafe. User {username} is in danger. Please check SMS.</Say></Response>",
                from_=TWILIO_PHONE_NUMBER,
                to=phone
            )

            # Save alert to alerts.json
            alerts = load_alerts()
            alerts.append({
                "user": username,
                "phone": phone,
                "latitude": lat,
                "longitude": lon,
                "location": location_link,
                "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            })
            save_alerts(alerts)

            return "🚨 Alert Sent & Logged Successfully!"

        except Exception as e:
            return str(e)

    return render_template('twilio.html')

# ------------------ ALERT DASHBOARD ------------------
@app.route('/alerts')
def alerts():
    if not session.get("user"):
        return redirect(url_for('login'))

    data = load_alerts()
    return render_template("alerts.html", alerts=data)
    
@app.route('/file_case')
def file_case():
    return render_template('file_case.html')

@app.route('/food_store')
def food_store():
    return render_template('food_store.html')


@app.route('/healthcare')
def healthcare():
    return render_template('healthcare.html')

@app.route('/eduvid')
def eduvid():
    return render_template('eduvid.html')
# ------------------------------------Profile --------------------------------------------
@app.route('/profile')
def profile():
    if not session.get("user"):
        return redirect(url_for("login"))

    users = load_users()
    username = session.get("user")

    user_data = users.get(username, {})

    return render_template("profile.html", user=user_data)
    # Load users.json
    import json
    with open("users.json") as f:
        users = json.load(f)

    user_data = users.get(username, {})

    return render_template("profile.html", user=user_data)
# ------------------ SCHEME EXPLORER ------------------
@app.route('/explore', methods=['GET', 'POST'])
def explore():
    eligible = []

    with open('schemes.json', encoding='utf-8') as f:
        schemes = json.load(f)

    if request.method == 'POST':
        age = int(request.form['age'])
        income = int(request.form['income'])
        gender = request.form['gender']
        state = request.form['state']
        marital_status = request.form['marital_status']
        education_level = request.form['education_level']
        religion = request.form.get('religion', '').strip()
        pregnant = request.form.get('pregnant') == 'yes'

        for scheme in schemes:
            if scheme["state"] != ["All"] and state not in scheme["state"]:
                continue
            if "gender" in scheme and scheme["gender"] != gender:
                continue
            if "min_age" in scheme and age < scheme["min_age"]:
                continue
            if "max_age" in scheme and age > scheme["max_age"]:
                continue
            if "income_limit" in scheme and income > scheme["income_limit"]:
                continue
            if "marital_status" in scheme and scheme["marital_status"] != "any" and scheme["marital_status"] != marital_status:
                continue
            if "education_level" in scheme and scheme["education_level"] != "any" and scheme["education_level"] != education_level:
                continue
            if "pregnant_required" in scheme and scheme["pregnant_required"] and not pregnant:
                continue
            if "religion" in scheme and scheme["religion"] != "any" and scheme["religion"].lower() != religion.lower():
                continue

            eligible.append(scheme)

    return render_template('explore.html', eligible=eligible)


# ------------------ RUN SERVER ------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

