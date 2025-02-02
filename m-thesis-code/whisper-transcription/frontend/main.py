
import pdfkit
import streamlit as st
import tempfile
from tempfile import NamedTemporaryFile
import re
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from datetime import date
import requests
from datetime import datetime
st.title("Stress Visualization")

current_date = datetime.now()
def clean_text(text):
    # Remove asterisks used for bold or headings
    text = re.sub(r'\*\*+', '', text)
    
    # Replace multiple line breaks with a single one
    text = re.sub(r'\n+', '\n\n', text)
    
    # Ensure proper formatting of sections with bold headings
    text = re.sub(r'(\n\s*[A-Z][a-z]+\s*:\s*)', '\n\n\\1', text)
    
    # Remove extra line breaks around headings and sections
    text = re.sub(r'(\n\s*[A-Z][a-z]+\s*:)', '\n\n\\1', text)
    
    # Trim extra spaces
    text = text.strip()
    
    return text

def transcript_api(file):
    
    # files=[("files",file) for file in files]
    files = {"file": (file.name, file.getvalue(), file.type)}
    try:
        response=requests.post("http://localhost:8000/transcript",files=files)
        if response.status_code==200:
            for line in response.iter_lines():
                   if line :
                      yield line.decode("utf-8")
            # return data
        else:
            st.error(f"connection failed")
    except Exception as e:
        st.error(f"Error in code {e}")
        return []
    
def summarize_api(text):
    try:
          response=requests.post("http://localhost:8000/meeting_summary",json={"text": text})
         
          if response.status_code==200:
               data=response.json()
               return data
          else:
            st.error(f"connection failed")
    except Exception as e:
        st.error(f"Error in code {e}")
        return []  
     


def generate_pdf(text):
    try:
        response = requests.post("http://localhost:8000/pdf_download", params={"text": text})
        if response.status_code == 200:
            return response.content
        else:
            st.error("Failed to generate PDF")
    except Exception as e:
        st.error(f"Error in generating PDF: {e}")
        return None


audio = st.file_uploader("Upload an audio file", type=["mp3","mp4","m4a"])
# print(audio)
if audio is not None:
        
        if st.button("Start "):
 
            result = transcript_api(audio)
            # print(type(result))
            # print(type(result))
            # st.write(result)
            

             # Store the results in session state
            st.session_state["transcript_result"] = result
           
            transcript_text=""
            for line in result :
                transcript_text += line + "\n"

             # Clean the transcript text
            cleaned_transcript = clean_text(transcript_text)
            expander = st.expander("Transcript result")
            expander.write(cleaned_transcript)
            text_result=summarize_api(cleaned_transcript)
            st.session_state["summary_result"] = text_result
            expander_3 = st.expander("Summarize with Makrdown")
            expander_3.markdown(text_result)
            expander_2 = st.expander("Modification")
            modified_summary=expander_2.text_area("Modifier le text ", value=text_result)
            # Update session state directly when text_area value changes
            if "modified_summary" not in st.session_state or st.session_state["modified_summary"] != modified_summary:
                st.session_state["modified_summary"] = modified_summary

                    


# if "summary_result" in st.session_state:
if "modified_summary" in st.session_state:

    # if st.button("Generate PDF"):
    #     pdf_data = generate_pdf(st.session_state["summary_result"])
    #     if pdf_data:
    #         st.download_button(label="Download PDF", data=pdf_data, file_name="summary.pdf", mime="application/pdf")

# PDF Generation
# if "summary_result" in st.session_state:
    # summary_result = st.session_state["summary_result"]
    summary_result=st.session_state["modified_summary"]

    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template = env.get_template("./template/template.html")

    if st.button("Generate PDF"):
        html = template.render(
            text=summary_result,
            date=current_date.strftime("%Y-%m-%d")
        )

        pdf_data = pdfkit.from_string(html, False)

        if pdf_data:
            st.balloons()
            st.success("🎉 Your PDF was generated!")
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_data,
                file_name="summary.pdf",
                mime="application/pdf"
            )

   






