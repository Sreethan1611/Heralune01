from os import getenv

import openai
from flask import Flask, request

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():

    if request.method == "POST":
        if journal_box is None:
            return "Error: No journal entry provided.", 400 
        openai.api_key = getenv("OPENAI_API_KEY")
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a supportive emotional assistant. A user is journaling their thoughts. "
                            "Respond with empathy, encouragement, and gentle reflection. Avoid judgment or medical advice. "
                            "If appropriate, suggest simple techniques for self-awareness or comfort."
                        )
                    },
                    {
                        "role": "user",
                        "content": journal_box
                    }
                ],
                temperature=0.7
            )
            feedback = response.choices[0].message.content
            return feedback
        except Exception as e:
            return f"An error occurred: {str(e)}", 500