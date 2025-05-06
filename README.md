# FaceMash

Flask-based app where users vote who’s “hotter” between two images, using Elo ratings and a tournament bracket.

## Features

- Voting between random pairs of images (players)
- Elo rating updates after each vote
- SQLite database for storing players, votes, and logs
- Auto-initializes players from the `static/playerimages` folder
- Tournament bracket with stages (Round of 16, Quarterfinals, Semis, Final)
- Responsive UI (not perfect on mobile)

## 📦 Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/facemash-clone.git
cd facemash-clone
```

2. Install dependencies:

```bash
pip install flask
```

3. Make sure you have a `static/playerimages` folder with `.webp` images.

4. Run the server:

```bash
python main.py
```

## How It Works

- On first run, it creates `players`, `users`, and `logs` tables in `facemash.db`
- Loads images from `static/playerimages`, each becomes a player with an initial Elo rating of 400
- Homepage randomly picks two players to vote on
- After voting, Elo ratings update and a log is saved

## 🗂 Project Structure

```
├── main.py
├── facemash.db
├── bracket_data.py
├── static/
│   ├── playerimages/
│   ├── uploads/
│   ├── css/
│   └── images/
├── templates/
│   ├── layout.html
│   ├── index.html
│   └── table.html
```

## Dependencies

- Python 3.x
- Flask
- SQLite3
- Jinja2 (included with Flask)

## Notes

- Mobile upload isn't perfect — contributions welcome!
- Basic design focused on core functionality
