from flask import Flask

app = Flask(__name__)


@app.route("/myjoke", methods=["GET"])
def mymethod():
    return "Why did the chicken cross the street? Ha! ha, ha!"


if __name__ == "__main__":
    app.run(debug=True)
