import os
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

TMDB_API_KEY = os.environ.get("API_KEY")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    if request.method == "POST":
        movie_name = request.form.get("movie")
        return redirect(url_for("find_movie", title=movie_name))
    return render_template("add.html")


@app.route("/find")
def find_movie():
    title = request.args.get("title")

    if not TMDB_API_KEY:
        return "TMDB API key not configured", 500

    response = requests.get(
        TMDB_SEARCH_URL,
        params={
            "api_key": TMDB_API_KEY,
            "query": title
        }
    )

    response.raise_for_status()
    results = response.json().get("results", [])

    movies = []

    for data in results:
        release_date = data.get("release_date") or ""
        year = None

        if release_date:
            try:
                year = int(release_date.split("-")[0])
            except ValueError:
                year = None

        movies.append({
            "id": data.get("id"),
            "title": data.get("title"),
            "year": year,
            "overview": data.get("overview"),
            "poster": (
                f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
                if data.get("poster_path") else None
            )
        })

    return render_template("select.html", movies=movies)


if __name__ == "__main__":
    app.run(debug=True)
