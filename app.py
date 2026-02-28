import streamlit as st
import PyPDF2
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io
import re

st.set_page_config(page_title="Générateur de Gammes IA", layout="wide")

# Intégration de l'ID session
st.sidebar.info("ID Utilisateur : 2033065084")

st.title("⚙️ Assistant de Fiabilité & Maintenance IA")

# --- CONNEXION INVISIBLE AU COFFRE-FORT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ Clé API non configurée dans les secrets du serveur.")
    st.stop()

available_models = []

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name.replace('models/', ''))
except Exception as e:
    st.error("Impossible de joindre Google.")

if available_models:
    selected_model = st.selectbox("Sélectionnez le moteur IA :", available_models)
    model = genai.GenerativeModel(selected_model)

    tab1, tab2 = st.tabs(["📄 Analyse de Manuel (PDF)", "📸 Plaque Signalétique (Photo)"])

    # ==========================================
    # ONGLET 1 : MANUEL PDF
    # ==========================================
    with tab1:
        st.header("Extraction depuis un document technique")
        uploaded_pdf = st.file_uploader("Chargez le manuel (PDF)", type="pdf")

        if uploaded_pdf and st.button("🚀 Analyser le manuel"):
            with st.spinner("Lecture et préparation de l'export Excel..."):
                pdf_reader = PyPDF2.PdfReader(uploaded_pdf)
                texte_manuel = "".join([page.extract_text() for page in pdf_reader.pages])
                
                prompt_pdf = f"""Tu es un Ingénieur Fiabiliste. Extrais un plan de maintenance pour notre GMAO.
                Format Markdown :
                1. 🆔 Carte d'Identité
                2. ⚠️ Sécurité & Consignation
                3. 🧰 Kit d'Intervention
                4. 📅 Gammes Préventives
                5. 🔍 Points Critiques AMDEC
                
                IMPORTANT : À la toute fin de ta réponse, génère un bloc de code ```csv contenant uniquement le tableau de la gamme de maintenance avec comme séparateur le point-virgule (;). Colonnes : Organe;Action;Périodicité;Pièces/Outillage.
                
                Texte : {texte_manuel[:30000]}"""
                
                try:
                    response = model.generate_content(prompt_pdf)
                    texte_complet = response.text
                    
                    affichage_visuel = re.sub(r'```csv.*?```', '', texte_complet, flags=re.IGNORECASE | re.DOTALL)
                    st.success("Gamme générée avec succès !")
                    st.markdown(affichage_visuel)
                    
                    csv_match = re.search(r'```csv\n(.*?)\n```', texte_complet, re.IGNORECASE | re.DOTALL)
                    if csv_match:
                        csv_texte = csv_match.group(1).strip()
                        try:
                            df = pd.read_csv(io.StringIO(csv_texte), sep=";")
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False, sheet_name='Planning')
                            
                            st.download_button(
                                label="📥 Télécharger le Planning sur Excel",
                                data=output.getvalue(),
                                file_name="Planning_Maintenance.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        except Exception:
                            pass
                except Exception as e:
                    st.error(f"Erreur avec ce modèle : {e}")

    # ==========================================
    # ONGLET 2 : PLAQUE SIGNALÉTIQUE (MODIFIÉ AVEC CAMÉRA)
    # ==========================================
    with tab2:
        st.header("Génération depuis le terrain")
        
        # Le technicien peut choisir d'importer ou de prendre une photo en direct
        methode_capture = st.radio("Comment souhaitez-vous fournir l'image ?", ["Ouvrir l'appareil photo 📷", "Importer un fichier 📁"])
        
        uploaded_image = None
        
        if methode_capture == "Ouvrir l'appareil photo 📷":
            uploaded_image = st.camera_input("Prenez la plaque en photo")
        else:
            uploaded_image = st.file_uploader("Chargez la photo de la plaque", type=["jpg", "jpeg", "png"])

        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Plaque prête pour l'analyse", width=400)
            
            if st.button("🔍 Identifier et Générer la Gamme"):
                with st.spinner("Analyse optique et préparation de l'export Excel..."):
                    prompt_vision = """Tu es un Responsable Technique. 
                    1. Fais l'OCR de cette plaque.
                    2. Génère une gamme de maintenance standardisée.
                    Format Markdown :
                    ### 🆔 Identification (Lu sur la plaque)
                    ### ⚠️ Risques et Sécurité standards
                    ### 📅 Plan de Maintenance Préventif Recommandé
                    ### 🔍 Points de vigilance majeurs
                    
                    IMPORTANT : À la toute fin de ta réponse, génère un bloc de code ```csv contenant uniquement le tableau du plan de maintenance avec comme séparateur le point-virgule (;). Colonnes : Organe;Action;Périodicité;Pièces/Outillage.
                    """
                    
                    try:
                        response = model.generate_content([prompt_vision, image])
                        texte_complet = response.text
                        
                        affichage_visuel = re.sub(r'```csv.*?```', '', texte_complet, flags=re.IGNORECASE | re.DOTALL)
                        st.success("Gamme générée !")
                        st.markdown(affichage_visuel)
                        
                        csv_match = re.search(r'```csv\n(.*?)\n```', texte_complet, re.IGNORECASE | re.DOTALL)
                        if csv_match:
                            csv_texte = csv_match.group(1).strip()
                            try:
                                df = pd.read_csv(io.StringIO(csv_texte), sep=";")
                                output = io.BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    df.to_excel(writer, index=False, sheet_name='Planning')
                                
                                st.download_button(
                                    label="📥 Télécharger le Planning sur Excel",
                                    data=output.getvalue(),
                                    file_name="Planning_Terrain.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except Exception:
                                pass
                    except Exception as e:
                        st.error(f"⚠️ Erreur avec ce modèle : {e}")