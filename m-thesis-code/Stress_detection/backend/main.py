import os
import json
import openai
import whisper
from flask import Flask, request, jsonify
from whisper import load_model

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY", "61FgJ")  # key

# Flask app initialization
app = Flask(__name__)

# File to store stress history
STRESS_HISTORY_FILE = "data/stress_history.json"

# Ensure the `data` directory exists
os.makedirs("data", exist_ok=True)

# Function to load stress history
def load_stress_history():
    if os.path.exists(STRESS_HISTORY_FILE):
        with open(STRESS_HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

# Function to save stress history
def save_stress_history(stress_levels):
    with open(STRESS_HISTORY_FILE, "w") as f:
        json.dump(stress_levels[-50:], f)  # Keep only last 50 records

# Function to process speech and detect stress
def detect_stress_from_audio(audio_file_path):
    try:
        # Load Whisper model
        model = load_model("base")
        # Transcribe the audio file
        result = model.transcribe(audio_file_path)
        transcript = result["text"]

        # OpenAI API for stress analysis
        client = openai.OpenAI(api_key=openai.api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Analyze the stress level in this speech."},
                {"role": "user", "content": transcript}
            ]
        )

        # Extract stress level
        stress_level_text = response.choices[0].message.content

        # Map detected stress level to numeric scale
        stress_mapping = {
            "Low (Relaxed)": 1,
            "Mild (Slight Stress)": 2,
            "Moderate": 3,
            "High (Overload)": 4,
            "Very High": 5,
            "Extreme": 6,
            "Critical": 7
        }

        detected_stress_level = None
        for key, value in stress_mapping.items():
            if key.lower() in stress_level_text.lower():
                detected_stress_level = value
                break

        # Default to Moderate if no match found
        if detected_stress_level is None:
            detected_stress_level = 3

        return detected_stress_level, transcript, stress_level_text
    except Exception as e:
        print(f"Error in stress detection: {e}")
        return None, None, None

# Flask route to process audio file
@app.route("/detect_stress", methods=["POST"])
def detect_stress():
    try:
        # Get uploaded file
        audio_file = request.files["audio_file"]
        file_path = "data/latest_audio.mp3"
        audio_file.save(file_path)

        # Process audio file
        detected_stress_level, transcript, stress_text = detect_stress_from_audio(file_path)

        if detected_stress_level is None:
            return jsonify({"error": "Failed to process audio"}), 400

        # Save stress level to history
        stress_history = load_stress_history()
        stress_history.append(detected_stress_level)
        save_stress_history(stress_history)

        # Return response
        return jsonify({
            "stress_level": detected_stress_level,
            "transcript": transcript,
            "stress_text": stress_text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
    # streamlit run frontend/main.py
# python backend/main.py
