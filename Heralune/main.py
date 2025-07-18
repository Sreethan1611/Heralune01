import os
from datetime import datetime

import requests
from flask import Flask, make_response, render_template, request
from flask.helpers import make_response

app = Flask(__name__)
api_key = os.getenv("GROQ_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():   
    journal_box = request.form.get("entry")
    mood = request.form.get("mood")
   
    if not journal_box or not mood:
            return "Missing journal or mood."

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
    return render_template("result.html", result=result, journal_box=journal_box, mood=mood)

@app.route('/reanalyze', methods=['POST'])
def reanalyze():
    journal_box = request.form.get("journal_box", "")
    mood = request.form.get("mood", "")
    return render_template("update.html", journal_box=journal_box, mood=mood)


@app.route('/reanalyze_result', methods=['POST'])
def reanalyze_result():
    previous_journal = request.form.get("journal_box", "")
    added_text = request.form.get("additional_entry", "")
    mood = request.form.get("mood", "")

    combined_journal = previous_journal + "\n\n" + added_text.strip()

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
            {"role": "user", "content": combined_journal}
        ],
        "temperature": 0.7
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    result = response.json()["choices"][0]["message"]["content"]

    return render_template("result.html", result=result, journal_box=combined_journal, mood=mood)


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        uploaded_file = request.files.get("journal_file")
        mood = request.form.get("today_mood")

        if uploaded_file and uploaded_file.filename.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8")
            updated_content = f"{content}\nMood today: {mood}"
            return send_file(io.BytesIO(updated_content.encode()), mimetype="text/plain",
                             as_attachment=True, download_name="updated_journal.txt")
        return "Invalid file format. Please upload a .txt file."
    return render_template("update.html")
    
@app.route("/download", methods=["POST"])
def download():
    journal = request.form.get("journal_box")
    mood = request.form.get("mood")
    insight = request.form.get("result") 

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"Heralune Journal Entry\nTimestamp: {timestamp}\nMood: {mood}\n\nJournal:\n{journal}\n\nHeralune’s Insight:\n{insight}"

    response = make_response(content)
    response.headers["Content-Disposition"] = "attachment; filename=heralune_journal.txt"
    response.headers["Content-Type"] = "text/plain"
    return response

if __name__ == "__main__":
    app.run(debug=True, port=81)
