import streamlit as st
import pypdf

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Vérificateur MOP - P&G Amiens",
    page_icon="✅",  # Tu peux mettre "✅" ou "✔" ici
    layout="wide"
)

st.title("✅ Assistant de Conformité - Mode Opératoire & JSA")
st.markdown("### Site P&G Amiens - Sécurité Construction")
st.markdown("Cet outil analyse à la volée votre document (PDF) pour vérifier sa conformité avec les exigences du manuel de sécurité (structure, risques, EPI, et procédures)[cite: 10]. **Aucune donnée n'est stockée.**")

# Zone de dépôt du fichier
uploaded_file = st.file_uploader("Glissez-déposez votre Mode Opératoire ou JSA (format PDF)", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Analyse du document en cours..."):
        # Extraction du texte du PDF en mémoire
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
            
    st.success("Document analysé avec succès !")
    
    # Définition des critères stricts basés sur le manuel P&G
    criteres = {
        "Références administratives (PDP / MOP)": ["pdp", "mop", "plan de prévention", "mode opératoire"],
        "Décomposition chronologique des tâches": ["tâche", "phase", "étape", "préparation"],
        "Analyse des risques associés": ["risque", "chute", "écrasement", "coupure", "incendie", "lombalgie"],
        "Mesures de prévention & EPI (Normes)": ["epi", "casque", "gant", "balisage", "jugulaire", "vgp", "en 388"],
        "Tâches à haut risque / Permis spécifiques": ["permis", "consigné", "espace confiné", "grutage", "point chaud", "loto"]
    }
    
    score = 0
    total_criteres = len(criteres)
    resultats_verification = []
    
    text_lower = text.lower()
    
    for categorie, mots_cles in criteres.items():
        trouve = any(kw in text_lower for kw in mots_cles)
        if trouve:
            score += 1
            resultats_verification.append((categorie, "Conforme / Mentionné", "success"))
        else:
            resultats_verification.append((categorie, "Non détecté ou insuffisant", "warning"))
            
    # Calcul du score final
    score_final = int((score / total_criteres) * 100)
    
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric(label="Score de conformité estimé", value=f"{score_final}%")
        if score_final >= 80:
            st.success("Le document présente une bonne structure de prévention conforme aux attentes du site.")
        else:
            st.warning("Attention : des éléments obligatoires exigés par le manuel P&G semblent absents.")
            
    with col2:
        st.markdown("### 📋 Détail de l'analyse par critères :")
        for cat, statut, type_alerte in resultats_verification:
            if type_alerte == "success":
                st.success(f"**{cat}** : ✅ {statut}")
            else:
                st.warning(f"**{cat}** : ⚠️ {statut}")
                
    st.markdown("---")
    st.markdown("### 🔍 Rappels des exigences du Manuel P&G Amiens :")
    st.info("""
    * **Règles générales :** Vérifiez que le balisage de la zone et la gestion quotidienne du *Housekeeping/5S* sont bien mentionnés[cite: 10].
    * **EPI & Normes :** Assurez-vous que les références normatives (comme les gants adaptés ou la jugulaire pour le travail en hauteur) sont explicitées[cite: 10].
    * **Validation :** Pour rappel, tout MOP doit être soumis au service sécurité construction au moins 48 heures avant le début de l'activité[cite: 10].
    """)
else:
    st.info("Veuillez importer un fichier PDF pour lancer l'évaluation.")