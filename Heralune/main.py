import os
import random
from datetime import datetime, timezone
from io import BytesIO

import requests
from flask import (
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(24)

api_key = os.getenv("GROQ_API_KEY")

def get_heralune_insight(journal_text):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a supportive emotional assistant. A user is journaling their thoughts. "
                    "Don't ask for a second entry. Respond with empathy, encouragement, and gentle "
                    "reflection. Avoid judgment or medical advice. If appropriate, suggest simple "
                    "techniques for self-awareness or comfort."
                )
            },
            {"role": "user", "content": journal_text}
        ],
        "temperature": 0.7
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    data = response.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")

def get_random_bg():
    return random.choice(["ms1.jpg", "ms2.jpg", "ms3.jpg", "ms4.jpg"])

@app.before_request
def ensure_bg():
    if "bg" not in session:
        session["bg"] = get_random_bg()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        journal = request.form.get("journal", "").strip()
        if not journal:
            return "Please enter a journal entry."
        session["journal"] = journal
        # Store the insight in 'result'
        session["result"] = get_heralune_insight(journal)
        return redirect(url_for("redo"))
    return render_template("index.html", bg=session["bg"])

@app.route("/analyze", methods=["POST"])
def analyze():
    journal_box = request.form.get("entry", "").strip()
    radmood = request.form.get("mood", "").strip()
    custom_mood = request.form.get("customMood", "").strip()
    mood = custom_mood or radmood
    if not journal_box or not mood:
        return "Missing journal or mood."

    result = get_heralune_insight(journal_box)
    return render_template(
        "result.html",
        journal_box=journal_box,
        mood=mood,
        bg=session["bg"]
    )

@app.route("/reanalyze", methods=["POST"])
def reanalyze():
    journal_box = request.form.get("journal_box", "")
    mood = request.form.get("mood", "")
    return render_template(
        "update.html",
        journal_box=journal_box,
        mood=mood,
        bg=session["bg"]
    )

@app.route("/redo", methods=["GET"])
def redo():
    journal = session.get("journal", "")
    result = session.get("result", "")
    return render_template(
        "redo.html",
        journal=journal,
        result=result,
        bg=session["bg"]
    )

@app.route("/reanalyze_result", methods=["POST"])
def reanalyze_result():
    previous_journal = request.form.get("journal_box", "")
    added_text = request.form.get("additional_entry", "").strip()
    mood = request.form.get("mood", "")
    combined_journal = previous_journal + ("\n\n" + added_text if added_text else "")
    result = get_heralune_insight(combined_journal)
    return render_template(
        "result.html",
        result=result,
        journal_box=combined_journal,
        mood=mood,
        bg=session["bg"]
    )

@app.route("/update", methods=["POST"])
def update_journal():
    uploaded_file = request.files.get("file")
    journal_entry = request.form.get("journal", "").strip()
    # Changed the variable name from 'insight' to 'result'
    result = request.form.get("insight", "").strip()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if not uploaded_file or not uploaded_file.filename or not uploaded_file.filename.endswith(".txt"):
        return "Please upload a valid .txt file."
    try:
        previous_content = uploaded_file.read().decode("utf-8")
    except Exception as e:
        return f"Error reading uploaded file: {e}"

    metadata = f"--- Appended Entry ---\nUpload Timestamp: {timestamp}"
    new_content = (
        f"\n\n{metadata}\nJournal Entry:\n{journal_entry}\n\nHeralune's Insight:\n{result}\n"
    )
    updated_content = f"{previous_content.strip()}{new_content}"

    output_file = BytesIO()
    output_file.write(updated_content.encode("utf-8"))
    output_file.seek(0)
    filename = f"heralune_updated_journal_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M:%S')}.txt"
    return send_file(
        output_file,
        as_attachment=True,
        download_name=filename,
        mimetype="text/plain"
    )

@app.route("/download", methods=["POST"])
def download():
    journal = request.form.get("journal_box", "")
    mood = request.form.get("mood", "")
    insight = request.form.get("result", "")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    content = (
        f"Heralune Journal Entry\nTimestamp: {timestamp}\nMood: {mood}\n\n"
        f"Journal:\n{journal}\n\nHeralune’s Insight:\n{insight}"
    )

    response = make_response(content)
    response.headers["Content-Disposition"] = "attachment; filename=heralune_journal.txt"
    response.headers["Content-Type"] = "text/plain"
    return response

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
