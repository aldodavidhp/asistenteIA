import streamlit as st
import os
import PyPDF2
import google.generativeai as genai
from datetime import datetime

# --- Configuración persistente del estado ---
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""
if 'question_input' not in st.session_state:
    st.session_state.question_input = ""
if 'protocol_pdf_text' not in st.session_state: # Para el texto del protocolo cargado
    st.session_state.protocol_pdf_text = None
if 'hc_pdf_text' not in st.session_state: # Para el texto del HC fijo
    st.session_state.hc_pdf_text = None
if 'use_protocol_for_analysis' not in st.session_state: # Nuevo para la opción de usar protocolo
    st.session_state.use_protocol_for_analysis = False

# --- Configuración de la página ---
st.set_page_config(
    page_title="iTziA - Asistente Clínico",
    page_icon="🤖",
    layout="centered" # Cambiado a 'wide' si se quiere más espacio, 'centered' es el predeterminado
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
        margin-bottom: 10px; /* Espacio debajo del checkbox */
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
    
    /* Estilo para el uploader de archivos */
    .stFileUploader>div>div {
        border: 2px dashed #4a6fa5;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        background-color: #e6f0fa;
    }
</style>
""", unsafe_allow_html=True)

# --- Configurar la API de Gemini ---
def configure_genai():
    # Asegúrate de reemplazar "TU_API_KEY_AQUI" con tu clave real de la API de Google Gemini
    genai.configure(api_key="TU_API_KEY_AQUI")

# --- Extraer texto de PDF ---
def extract_text_from_pdf(pdf_source):
    text = ""
    try:
        if isinstance(pdf_source, str): # Si es una ruta de archivo (para HC.pdf)
            with open(pdf_source, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() or ""
        elif hasattr(pdf_source, 'read'): # Si es un objeto UploadedFile de Streamlit
            reader = PyPDF2.PdfReader(pdf_source)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error al leer PDF: {e}")
        return None

# --- Generar respuesta médica formateada ---
def generate_medical_response(hc_text, protocol_text, use_protocol, question):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    Eres un médico experto analizando información clínica. Responde la siguiente pregunta
    basándote EXCLUSIVAMENTE en la información proporcionada en los documentos.

    Documento de Historial Clínico (HC):
    {hc_text[:15000]}
    """
    
    if use_protocol and protocol_text:
        prompt += f"""
        Documento de Protocolo de Reconstrucción Articular (Cadera/Rodilla):
        {protocol_text[:15000]}
        """
    
    prompt += f"""
    
    Pregunta:
    {question}
    
    Si se indicó usar el protocolo, integra la información de ambos documentos (HC y Protocolo) de forma coherente y profesional.
    Si el protocolo no se indicó o no está disponible, responde solo con la información del HC.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error en IA: {e}")
        return None

# --- FUNCIONES DE CALLBACK ---

def on_analyze_click():
    current_question = st.session_state.question_input
    
    # Limpia el text_area en session_state *antes* de que se re-renderice
    st.session_state.question_input = "" 
    
    # Asegúrate de que el HC esté cargado antes de proceder
    if not st.session_state.hc_pdf_text:
        st.session_state.last_response = "Error: El Historial Clínico no se pudo cargar. Asegúrate de que 'HC.pdf' existe en la ruta."
        return

    hc_text_to_analyze = st.session_state.hc_pdf_text
    protocol_text_to_analyze = st.session_state.protocol_pdf_text if st.session_state.use_protocol_for_analysis else None

    with st.spinner("Procesando consulta..."):
        response = generate_medical_response(hc_text_to_analyze, protocol_text_to_analyze, st.session_state.use_protocol_for_analysis, current_question)
        st.session_state.last_response = response
        st.session_state.last_question = "" # Limpia la "última pregunta" si es necesario

# --- Interfaz principal ---
def main():
    configure_genai()
    
    # --- Header corporativo ---
    st.markdown("""
    <div class="header">
        <h1 style="margin:0; color:white;">🧑‍⚕️💻 iTziA</h1>
        <p style="margin:0; opacity:0.9;">Asistente Clínico Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Estructura principal sin columnas para reubicar elementos ---
    
    st.markdown("### Dr. Estrada")
    
    # --- Cargar PDF del Historial Clínico (fijo) ---
    PDF_HC_PATH = "HC.pdf"
    if not os.path.exists(PDF_HC_PATH):
        st.error(f"Error: Archivo de Historial Clínico no encontrado en la ruta fija: {PDF_HC_PATH}. Por favor, asegúrate de que 'HC.pdf' esté presente.")
        st.session_state.hc_pdf_text = None
    else:
        if st.session_state.hc_pdf_text is None: # Solo carga si no se ha cargado antes
            st.session_state.hc_pdf_text = extract_text_from_pdf(PDF_HC_PATH)
            if st.session_state.hc_pdf_text:
                st.success(f"Historial Clínico (HC.pdf) cargado desde {PDF_HC_PATH}.")
            else:
                st.error(f"No se pudo extraer texto del Historial Clínico (HC.pdf). Asegúrate de que el PDF sea de texto.")
        else:
            st.info(f"Historial Clínico (HC.pdf) ya está cargado desde {PDF_HC_PATH}.")

    # --- Sección de carga de Protocolo de Reconstrucción Articular (ahora en el cuerpo principal) ---
    st.subheader("Cargar Protocolo de Reconstrucción Articular")
    uploaded_protocol_file = st.file_uploader(
        "Sube el archivo PDF del Protocolo de Reconstrucción Articular (Cadera/Rodilla)", 
        type="pdf", 
        key="protocol_uploader"
    )

    if uploaded_protocol_file is not None:
        st.session_state.protocol_pdf_text = extract_text_from_pdf(uploaded_protocol_file)
        if st.session_state.protocol_pdf_text:
            st.success("Protocolo de Reconstrucción Articular cargado correctamente.")
        else:
            st.error("No se pudo extraer texto del Protocolo. Asegúrate de que el PDF sea de texto y no una imagen.")
    elif 'protocol_pdf_text' in st.session_state and st.session_state.protocol_pdf_text:
        st.info("Protocolo de Reconstrucción Articular cargado previamente.")
    else:
        st.info("No se ha cargado ningún Protocolo de Reconstrucción Articular.")

    st.markdown("---")
    
    # --- Sección de entrada de texto ---
    st.text_area(
        "¿En qué puedo ayudarte?", 
        value=st.session_state.get('question_input', ''), 
        height=100,
        placeholder="Ingrese su pregunta médica aquí...",
        key="question_input"
    )
    
    # --- Casilla de verificación para usar el protocolo ---
    st.session_state.use_protocol_for_analysis = st.checkbox(
        "**✅ Complementar con el Protocolo de Reconstrucción Articular**",
        value=st.session_state.use_protocol_for_analysis,
        help="Marca esta casilla si deseas que la IA use la información del protocolo cargado para responder a tu pregunta."
    )

    # --- Botón principal de consulta ---
    st.button(
        "🔍 Analizar con iTziA", 
        type="primary", 
        key="main_button",
        on_click=on_analyze_click
    )
    
    # --- Mostrar respuesta si existe ---
    if st.session_state.last_response:
        st.markdown("---")
        st.markdown("### Respuesta")
        st.markdown(st.session_state.last_response)

    # --- Barra lateral con instrucciones (se mantiene aquí, pero se puede mover si se desea) ---
    st.sidebar.markdown("""
    <div style="background: #f8f9fa;  
                padding: 15px;  
                border-radius: 8px;  
                border-left: 4px solid #4a6fa5;
                margin-top: 20px;">
        <h3 style="color: #3a5a80; margin-top:0;">Instrucciones</h3>
        <ol style="color: #495057;">
            <li style="margin-bottom: 8px;">🔔 La información es extraída de fuentes autorizadas por iTziA.</li>
            <li style="margin-bottom: 8px;">⬆️ Sube el PDF del **Protocolo** en la sección principal. El Historial Clínico (HC.pdf) se carga automáticamente.</li>
            <li style="margin-bottom: 8px;">⌨️ Escribe tu consulta en el área de texto.</li>
            <li style="margin-bottom: 8px;">🤝 Marca la casilla para que iTziA use el Protocolo en su análisis.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
