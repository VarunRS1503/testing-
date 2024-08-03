import streamlit as st
import tempfile
import os
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from crewai import Process, Agent, Task, Crew
from langchain_groq import ChatGroq
from agents import compliance_agents, compliance_agents_tasks
from utils import extract_compliance_issues, format_compliance_issues, split_compliance_issues

# Initialize the Deepgram client
DG_KEY = "88b968f3e3cfc8eaf5a596e15c579ffca9a59aed"
deepgram = DeepgramClient(DG_KEY)

def transcribe_audio_file(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        buffer_data = audio_file.read()

    options = {
        "model": "nova-2",
        "smart_format": True,
        "language": "hi",
        "diarize": True,
        "profanity_filter": False
    }
    payload = {
        "buffer": buffer_data,
    }
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
    return response

def process_diarized_transcript(res):
    transcript = res['results']['channels'][0]['alternatives'][0]
    words = res['results']['channels'][0]['alternatives'][0]['words']
    current_speaker = None
    current_sentence = []
    output = []
    for word in words:
        if current_speaker != word['speaker']:
            if current_sentence:
                output.append((current_speaker, ' '.join(current_sentence)))
                current_sentence = []
            current_speaker = word['speaker']

        current_sentence.append(word['punctuated_word'])

        if word['punctuated_word'].endswith(('.', '?', '!')):
            output.append((current_speaker, ' '.join(current_sentence)))
            current_sentence = []

    if current_sentence:
        output.append((current_speaker, ' '.join(current_sentence)))
    return output

def format_speaker(speaker_num):
    return "recovery_agent" if speaker_num == 0 else "customer"

def transcribe_and_process_audio(audio_file_path):
    res = transcribe_audio_file(audio_file_path)
    diarized_result = process_diarized_transcript(res)
    if not diarized_result:
        return "No transcription available. The audio might still be too low quality or silent."

    transcription = ""
    for speaker, sentence in diarized_result:
        line = f"{format_speaker(speaker)}: {sentence}\n"
        transcription += line

    return transcription

def analyze_compliance(text):
    compliance_structure = '''{
        "compliance_issues": [
            {
                "issue_occurred": "code and Name of the compliance issue identified",
                "conversation_part": "<text_excerpt_from_conversation where the non-compliance has occurred>"
            }
        ]
    }'''

    agent = compliance_agents()
    compliance_monitor_agent = agent.compliance_monitor()
    tasks = compliance_agents_tasks()
    compliance_monitor_task = tasks.compliance_monitor_task(compliance_monitor_agent)

    crew = Crew(agents=[compliance_monitor_agent], tasks=[compliance_monitor_task], verbose=False)

    output = crew.kickoff(inputs={'text': text, 'compliance_structure': compliance_structure})
    output_string = output.raw
    output_dict = extract_compliance_issues(output_string)

    if output_dict:
        customer_dict, agent_dict = split_compliance_issues(output_dict)
        customer_issues = format_compliance_issues(customer_dict)
        recovery_agent_issues = format_compliance_issues(agent_dict)
        return customer_issues, recovery_agent_issues
    else:
        return None, None

# Streamlit interface
st.title("Audio Transcription and Compliance Monitoring")

uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
        temp_audio_file.write(uploaded_file.read())
        temp_audio_file_path = temp_audio_file.name

    st.write("Transcribing audio...")
    transcription = transcribe_and_process_audio(temp_audio_file_path)
    
    st.write("Transcription:")
    st.text(transcription)

    if st.button("Analyze Compliance"):
        st.write("Analyzing compliance...")
        customer_issues, recovery_agent_issues = analyze_compliance(transcription)

        st.subheader("Detected Compliance Violations by Customer")
        st.text(customer_issues if customer_issues else "No compliance violations detected for the customer.")
        st.subheader("Detected Non-Compliance Violations by Recovery Agent")
        st.text(recovery_agent_issues if recovery_agent_issues else "No compliance violations detected for the recovery agent.")
