import streamlit as st
import os
import PyPDF2
import google.generativeai as genai
from datetime import datetime

# --- Configuración persistente del estado (sin voz) ---
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""
# 'voice_output' y 'voice_engine_instance' ya no son necesarios, se eliminan.

# **IMPORTANTE: Clave para el valor del text_area**
# Se mantiene esta clave para controlar el text_area
if 'question_input' not in st.session_state: # Usamos la misma clave que el widget para simplificar
    st.session_state.question_input = ""

# --- Configuración de la página ---
st.set_page_config(
    page_title="ItzAI - Asistente Clínico",
    page_icon="🤖",
    layout="centered"
)

# --- Estilos CSS personalizados para diseño profesional ---
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
    
    /* Botón de voz (este estilo se podría eliminar si no hay botón de voz) */
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

# --- Configurar la API de Gemini ---
def configure_genai():
    genai.configure(api_key="AIzaSyAzPOlBiKoXpqFRLFzG6z_wuqPLE-aay4c")  # Reemplaza con tu API key

# --- Extraer texto de PDF ---
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

# --- Generar respuesta médica formateada ---
def generate_medical_response(pdf_text, question):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    Eres un médico experto analizando historias clínicas. Responde la siguiente pregunta 
    basándote EXCLUSIVAMENTE en la información proporcionada en el expediente clínico.
        Formato de respuesta requerido:
    
    **EXPEDIENTE | ItzIA**
    **Fecha**: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    **Consulta**: {question[:100]}{'...' if len(question) > 100 else ''}
    
    **Hallazgos Clínicos**:
    - [Análisis detallado de los hallazgos relevantes]
    
    **Evaluación Neurológica**:
    - [Interpretación de los datos neurológicos]
    
    **Recomendaciones**:
    - [Sugerencias basadas en la evidencia]
    
    **Tecnologías Aplicables**:
    - [Posibles estudios complementarios: EEG, PSG, BCI, etc.]
    
    
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

# --- FUNCIONES DE CALLBACK (Solo para el botón de análisis) ---

def on_analyze_click():
    # Obtiene la pregunta actual del text_area (su valor está en st.session_state.question_input)
    current_question = st.session_state.question_input

    # Limpia el text_area en session_state *antes* de que se re-renderice
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

# --- Interfaz principal ---
def main():
    configure_genai()
    
    # --- Header corporativo ---
    st.markdown("""
    <div class="header">
        <h1 style="margin:0; color:white;">🧑‍⚕️💻 ItzAI</h1>
        <p style="margin:0; opacity:0.9;">Asistente Clínico Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Barra lateral con instrucciones (sin opción de voz) ---
    st.sidebar.markdown("""
    <div style="background: #f8f9fa; 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 4px solid #4a6fa5;
                margin-top: 20px;">
        <h3 style="color: #3a5a80; margin-top:0;">Instrucciones</h3>
        <ol style="color: #495057;">
            <li style="margin-bottom: 8px;">🔔 La información es extraída de fuentes autorizadas por NeuroXpand</li>
            <li style="margin-bottom: 8px;">⌨️ Escribe tu consulta en el área de texto</li>
            <li style="margin-bottom: 8px;">📄 Integra la información que requieras para analizar con IA</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Cargar PDF (ajustar ruta) ---
    PDF_PATH = "HC.pdf"
    if not os.path.exists(PDF_PATH):
        st.error(f"Archivo no encontrado: {PDF_PATH}")
        return
    
    pdf_text = extract_text_from_pdf(PDF_PATH)
    if not pdf_text:
        return 
    
    st.markdown("### Realizar consulta")
    
    # --- Sección de entrada de texto (sin botón de voz) ---
    # Usamos st.session_state.question_input directamente como value
    # para que el textarea se limpie mediante el callback.
    st.text_area(
        "Escriba su pregunta:", 
        value=st.session_state.get('question_input', ''), 
        height=100,
        placeholder="Ingrese su pregunta médica aquí...",
        key="question_input" # Esta es la clave del widget y también la que controla su valor en session_state
    )
    
    # --- Botón principal de consulta ---
    # Usa on_click para llamar a la función que procesa y limpia
    st.button(
        "🔍 Analizar con NeuroeXpand", 
        type="primary", 
        key="main_button",
        on_click=on_analyze_click # Asigna el callback aquí
    )
    
    # --- Mostrar respuesta si existe ---
    if st.session_state.last_response:
        st.markdown("---")
        st.markdown("### Respuesta")
        st.markdown(st.session_state.last_response)

if __name__ == "__main__":
    main()
