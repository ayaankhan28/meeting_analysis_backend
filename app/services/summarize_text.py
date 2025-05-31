from backend.app.config import OPENAI_API_KEY
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
def summarize_text(transcription):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": "Summarize the following text and extract key points: keep the summary under 100 words"},
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    summary = completion.choices[0].message.content
    key_points = summary.split("\n")

    return  summary, key_points


