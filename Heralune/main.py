from flask import Flask, request, render_template
import requests
import os

app = Flask(__name__)
api_key = os.getenv("GROQ_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    journal_box = request.form.get("entry")  # Get the form data

    if not journal_box:
        return "No journal entry provided."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a supportive emotional assistant. A user is journaling their thoughts. Don't ask for a second entry."
                    "Respond with empathy, encouragement, and gentle reflection. Avoid judgment or medical advice. "
                    "If appropriate, suggest simple techniques for self-awareness or comfort."
                )
            },
            {
                "role": "user",
                "content": journal_box
            }
        ],
        "temperature": 0.7
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data
    )

    result = response.json()["choices"][0]["message"]["content"]
    return render_template("result.html", result=result, journal_box=journal_box)

if __name__ == "__main__":
    app.run(debug=True, port=81)
