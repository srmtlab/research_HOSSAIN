import streamlit as st
import json
import requests
import os
import numpy as np
import pandas as pd
import plotly.express as px

# Backend API URL
BACKEND_URL = "http://127.0.0.1:5000/detect_stress"

# File to store stress history
STRESS_HISTORY_FILE = "data/stress_history.json"

# Function to load stress history
def load_stress_history():
    try:
        with open(STRESS_HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Streamlit UI
st.title("🎤 Speech Stress Detection System")

# File Upload Section
st.subheader("📂 Upload an Audio File")
uploaded_file = st.file_uploader("Upload your speech recording", type=["mp3", "wav", "m4a"])

# Ensure directory exists for storing uploaded audio
audio_dir = "data"
os.makedirs(audio_dir, exist_ok=True)

# Define file path for storing the uploaded audio file
file_path = os.path.join(audio_dir, "latest_audio.mp3")

# Save and play uploaded file
if uploaded_file is not None:
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if os.path.exists(file_path):
            st.markdown("🎵 **Audio Playback:**")
            with open(file_path, "rb") as audio:
                audio_bytes = audio.read()
            st.audio(audio_bytes)
        else:
            st.error("⚠️ Error: Audio file not found. Please try uploading again.")

    except Exception as e:
        st.error(f"❌ Audio processing error: {str(e)}")

    # Show loading spinner
    with st.spinner("🔄 Analyzing speech stress... Please wait."):
        files = {"audio_file": open(file_path, "rb")}
        response = requests.post(BACKEND_URL, files=files)

    if response.status_code == 200:
        result = response.json()
        detected_stress_level = result["stress_level"]
        transcript = result["transcript"]
        stress_text = result["stress_text"]

        # Stress Level UI with improved visibility
        stress_color_map = {
            1: "#66cc66", 2: "#99cc66", 3: "#ffff99",
            4: "#ffcc00", 5: "#ff9900", 6: "#ff3300", 7: "#cc0000"
        }
        stress_color = stress_color_map.get(detected_stress_level, "#cccccc")
        text_color = "black" if detected_stress_level <= 3 else "white"
        stress_icon = "🟢" if detected_stress_level <= 3 else "🟠" if detected_stress_level == 4 else "🔴"
        stress_message = f"{stress_icon} **Detected Stress Level:** {stress_text} (Level {detected_stress_level})"

        st.markdown(f"""
            <div style="
                padding: 15px;
                border-radius: 10px;
                background-color: {stress_color};
                font-weight: bold;
                font-size: 20px;
                color: {text_color};
                text-align: center;
                border: 2px solid black;
                box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.2);
            ">
                {stress_message}
            </div>
        """, unsafe_allow_html=True)

        # Transcript
        st.subheader("📝 Transcript")
        st.write(f"🗣 **{transcript}**")

        # Save detected stress level
        stress_history = load_stress_history()
        stress_history.append(detected_stress_level)
        with open(STRESS_HISTORY_FILE, "w") as f:
            json.dump(stress_history[-50:], f)  # Keep last 50 entries
    else:
        st.error("❌ Error processing the audio file. Please try again.")

# Stress Trends Visualization
st.subheader("📈 Stress Trends Over Time")
stress_history = load_stress_history()

if len(stress_history) > 1:
    session_numbers = list(range(1, len(stress_history) + 1))
    
    # Step 1: Interactive Time Range Selection
    time_range = st.slider("⏳ Select Time Range", min_value=1, max_value=len(session_numbers), value=(1, len(session_numbers)))
    filtered_sessions = session_numbers[time_range[0]-1:time_range[1]]
    filtered_stress = stress_history[time_range[0]-1:time_range[1]]
    
    # Step 2: Moving Average Trend Analysis
    df = pd.DataFrame({"Session": filtered_sessions, "Stress Level": filtered_stress})
    df["Moving Average"] = df["Stress Level"].rolling(window=5, min_periods=1).mean()
    
    # Step 3: Stress Level Breakdown (Pie Chart) with labels
    color_map = {3: "#66cc66", 5: "#ff9900", 6: "#cc0000"}  # Adjust colors
    fig_pie = px.pie(df, names="Stress Level", title="🔹 Stress Level Distribution", color="Stress Level", color_discrete_map=color_map)
    fig_pie.update_layout(
        annotations=[dict(
            text="🟢 Low (1-3) | 🟠 Mild (4-5) | 🔴 High (6-7)",
            x=0.5, y=-0.2, showarrow=False, font_size=14
        )]
    )
    st.plotly_chart(fig_pie)
    
    # Step 4: Data Export & Report Generation
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Stress Report", csv, "stress_report.csv", "text/csv")
    
    # Interactive Plotly Scatter Plot with trend line
    fig = px.scatter(df, x="Session", y="Stress Level", color="Stress Level", title="📊 Stress Level Over Time",
                     color_discrete_map=color_map, labels={"Session": "📅 Time (Sessions)", "Stress Level": "⚡ Stress Level (1-7)"})
    fig.add_scatter(x=df["Session"], y=df["Moving Average"], mode='lines', name='Stress Trend', line=dict(color='blue', width=2))
    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=2)))
    fig.update_layout(
        font=dict(size=14, color='black'),
        yaxis=dict(range=[1, 7], title="Stress Level (1-7)", showgrid=True, tickfont=dict(size=14)),
        xaxis=dict(title="Time (Sessions)", showgrid=True, tickfont=dict(size=14), range=[1, len(session_numbers)]),
        annotations=[dict(
            text="📉 Trend Line Explanation: The blue line represents the overall trend of stress levels, smoothing fluctuations over time.",
            x=0.5, y=-0.2, showarrow=False, font_size=14
        )]
    )
    st.plotly_chart(fig)
else:
    st.info("📉 Not enough data to display trends yet. Try analyzing more speech samples.")

# streamlit run frontend/main.py
