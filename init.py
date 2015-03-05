from flask import Flask, make_response, request, current_app, render_template, session, redirect, url_for, escape

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug = True)