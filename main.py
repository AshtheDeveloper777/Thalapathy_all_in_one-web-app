from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap5 import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv


TMDB_SEARCH_URL = os.getenv("TMDB_SEARCH_URL")
TMDB_MOVIE_DETAILS_URL = os.getenv("TMDB_MOVIE_DETAILS_URL")
TMDB_IMAGE_BASE_URL = os.getenv("TMDB_IMAGE_BASE_URL")
API_KEY =os.getenv("API_KEY")


app = Flask(__name__)
#app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
print("SECRET_KEY =", app.config["SECRET_KEY"])




Bootstrap(app)
db = SQLAlchemy(app)

# ================= DATABASE MODEL =================
class Movie(db.Model):
    __tablename__ = "movies"
    from sqlalchemy import Text
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer)
    description = db.Column(Text)   # ✅ CHANGE HERE
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(500))



with app.app_context():
    db.create_all()

# ================= FORMS =================
class MovieForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10")
    review = StringField("Your Review")
    submit = SubmitField("Done")

# ================= ROUTES =================
@app.route("/")
def home():
    movies = Movie.query.all()
    movies.sort(key=lambda m: m.rating or 0, reverse=True)

    for i, movie in enumerate(movies):
        movie.ranking = i + 1

    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get_or_404(movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = MovieForm()
    if form.validate_on_submit():
        response = requests.get(
            TMDB_SEARCH_URL,
            params={"api_key": API_KEY, "query": form.title.data},
            timeout=10
        )
        response.raise_for_status()
        return render_template("select.html", options=response.json()["results"])

    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")

    if movie_api_id:
        response = requests.get(
            f"{TMDB_MOVIE_DETAILS_URL}/{movie_api_id}",
            params={"api_key": API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        new_movie = Movie(
            title=data["title"],
            year=int(data["release_date"].split("-")[0]),
            img_url=f"{TMDB_IMAGE_BASE_URL}{data['poster_path']}",
            description=data["overview"]
        )

        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
