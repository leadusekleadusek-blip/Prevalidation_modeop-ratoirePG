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
            padding: 20px 25px;
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

# --- EN-TÊTE AVEC LE LOGO P&G ET LE TITRE ---
header_col1, header_col2 = st.columns([1, 6], gap="medium")

with header_col1:
  logo_path = "P&G_Logo.svg.webp"
  if os.path.exists(logo_path):
    st.image(logo_path, width=110)
  else:
    st.markdown("### ✅")

with header_col2:
  st.markdown(
      """
        <div class="pg-header" style="margin-bottom: 0px; padding: 15px 25px;">
            <h1 style="color: white; margin: 0; font-size: 1.8rem;">P&G Amiens | Assistant Sécurité Construction</h1>
            <p style="font-size: 1rem; margin: 0; opacity: 0.9;">Plateforme intelligente de pré-validation des Modes Opératoires et JSA</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# --- CHARGEMENT AUTOMATIQUE DU MANUEL P&G DEPUIS LE REPO GITHUB ---
MANUAL_PATH = "python_constructionsafetymanuel.pdf"

text_manual = ""
if os.path.exists(MANUAL_PATH):
  try:
    reader_manual = pypdf.PdfReader(MANUAL_PATH)
    for page in reader_manual.pages:
      text_manual += page.extract_text() or ""
  except Exception as e:
    st.warning(f"⚠️ Impossible de lire le fichier '{MANUAL_PATH}'.")
else:
  st.error(
      f"❌ Fichier de référence introuvable : `{MANUAL_PATH}`. Veuillez vérifier"
      " qu'il est bien à la racine de votre dépôt."
  )

# --- SECTION DE DÉPÔT DU DOCUMENT À AUDITER ---
st.markdown("### 📂 Document de l'Entreprise Extérieure à auditer")
uploaded_file = st.file_uploader(
    "Glissez le Mode Opératoire (MOP) ou la JSA au format PDF", type=["pdf"]
)

if uploaded_file is not None and text_manual != "":
  with st.spinner(
      "🔄 Analyse croisée dynamique entre le Manuel P&G et le MOP..."
  ):
    # Lecture du MOP soumis
    reader_mop = pypdf.PdfReader(uploaded_file)
    text_mop = ""
    for page in reader_mop.pages:
      text_mop += page.extract_text() or ""

  # Vérification si le PDF est vide (ex: scan image)
  if len(text_mop.strip()) < 20:
    st.error(
        "⚠️ Le document PDF importé semble être une image scannée ou ne"
        " contient pas de texte sélectionnable. L'application ne peut pas lire"
        " le contenu (Score : 0%). Veuillez importer un PDF textuel."
    )
  else:
    st.success("✨ Analyse croisée terminée avec succès !")

    # --- CALCUL DYNAMIQUE DES SCORES ---
    text_mop_lower = text_mop.lower()

    # 1. Critères Administratifs élargis
    admin_criteres = {
        "Plan de Prévention / PDP": [
            "pdp",
            "plan de prevention",
            "prévention",
        ],
        "Dates de validité": ["date", "planning", "calendrier", "du ", " au "],
        "Signatures / Responsable": [
            "signature",
            "signé",
            "superviseur",
            "n2",
            "responsable",
        ],
        "Identification entreprise": [
            "entreprise",
            "société",
            "intervenant",
            "societe",
        ],
    }
    admin_valides = [
        k
        for k, mots in admin_criteres.items()
        if any(m in text_mop_lower for m in mots)
    ]
    score_admin = int((len(admin_valides) / len(admin_criteres)) * 100)

    # 2. Critères Techniques & Opérationnels élargis
    tech_criteres = {
        "Décomposition des tâches": ["tâche", "phase", "étape", "operation"],
        "Analyse des risques": ["risque", "chute", "danger", "prevention"],
        "EPI & Normes (ex: jugulaire)": [
            "jugulaire",
            "casque",
            "gant",
            "epi",
            "norme",
        ],
        "Balisage de zone": ["balisage", "périmètre", "zone", "sécurité", "3m"],
        "Gestion des tâches à haut risque": [
            "permis",
            "feu",
            "confiné",
            "consignation",
        ],
    }
    tech_valides = [
        k
        for k, mots in tech_criteres.items()
        if any(m in text_mop_lower for m in mots)
    ]
    score_technique = int((len(tech_valides) / len(tech_criteres)) * 100)

    # Score Global (Moyenne des deux)
    score_global = int((score_admin + score_technique) / 2)


    # Fonction couleur
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

    # --- SECTION VISUELLE : JAUGE & SYNTHÈSE ---
    col_gauge, col_info = st.columns([1.1, 1.9], gap="large")

    with col_gauge:
      st.markdown("### 📊 Indice de Conformité Global")

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
      if score_global >= 75:
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

      st.markdown(
          f"""
            * **Score Administratif :** <span style="color:{color_admin}; font-weight:bold; font-size:1.1rem;">{score_admin}%</span>
            * **Score Technique & Opérationnel :** <span style="color:{color_tech}; font-weight:bold; font-size:1.1rem;">{score_technique}%</span>
            * ⏱️ *Rappel : Validation requise 48h avant le début des travaux.*
            """,
          unsafe_allow_html=True,
      )

    st.markdown(
        "<br><hr style='border: 2px solid #0B2341;'><br>",
        unsafe_allow_html=True,
    )

    # --- ANALYSE DÉTAILLÉE PAR PHASE ---
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
        st.markdown("##### ✅ Éléments détectés")
        if admin_valides:
          for el in admin_valides:
            st.markdown(f"- {el}")
        else:
          st.markdown("- Aucun élément administratif clé détecté.")
      with col_a2:
        st.markdown("##### ⚠️ Points manquants ou non détectés")
        admin_manquants = [
            k for k in admin_criteres.keys() if k not in admin_valides
        ]
        if admin_manquants:
          for el in admin_manquants:
            st.markdown(f"- **{el}** : À préciser dans le document.")
        else:
          st.markdown("- Tous les critères administratifs sont présents !")

    with tab2:
      st.markdown("#### Conformité Technique & Opérationnelle")
      col_t1, col_t2 = st.columns(2)
      with col_t1:
        st.markdown("##### ✅ Éléments détectés")
        if tech_valides:
          for el in tech_valides:
            st.markdown(f"- {el}")
        else:
          st.markdown("- Aucun critère technique clé détecté.")
      with col_t2:
        st.markdown("##### ⚠️ Points manquants ou non détectés")
        tech_manquants = [
            k for k in tech_criteres.keys() if k not in tech_valides
        ]
        if tech_manquants:
          for el in tech_manquants:
            st.markdown(f"- **{el}** : Mention absente (Exigence P&G).")
        else:
          st.markdown("- Tous les critères techniques sont validés !")

    # --- PLAN D'ACTION ---
    st.markdown(
        "<br><hr style='border: 1px dashed #CBD5E1;'><br>",
        unsafe_allow_html=True,
    )
    st.markdown("### 🛠️ Plan d'action & Tâches à effectuer par l'entreprise")
    st.markdown("Voici les axes d'amélioration générés d'après l'analyse :")

    if score_global < 100:
      col_p1, col_p2 = st.columns(2)
      with col_p1:
        st.markdown(
            """
                <div class="card-tache">
                    <b>1. Compléter les sections manquantes</b><br>
                    <span style="color: #64748B; font-size: 0.9rem;">Reprendre les points signalés ci-dessus pour les expliciter dans le MOP.</span>
                </div>
                <div class="card-tache">
                    <b>2. Valider les exigences P&G</b><br>
                    <span style="color: #64748B; font-size: 0.9rem;">S'assurer que les consignes spécifiques du site (balisage, EPI) sont rédigées.</span>
                </div>
                """,
            unsafe_allow_html=True,
        )
      with col_p2:
        st.markdown(
            """
                <div class="card-tache">
                    <b>3. Validation des signatures</b><br>
                    <span style="color: #64748B; font-size: 0.9rem;">Vérifier la présence des noms et signatures du superviseur N2 et de l'entreprise.</span>
                </div>
                <div class="card-tache">
                    <b>4. Re-soumission du document</b><br>
                    <span style="color: #64748B; font-size: 0.9rem;">Déposer la version corrigée sur l'application 48h avant le chantier.</span>
                </div>
                """,
            unsafe_allow_html=True,
        )
    else:
      st.success(
          "🎉 Félicitations ! Le document remplit l'ensemble des critères"
          " contrôlés par rapport au manuel P&G."
      )

elif uploaded_file is None:
  st.info(
      "👆 Le **Construction Safety Manual** est chargé automatiquement en"
      " arrière-plan. Veuillez simplement importer **le MOP de l'entreprise**"
      " pour lancer l'analyse dynamique."
  )
