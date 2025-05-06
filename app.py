from flask import Flask, render_template, request, redirect, flash, session, url_for, make_response
from werkzeug.utils import secure_filename
import random
import sqlite3
import os
import uuid


from bracket_data import (
    round_16_right, round_16_left, round_8_left,
    round_8_right, quarter_finals_left, quarter_finals_right,
    semi_finals_left, semi_finals_right, final
)

app = Flask(__name__)

DATA_FILE = "facemash.db"
IMAGE_FOLDER = "static/playerimages"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

app.secret_key = os.urandom(24)  # THE KEY
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# DB functions players
def players():
    connection = sqlite3.connect(DATA_FILE)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            elo REAL,
            path TEXT,
            votes INTEGER
        );""")
    connection.commit()
    connection.close()

def users():
    connection = sqlite3.connect(DATA_FILE)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            votes INTEGER
        );""")
    connection.commit()
    connection.close()

def logs():
    connection = sqlite3.connect(DATA_FILE)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            user_id INTEGER NOT NULL,
            winner_id INTEGER NOT NULL,
            loser_id INTEGER NOT NULL,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
            FOREIGN KEY(winner_id) REFERENCES players(player_id)
            FOREIGN KEY(loser_id) REFERENCES players(player_id)
        );""")
    connection.commit()
    connection.close()

if not os.path.exists(DATA_FILE):
    exit("DB doesn't exist")

players()
users()
logs()

connection = sqlite3.connect(DATA_FILE)
cursor = connection.cursor()


image_files = [f for f in os.listdir(IMAGE_FOLDER) if os.path.isfile(os.path.join(IMAGE_FOLDER, f))]
UserFilenames = [os.path.splitext(i)[0] for i in image_files]

cursor.execute("SELECT NAME FROM players")
results = cursor.fetchall()
DBnames = [row[0] for row in results]


for name in UserFilenames:
    if name not in DBnames:
        path = os.path.join(IMAGE_FOLDER, name + ".webp")
        cursor.execute("""
            INSERT INTO players(name, elo, path, votes)
            VALUES(?, ?, ?, ?)
        """, (name, 400.0, path, 0,))

connection.commit()

# Functions for db work
def load_user_data(ipaddress):
    connection = sqlite3.connect(DATA_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT user_id FROM users WHERE ip_address = ?", (ipaddress,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO USERS (ip_address,votes) VALUES (?,?)", (ipaddress,0,))
        connection.commit()
    
    connection.close()

def load_logs(winner_id, loser_id, ipaddress):
    connection = sqlite3.connect(DATA_FILE)
    cursor = connection.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE ip_address = ?",(ipaddress,))
    answer = cursor.fetchone()
    user_id = answer[0]

    cursor.execute("""INSERT INTO logs(user_id, winner_id, loser_id)
                      VALUES(?, ?, ?)""", (user_id, winner_id, loser_id))
    
    cursor.execute("UPDATE users SET votes = votes + 1 WHERE user_id = ? ",(user_id,))

    #Output to console
    cursor.execute("SELECT NAME FROM players WHERE player_id = ?", (winner_id,))
    winner_name = cursor.fetchone()[0]

    cursor.execute("SELECT NAME FROM players WHERE player_id = ?", (loser_id,))
    loser_name = cursor.fetchone()[0]

    print(f"{ipaddress} has chosen {winner_name} instead of {loser_name}")
    connection.commit()
    connection.close()

def save_data(winner_id, loser_id, winner_elo, loser_elo, winner_votes, loser_votes):
    connection = sqlite3.connect(DATA_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE players
        SET elo = ?, VOTES = ?
        WHERE player_id = ?
    """, (winner_elo, winner_votes, winner_id))

    cursor.execute("""
        UPDATE players
        SET elo = ?, VOTES = ?
        WHERE player_id = ?
    """, (loser_elo, loser_votes, loser_id))

    connection.commit()
    connection.close()

#Back upload to db
cursor.execute("SELECT player_id, name, elo, path, votes FROM players")
results = cursor.fetchall()
users = [{"id": row[0], "name": row[1], "elo": row[2], "image": row[3], "votes": row[4]} for row in results]


def get_random_pair():
    if len(users) < 2:
        return None, None

    weighted_users = sorted(users, key=lambda u: u["elo"], reverse=True)
    pair = random.sample(weighted_users[:max(5, len(users))], 2)

    for user in pair:
        rel_path = os.path.relpath(user["image"], "static")
        rel_path = rel_path.replace("\\", "/")
        user["image"] = url_for("static", filename=rel_path)

    return pair[0], pair[1]

def get_ip():
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR') or \
                 request.environ.get('HTTP_X_REAL_IP') or \
                 request.environ.get('REMOTE_ADDR') or \
                 request.remote_addr
    return ip_address

# MAIN ROUTES 

@app.route("/", methods=["GET","POST"])
def index():
    user1, user2 = get_random_pair()
    ipaddress = get_ip()
    load_user_data(ipaddress)
    print(get_ip())
    return render_template("index.html", user1=user1, user2=user2, dayOfCompetion=1)

@app.route("/table", methods=["GET","POST"])
def table():
    return render_template("table.html",round_16_left=round_16_left,round_16_right=round_16_right,
    round_8_left=round_8_left,round_8_right=round_8_right,
    quarter_finals_left=quarter_finals_left,quarter_finals_right=quarter_finals_right,
    semi_finals_left=semi_finals_left,semi_finals_right=semi_finals_right,
    final=final)

@app.route("/vote", methods=["POST"])
def vote():
    connection = sqlite3.connect(DATA_FILE)
    cursor = connection.cursor()

    winner_id = int(request.form.get("winner"))
    loser_id = int(request.form.get("loser"))

    winner = None
    loser = None 

    cursor.execute("SELECT player_id, NAME, ELO, PATH, VOTES FROM players WHERE player_id = ?", (winner_id,))
    row = cursor.fetchone()
    if row:
        winner = {"id": row[0], "name": row[1], "elo": row[2], "image": row[3], "votes": row[4]}
    
    cursor.execute("SELECT player_id, NAME, ELO, PATH, VOTES FROM players WHERE player_id = ?", (loser_id,))
    row = cursor.fetchone()
    if row:
        loser = {"id": row[0], "name": row[1], "elo": row[2], "image": row[3], "votes": row[4]}

    if not winner or not loser:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    winner["votes"] += 1

    Ra = winner["elo"]
    Rb = loser["elo"]

    Ea = 1 / (1 + 10 ** ((Rb - Ra) / 400))
    Eb = 1 / (1 + 10 ** ((Ra - Rb) / 400))

    K = 32
    
    new_winner_elo = Ra + K * (1 - Ea)
    new_loser_elo = Rb + K * (0 - Eb)
    
    new_winner_elo = max(100, new_winner_elo)
    new_loser_elo = max(100, new_loser_elo)

    save_data(winner_id, loser_id, new_winner_elo, new_loser_elo, winner["votes"], loser["votes"])
    
    ipaddress = get_ip()
    load_logs(winner_id, loser_id, ipaddress)

    connection.close()
    return redirect(request.referrer or url_for('index'))


#Yes I havent add upload button to the Modernindex, but
#it's work not so good whe u use it on phone, so if u really need it,
#U have to code by yourself
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.errorhandler(413)
def handle_file_too_large(error):
    flash('File is to big, Max size is 1 MB.')
    return redirect(request.url)

if __name__ == "__main__":
    app.run(debug=False)


            