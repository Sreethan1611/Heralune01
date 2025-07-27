import os
from datetime import datetime
from io import BytesIO
import requests
from flask import (
    Flask,
    gunicorn,
    make_response,
    Response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

api_key = os.getenv("GROQ_API_KEY")


def get_heralune_insight(journal_text):
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
            {"role": "user", "content": journal_text}
        ],
        "temperature": 0.7
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data
    )

    return response.json()["choices"][0]["message"]["content"]


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        journal = request.form['journal']
        heralune_insight = get_heralune_insight(journal)
        session['journal'] = journal
        session['insight'] = heralune_insight
        return redirect(url_for('redo'))
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    journal_box = request.form.get("entry")
    mood = request.form.get("mood")

    if not journal_box or not mood:
        return "Missing journal or mood."

    result = get_heralune_insight(journal_box)
    return render_template("result.html", result=result, journal_box=journal_box, mood=mood)


@app.route('/reanalyze', methods=['POST'])
def reanalyze():
    journal_box = request.form.get("journal_box", "")
    mood = request.form.get("mood", "")
    return render_template("update.html", journal_box=journal_box, mood=mood)

@app.route('/redo', methods=['POST'])
def redo():
    journal = request.form.get("journal", "")
    insight = request.form.get("insight", "")
    return render_template("redo.html", journal=journal, insight=insight)

@app.route('/reanalyze_result', methods=['POST'])
def reanalyze_result():
    previous_journal = request.form.get("journal_box", "")
    added_text = request.form.get("additional_entry", "")
    mood = request.form.get("mood", "")
    combined_journal = previous_journal + "\n\n" + added_text.strip()
    result = get_heralune_insight(combined_journal)
    return render_template("result.html", result=result, journal_box=combined_journal, mood=mood)

    from datetime import datetime

@app.route('/update', methods=['POST'])
def update_journal():
        uploaded_file = request.files.get("file")
        journal_entry = request.form.get("journal", "").strip()
        insight = request.form.get("insight", "").strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = f"--- Appended Entry ---\nUpload Timestamp: {timestamp}"
        if not uploaded_file or not uploaded_file.filename or not uploaded_file.filename.endswith(".txt"):
            return "Please upload a valid .txt file."
        try:
            previous_content = uploaded_file.read().decode("utf-8")
        except Exception as e:
            return f"Error reading uploaded file: {e}"
        new_content = (
            f"\n\n{metadata}\nJournal Entry:\n{journal_entry}\n\nHeralune's Insight:\n{insight}\n"
        )
        updated_content = f"{previous_content.strip()}{new_content}"
        output_file = BytesIO()
        output_file.write(updated_content.encode("utf-8"))
        output_file.seek(0)
        filename = f"heralune_updated_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return send_file(output_file,
                         as_attachment=True,
                         download_name=filename,
                         mimetype='text/plain')

@app.route('/upload', methods=['POST'])
def upload():
    journal = request.form['journal']
    insight = request.form.get("insight", "")
    uploaded_file = request.files.get('file')

    old_content = ""
    if uploaded_file and uploaded_file.filename:
        old_content = uploaded_file.read().decode("utf-8")
    new_entry = f"\n\n---\nJournal Entry:\n{journal}\n\nHeralune's Insight:\n{insight}"
    combined_content = old_content + new_entry

    output_file = BytesIO()
    output_file.write(combined_content.encode("utf-8"))
    output_file.seek(0)
    filename = f"heralune_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    return send_file(output_file,
                     as_attachment=True,
                     download_name=filename,
                     mimetype='text/plain')

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
