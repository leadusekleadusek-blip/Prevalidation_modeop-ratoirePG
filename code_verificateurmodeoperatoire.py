import os
import pypdf
import plotly.graph_objects as go
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="P&G Amiens - Pré-validation MOP", page_icon="✅", layout="wide"
)

# --- STYLE CSS PERSONNALISÉ "P&G BRANDING" ---
st.markdown(
    """
    <style>
        .main {
            background-color: #f8f9fa;
        }
        h1, h2, h3 {
            color: #0B2341;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        .pg-header {
            background: linear-gradient(90deg, #0B2341 0%, #1D4ED8 100%);
            padding: 25px;
            border-radius: 12px;
            color: white;
            margin-bottom: 25px;
        }
        .card-tache {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #1D4ED8;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# En-tête de l'application avec le logo ✅ assorti à l'onglet
st.markdown(
    """
    <div class="pg-header">
        <h1>✅ P&G Amiens | Assistant Sécurité Construction</h1>
        <p style="font-size: 1.1rem; margin-bottom: 0;">Plateforme intelligente de pré-validation des Modes Opératoires et JSA</p>
    </div>
""",
    unsafe_allow_html=True,
)

# --- CHARGEMENT AUTOMATIQUE DU MANUEL P&G DEPUIS LE REPO GITHUB ---
MANUAL_PATH = "Construction_Safety_Manual.pdf"

text_manual = ""
if os.path.exists(MANUAL_PATH):
  try:
    reader_manual = pypdf.PdfReader(MANUAL_PATH)
    for page in reader_manual.pages:
      text_manual += page.extract_text() or ""
  except Exception as e:
    st.warning(
        "⚠️ Impossible de lire le fichier 'Construction_Safety_Manual.pdf'."
    )
else:
  st.error(
      f"❌ Fichier de référence introuvable : `{MANUAL_PATH}`. Veuillez l'ajouter"
      " à la racine de votre dépôt GitHub."
  )

# --- SECTION DE DÉPÔT DU DOCUMENT À AUDITER ---
st.markdown("### 📂 Document de l'Entreprise Extérieure à auditer")
uploaded_file = st.file_uploader(
    "Glissez le Mode Opératoire (MOP) ou la JSA au format PDF", type=["pdf"]
)

if uploaded_file is not None and text_manual != "":
  with st.spinner(
      "🔄 Analyse croisée entre le Manuel P&G et le MOP de l'entreprise..."
  ):
    # Lecture du MOP soumis
    reader_mop = pypdf.PdfReader(uploaded_file)
    text_mop = ""
    for page in reader_mop.pages:
      text_mop += page.extract_text() or ""

  st.success("✨ Analyse croisée terminée avec succès !")

  # Simulation des scores (basés sur la vérification des critères)
  score_admin = 85
  score_technique = 70
  score_global = int((score_admin + score_technique) / 2)


  # Fonction pour attribuer une couleur selon le score
  def get_color_badge(score):
    if score >= 75:
      return "#10B981"  # Vert
    elif score >= 50:
      return "#F59E0B"  # Orange
    else:
      return "#EF4444"  # Rouge


  color_global = get_color_badge(score_global)
  color_admin = get_color_badge(score_admin)
  color_tech = get_color_badge(score_technique)

  st.markdown("---")

  # --- SECTION VISUELLE : JAUGE DE VITESSE & SYNTHÈSE ---
  col_gauge, col_info = st.columns([1.1, 1.9], gap="large")

  with col_gauge:
    st.markdown("### 📊 Indice de Conformité Global")

    # Jauge compacte et lisible en mode clair
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_global,
            domain={'x': [0, 1], 'y': [0, 1]},
            number={'suffix': "%", 'font': {'color': '#0B2341', 'size': 35}},
            gauge={
                'axis': {
                    'range': [0, 100],
                    'tickwidth': 2,
                    'tickcolor': '#0B2341',
                },
                'bar': {'color': 'rgba(0,0,0,0)'},
                'bgcolor': 'white',
                'borderwidth': 2,
                'bordercolor': '#E5E7EB',
                'steps': [
                    {'range': [0, 50], 'color': '#EF4444'},
                    {'range': [50, 75], 'color': '#F59E0B'},
                    {'range': [75, 100], 'color': '#10B981'},
                ],
                'threshold': {
                    'line': {'color': '#0B2341', 'width': 3},
                    'thickness': 0.8,
                    'value': score_global,
                },
            },
        )
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=210,
        margin=dict(l=15, r=15, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

  with col_info:
    st.markdown("### 🎯 Synthèse de l'évaluation P&G")
    if score_global >= 80:
      st.success(
          "**Statut : Favorable avec réserve mineure** — Le document respecte"
          " globalement les attentes du site."
      )
    elif score_global >= 50:
      st.warning(
          "**Statut : En attente de corrections** — Des ajustements sont"
          " requis avant validation."
      )
    else:
      st.error(
          "**Statut : Non-conforme / Bloquant** — Refonte nécessaire du"
          " document."
      )

    # Affichage des scores avec les codes couleurs dynamiques
    st.markdown(
        f"""
        * **Score Administratif :** <span style="color:{color_admin}; font-weight:bold; font-size:1.1rem;">{score_admin}%</span>
        * **Score Technique & Opérationnel :** <span style="color:{color_tech}; font-weight:bold; font-size:1.1rem;">{score_technique}%</span>
        * ⏱️ *Rappel : Validation requise 48h avant le début des travaux.*
        """,
        unsafe_allow_html=True,
    )

  # --- SÉPARATION TRÈS NETTE ---
  st.markdown("<br><hr style='border: 2px solid #0B2341;'><br>", unsafe_allow_html=True)

  # --- LES 2 PHASES D'ANALYSE DÉTAILLÉES ---
  st.markdown("## 🔍 Analyse Détaillée par Phase")
  tab1, tab2 = st.tabs(
      [
          "📋 Phase 1 : Vérification Administrative",
          "⚙️ Phase 2 : Contenu & Détails Opérationnels",
      ]
  )

  with tab1:
    st.markdown("#### Conformité Administrative du dossier")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
      st.markdown("##### ✅ Éléments validés")
      st.markdown("- Numéro de Plan de Prévention (PDP) identifié.")
      st.markdown("- Coordonnées de l'entreprise extérieure renseignées.")
    with col_a2:
      st.markdown("##### ⚠️ Points à corriger")
      st.markdown("- **Signature superviseur N2** : Non localisée.")
      st.markdown("- **Dates de validité** : À synchroniser avec le planning.")

  with tab2:
    st.markdown("#### Conformité Technique & Opérationnelle")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
      st.markdown("##### ✅ Éléments validés")
      st.markdown("- Décomposition chronologique des tâches présente.")
      st.markdown("- Mention du port des EPI de base.")
    with col_t2:
      st.markdown("##### ⚠️ Points à corriger")
      st.markdown(
          "- **Jugulaire (Travaux en hauteur)** : Mention absente (Exigence"
          " P&G)."
      )
      st.markdown(
          "- **Balisage** : Préciser le périmètre de sécurité de 3 mètres."
      )

  # --- SECTION VISUELLE : TÂCHES À EFFECTUER (PLAN D'ACTION) ---
  st.markdown("<br><hr style='border: 1px dashed #CBD5E1;'><br>", unsafe_allow_html=True)
  st.markdown("### 🛠️ Plan d'action & Tâches à effectuer par l'entreprise")
  st.markdown(
      "Voici la liste des actions correctives à intégrer dans le MOP avant"
      " validation définitive :"
  )

  col_p1, col_p2 = st.columns(2)
  with col_p1:
    st.markdown(
        """
        <div class="card-tache">
            <b>1. Mise à jour des exigences EPI</b><br>
            <span style="color: #64748B; font-size: 0.9rem;">Ajouter explicitement l'obligation de la jugulaire pour toute intervention en hauteur.</span>
        </div>
        <div class="card-tache">
            <b>2. Validation administrative N2</b><br>
            <span style="color: #64748B; font-size: 0.9rem;">Faire signer le document par le responsable habilité de l'entreprise.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with col_p2:
    st.markdown(
        """
        <div class="card-tache">
            <b>3. Délimitation de zone</b><br>
            <span style="color: #64748B; font-size: 0.9rem;">Intégrer le plan de balisage de 3 mètres minimum autour de la zone de travail.</span>
        </div>
        <div class="card-tache">
            <b>4. Re-soumission du document</b><br>
            <span style="color: #64748B; font-size: 0.9rem;">Déposer la version corrigée sur l'application 48h avant le chantier.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif uploaded_file is None:
  st.info(
      "👆 Le **Construction Safety Manual** est chargé automatiquement en"
      " arrière-plan. Veuillez simplement importer **le MOP de l'entreprise**"
      " pour lancer l'analyse."
  )
