import streamlit as st
import speech_recognition as sr
import google.generativeai as genai
import base64
import time
import pygame
import io
from gtts import gTTS
from PyPDF2 import PdfReader

# Configurer l'API Google Generative AI
genai.configure(api_key='Your_GEMINI_API_KEY')

# Titre de l'application
st.title("صوت القانون ")

# Description du chatbot
st.markdown("""

صوت القانون هو شات بوت تم تطويره من قبل مجموعة AI Defenders. يتحدث بالعربية ويعتمد على ملف PDF يحتوي على قوانين مغربية بهدف توعية الناس بالقوانين وحقوقهم وواجباتهم.
""")

# Afficher une image GIF dans la mise en page
with open("chatbot.gif", "rb") as file:
    img_url = base64.b64encode(file.read()).decode("utf-8")

img_width = 400
st.markdown(
    f'<img src="data:image/jpg;base64,{img_url}" alt="chatbot" style="width: {img_width}px; float: right; margin-right: 32%;">',
    unsafe_allow_html=True,
)

# Initialiser l'état de session pour la visibilité de la conversation
if "show_conversation" not in st.session_state:
    st.session_state.show_conversation = False

# Fonction pour convertir la parole en texte
def recognize_speech_from_mic(language="ar"):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        st.info("Listening...")
        audio = recognizer.listen(source)

    try:
        st.info("Recognizing speech...")
        text = recognizer.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        st.error("Google Speech Recognition could not understand audio")
        return None
    except sr.RequestError as e:
        st.error(f"Could not request results; {e}")
        return None

# Initialiser le mixeur Pygame
pygame.mixer.init()

# Fonction pour convertir le texte en parole
def text_to_speech(text, language="ar"):
    tts = gTTS(text, lang=language)
    output = io.BytesIO()
    tts.write_to_fp(output)
    output.seek(0)
    pygame.mixer.music.load(output)
    pygame.mixer.music.play()
    
    # Attendre que l'audio finisse de jouer
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Charger les informations en arabe à partir d'un fichier PDF
with open("info_arabic.pdf", "rb") as file:
    pdf_reader = PdfReader(file)
    Info = ""
    for page in pdf_reader.pages:
        Info += page.extract_text()

Question = ''

# Section pour la saisie vocale
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Speak"):
        recognized_text = recognize_speech_from_mic()
        if recognized_text:
            Question = recognized_text

# Section pour la saisie de texte
with col2:
    typed_question = st.text_input("Or type your question here:")
    if typed_question:
        Question = typed_question

# Bouton pour afficher/masquer la conversation
if st.button("Show/Hide Conversation"):
    st.session_state.show_conversation = not st.session_state.show_conversation

# Préparer la demande pour l'API
prompt = f'''
Question: {Question}.

Respond to this question in Arabic based on the Info provided below. If the question is not related to the Info, respond based on your knowledge but in Arabic.

Info: {Info}.
'''

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

def get_chat_response(prompt):
    bot_message = model.generate_content(prompt)
    return bot_message.text

# Emulateur de réponse en flux
def response_generator(prompt):
    response = get_chat_response(prompt)
    
    for word in response.split():
        yield word + " "
        time.sleep(0.06)

# Initialiser l'historique de la conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher les messages de la conversation à partir de l'historique lors du rechargement de l'application
if st.session_state.show_conversation:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Initialiser la variable de réponse
response = ""

# Accepter l'entrée de l'utilisateur
if Question != '':
    # Ajouter le message de l'utilisateur à l'historique de la conversation
    st.session_state.messages.append({"role": "user", "content": Question})
    # Afficher le message de l'utilisateur dans le conteneur de message de chat
    if st.session_state.show_conversation:
        with st.chat_message("user"):
            st.markdown(Question)

    # Afficher la réponse de l'assistant dans le conteneur de message de chat
    if st.session_state.show_conversation:
        with st.chat_message("assistant"):
            response = st.write_stream(response_generator(prompt))
    else:
        response = get_chat_response(prompt)

    # Ajouter la réponse de l'assistant à l'historique de la conversation
    st.session_state.messages.append({"role": "assistant", "content": response})
    text_to_speech(response)

# Afficher la réponse de l'assistant si la conversation n'est pas affichée
if response and not st.session_state.show_conversation:
    st.write(response)

# Ajouter un peu de CSS pour améliorer l'apparence
st.markdown("""
    <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTextInput>div>input {
            padding: 10px;
            font-size: 16px;
            border-radius: 8px;
            border: 1px solid #ccc;
            margin-top: 10px;
        }
        .stRadio>div>label {
            margin-right: 10px;
        }
    </style>
""", unsafe_allow_html=True)
