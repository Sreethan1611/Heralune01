
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# Optional route (if you're using a form on index.html)
@app.route("/analyze", methods=["POST"])
def analyze():
    journal_entry = request.form["entry"]
    return render_template("result.html", result=journal_entry)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=81)
