import streamlit as st
import os
import PyPDF2
import google.generativeai as genai
import pyttsx3
#import speech_recognition as sr
from datetime import datetime

# Configuración persistente del estado
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""
if 'voice_output' not in st.session_state:
    st.session_state.voice_output = False  # Habilitado por defecto

# **IMPORTANTE: Nueva clave para el valor del text_area**
# Esto evita el conflicto con la clave del widget itself.
if 'current_question_text' not in st.session_state:
    st.session_state.current_question_text = ""

# Configuración de la página
st.set_page_config(
    page_title="NeuroeXpand - Asistente Clínico",
    page_icon="🤖",
    layout="centered"
)

# Estilos CSS personalizados para diseño profesional
st.markdown("""
<style>
    /* Estilo base para todos los botones */
    .stButton>button {
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin: 5px 0;
        width: 100%;
    }
    
    /* Botón principal (Consultar) */
    .stButton>button:first-of-type {
        background-color: #4a6fa5;
        color: white;
        border: 1px solid #3a5a80;
    }
    
    .stButton>button:first-of-type:hover {
        background-color: #3a5a80;
        box-shadow: 0 4px 6px rgba(58, 90, 128, 0.1);
    }
    
    /* Botón de voz */
    .stButton>button:nth-of-type(2) {
        background-color: #f8f9fa;
        color: #4a6fa5;
        border: 1px solid #dee2e6;
    }
    
    .stButton>button:nth-of-type(2):hover {
        background-color: #e9ecef;
        color: #3a5a80;
    }
    
    /* Header profesional */
    .header {
        background: linear-gradient(135deg, #4a6fa5, #3a5a80);
        color: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    /* Checkbox profesional */
    .stCheckbox>div>div {
        background: #f8f9fa !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
    }
    
    /* Text area */
    .stTextArea>div>div>textarea {
        border-radius: 8px !important;
        border: 1px solid #dee2e6 !important;
    }
    
    /* Tarjeta de respuesta */
    .response-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #4a6fa5;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Configurar la API de Gemini
def configure_genai():
    genai.configure(api_key="AIzaSyAzPOlBiKoXpqFRLFzG6z_wuqPLE-aay4c")  # Reemplaza con tu API key

# Inicializar el motor de voz
def init_voice_engine():
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        return engine
    except Exception as e:
        st.warning(f"Voz no disponible: {e}")
        return None

# Función para reconocer voz
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Escuchando... Por favor hable ahora")
        audio = r.listen(source, timeout=5, phrase_time_limit=10)
        try:
            return r.recognize_google(audio, language='es-ES')
        except Exception:
            return None

# Extraer texto de PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error al leer PDF: {e}")
        return None

# Generar respuesta médica formateada
def generate_medical_response(pdf_text, question):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    Eres un médico experto analizando historias clínicas. Responde la siguiente pregunta 
    basándote EXCLUSIVAMENTE en la información proporcionada en el expediente clínico.
    
    Documento médico:
    {pdf_text[:15000]}
    
    Pregunta:
    {question}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error en IA: {e}")
        return None

# --- FUNCIONES DE CALLBACK ---

# Callback para el botón "Analizar con NeuroeXpand"
def on_analyze_click():
    # 'question_input' es la key del widget text_area. Su valor actual se guarda automáticamente
    # en st.session_state[key] cuando interactúas con él.
    # Por lo tanto, la pregunta se obtiene de st.session_state.question_input
    current_question = st.session_state.question_input # Obtiene el valor actual del textarea

    # Limpia el textarea estableciendo el valor de su clave en session_state a una cadena vacía.
    # Esto es seguro porque se ejecuta en el callback, ANTES de que el widget se re-renderice.
    st.session_state.question_input = "" 
    
    # Procesa la pregunta y genera la respuesta
    pdf_path = "HC.pdf"
    if not os.path.exists(pdf_path):
        st.error(f"Archivo no encontrado: {pdf_path}")
        st.session_state.last_response = "Error: Archivo PDF no encontrado."
        return

    pdf_text = extract_text_from_pdf(pdf_path)
    if not pdf_text:
        st.session_state.last_response = "Error: No se pudo extraer texto del PDF."
        return

    with st.spinner("Procesando consulta..."):
        response = generate_medical_response(pdf_text, current_question)
        st.session_state.last_response = response
        st.session_state.last_question = "" # Limpia la "última pregunta" si es necesario

        # Reproducir voz automáticamente si está habilitado
        if st.session_state.voice_output and 'voice_engine_instance' in st.session_state and st.session_state.voice_engine_instance and response:
            with st.spinner("Generando respuesta de voz..."):
                st.session_state.voice_engine_instance.say(response)
                st.session_state.voice_engine_instance.runAndWait()

# Callback para el botón "Preguntar por voz"
def on_voice_button_click():
    question = recognize_speech()
    if question:
        st.session_state.last_question = question
        # Asigna la pregunta reconocida a la clave del text_area en session_state
        # Esto se reflejará en el text_area en la próxima ejecución.
        st.session_state.question_input = question 
    else:
        st.warning("No se detectó voz. Intente nuevamente")


# Interfaz principal
def main():
    configure_genai()
    # Inicializa el motor de voz y guárdalo en session_state para que sea accesible en callbacks
    if 'voice_engine_instance' not in st.session_state:
        st.session_state.voice_engine_instance = init_voice_engine()
    
    # Header corporativo
    st.markdown("""
    <div class="header">
        <h1 style="margin:0; color:white;">🧑‍⚕️💻 NeuroeXpand</h1>
        <p style="margin:0; opacity:0.9;">Asistente Clínico Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra lateral con configuración e instrucciones
    st.session_state.voice_output = st.sidebar.checkbox(
        "Salida por voz", 
        value=st.session_state.voice_output,
        help="Activa/desactiva la reproducción de voz para las respuestas"
    )
    
    # Instrucciones de uso con estilo profesional
    st.sidebar.markdown("""
    <div style="background: #f8f9fa; 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 4px solid #4a6fa5;
                margin-top: 20px;">
        <h3 style="color: #3a5a80; margin-top:0;">Instrucciones</h3>
        <ol style="color: #495057;">
            <li style="margin-bottom: 8px;">🔔La información es extraída de fuentes autorizadas por NeuroXpand</li>
            <li style="margin-bottom: 8px;">🎤 Consultar por voz o texto</li>
            <li style="margin-bottom: 8px;">📄Integra la información que requieras para analizar con IA</li>
            
        
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar PDF (ajustar ruta)
    PDF_PATH = "HC.pdf"
    if not os.path.exists(PDF_PATH):
        st.error(f"Archivo no encontrado: {PDF_PATH}")
        # Considera cómo manejar esto para que el resto de la app no falle
        return
    
    # El texto del PDF se extrae al principio de la función main
    # para que esté disponible globalmente o se pase a las callbacks
    pdf_text = extract_text_from_pdf(PDF_PATH)
    if not pdf_text:
        return # Si no hay texto, no tiene sentido continuar
    
    st.markdown("### Realizar consulta")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Botón de voz profesional
        st.button(
            "🎤 Preguntar por voz", 
            key="voice_button", 
            on_click=on_voice_button_click # Asigna el callback aquí
        )
    
    with col2:
        # Entrada por texto
        # El valor del textarea se controla ahora directamente por st.session_state.question_input
        # La clave del widget y la clave del valor en session_state coinciden.
        st.text_area(
            "Escriba su pregunta:", 
            value=st.session_state.get('question_input', ''), # El valor inicial o actual
            height=100,
            placeholder="Ingrese su pregunta médica aquí...",
            key="question_input" # Esta es la key del widget, y también la clave en session_state para su valor
        )
    
    # Botón principal de consulta
    # Usa on_click para llamar a la función que procesa y limpia
    st.button(
        "🔍 Analizar con NeuroeXpand", 
        type="primary", 
        key="main_button",
        on_click=on_analyze_click # Asigna el callback aquí
    )
    
    # Mostrar respuesta si existe
    if st.session_state.last_response:
        st.markdown("---")
        st.markdown("### Respuesta")
        st.markdown(st.session_state.last_response)

if __name__ == "__main__":
    main()
