import os
from datetime import datetime
from io import BytesIO
import requests
from flask import Flask, make_response, render_template, request, send_file
from flask.helpers import make_response
from flask import Flask, request, Response

app = Flask(__name__)
api_key = os.getenv("GROQ_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route('/reupload', methods=['POST'])
def reupload():
    file = request.files.get('file')
    if file:
        content = file.read().decode('utf-8') 
        result = f"File has {len(content)} characters." 
        return render_template('index.html', result=result)
    else:
        return render_template('index.html', result="No file uploaded.")

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

@app.route("/redo", methods=["GET"])
def redo():
    return render_template("redo_upload.html")

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

@app.route("/update", methods=["POST"])
def update_journal():
    uploaded_file = request.files.get("uploaded_file")
    new_entry = request.form.get("journal_entry", "").strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not uploaded_file or not uploaded_file.filename or not uploaded_file.filename.endswith(".txt"):
        return "Please upload a valid .txt file."

    try:
        previous_content = uploaded_file.read().decode("utf-8")
    except Exception as e:
        return f"Error reading uploaded file: {e}"
    updated_content = f"{previous_content.strip()}\n\n[{timestamp}]\n{new_entry.strip()}"
    output_filename = f"heralune_updated_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return Response(
        updated_content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={output_filename}"}
    )

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
