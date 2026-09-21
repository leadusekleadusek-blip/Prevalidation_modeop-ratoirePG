import os
import re
import pypdf
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF

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
        .card-hr {
            background-color: #FEF2F2;
            padding: 12px;
            border-radius: 8px;
            border-left: 5px solid #EF4444;
            margin-bottom: 8px;
        }
        .banner-conforme {
            background-color: #D1FAE5;
            color: #065F46;
            padding: 15px;
            border-radius: 8px;
            border-left: 6px solid #10B981;
            font-weight: bold;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 20px;
        }
        .banner-non-conforme {
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 15px;
            border-radius: 8px;
            border-left: 6px solid #EF4444;
            font-weight: bold;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 20px;
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
if not os.path.exists(MANUAL_PATH):
  for f in os.listdir("."):
    if ("safety" in f.lower() or "manuel" in f.lower()) and f.endswith(".pdf"):
      MANUAL_PATH = f
      break

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
      "❌ Fichier de référence 'python_constructionsafetymanuel.pdf' introuvable"
      " à la racine de votre dépôt."
  )

# --- SECTION DE DÉPÔT DU DOCUMENT À AUDITER ---
st.markdown("### 📂 Document de l'Entreprise Extérieure à auditer")
uploaded_file = st.file_uploader(
    "Glissez le Mode Opératoire (MOP) ou la JSA au format PDF", type=["pdf"]
)

if uploaded_file is not None and text_manual != "":
  with st.spinner("Analyse du mode opératoire en cours..."):
    reader_mop = pypdf.PdfReader(uploaded_file)
    text_mop = ""
    for page in reader_mop.pages:
      text_mop += page.extract_text() or ""

  if len(text_mop.strip()) < 20:
    st.error(
        "⚠️ Le document PDF importé semble être une image scannée ou ne"
        " contient pas de texte sélectionnable. Veuillez importer un PDF"
        " textuel."
    )
  else:
    st.success("✨ Document extrait avec succès !")

    text_mop_lower = text_mop.lower()

    # --- EXTRACTION AUTOMATIQUE DES MÉTADONNÉES DU MOP ---
    mop_lines = [line.strip() for line in text_mop.split('\n') if line.strip()]
    intervention_title = mop_lines[0] if mop_lines else "Mode Opératoire - Intervention Chantier"
    if len(intervention_title) > 65:
        intervention_title = intervention_title[:62] + "..."

    pdp_match = re.search(r'pdp[:\s\-]*([a-zA-Z0-9\-_]+)', text_mop_lower)
    pdp_ref = pdp_match.group(1).upper() if pdp_match else "Non specifie (A verifier)"

    # --- 1. CONTRÔLE DES POINTS ADMINISTRATIFS OBLIGATOIRES ---
    admin_criteres = {
        "Dates de travaux prévus": ["date", "planning", "calendrier", "du ", " au ", "période"],
        "Référence PDP": ["pdp", "plan de prévention", "plan de prevention"],
        "Project Manager": ["project manager", "chef de projet", "responsable de projet", "chargé d'affaire"],
        "Rédacteur avec N° de téléphone": ["rédacteur", "redacteur", "établi par", "contact", "tél", "telephone", "06", "07"],
        "Nom de l'entreprise & Logo": ["entreprise", "société", "societe", "sarl", "sas", "logo"],
        "Encart signature des intervenants": ["signature", "signé", "signataire", "visé par", "intervenants"],
    }
    
    admin_valides = [k for k, mots in admin_criteres.items() if any(m in text_mop_lower for m in mots)]
    admin_manquants = [k for k in admin_criteres.keys() if k not in admin_valides]
    score_admin = int((len(admin_valides) / len(admin_criteres)) * 100)

    # --- 2. CONTRÔLE TECHNIQUE & FORMAT ---
    tech_criteres = {
        "Format Tableau (Phase / Moyens / Risques / Prévention)": ["phase", "étape", "moyen", "matériel", "risque", "danger", "prévention", "mesure"],
        "Véracité & Chronologie des phases": ["chronologie", "séquence", "etape 1", "phase 1", "ensuite", "puis"],
        "Adéquation des EPI (casque, gants, lunettes...)": ["epi", "casque", "gant", "lunettes", "chaussures", "jugulaire", "protection"],
    }

    tech_valides = [k for k, mots in tech_criteres.items() if any(m in text_mop_lower for m in mots)]
    tech_manquants = [k for k in tech_criteres.keys() if k not in tech_valides]
    score_technique = int((len(tech_valides) / len(tech_criteres)) * 100)

    # --- 3. DÉTECTION DES 10 TÂCHES À HAUT RISQUE (Standards P&G) ---
    taches_haut_risque_ref = {
        "Travail en hauteur": ["hauteur", "échafaudage", "nacelle", "toiture", "pirl", "echelle"],
        "Consignation et isolation des énergies (LOTO)": ["consignation", "loto", "isolation", "cadenassage", "energie"],
        "Travail en espace confiné": ["espace confiné", "cuve", "silo", "regard", "espace confine"],
        "Travaux par point chaud (soudures, découpes)": ["point chaud", "soudure", "meulage", "découpe", "feu", "soudage"],
        "Manipulation de produits chimiques dangereux": ["chimique", "acide", "solvant", "produit dangereux", "fds", "fms"],
        "Opérations de levage et manutention lourde": ["levage", "grue", "palonnier", "manutention lourde", "charge"],
        "Circulation et conduite d'engins (chariots élévateurs)": ["chariot", "élévateur", "engin", "caces", "cariste", "circulation"],
        "Interventions sur installations électriques sous tension": ["électrique", "electrique", "sous tension", "armoire", "habilitation"],
        "Travaux d'excavation et creusement": ["excavation", "terrassement", "tranchée", "creusement", "sol"],
        "Interventions sur conduites / équipements sous pression ou température": ["pression", "vapeur", "haute température", "conduite"],
    }

    taches_detectees = [nom for nom, mots in taches_haut_risque_ref.items() if any(m in text_mop_lower for m in mots)]

    # --- 4. RAISONNEMENT CONTEXTUEL SUR LES OUTILS ET ÉQUIPEMENTS ---
    suggestions_contexte = []
    
    if "meuleuse" in text_mop_lower or "disqueuse" in text_mop_lower or "meuler" in text_mop_lower:
        if not any(w in text_mop_lower for w in ["écran facial", "visière", "lunettes"]):
            suggestions_contexte.append("⚠️ Outil (Meuleuse) : Utilisation de meuleuse détectée sans mention claire d'un écran facial / lunettes de protection et de gants anti-coupure adaptés.")
        if "point chaud" not in taches_detectees:
            suggestions_contexte.append("⚠️ Outil (Meuleuse) : L'usage d'une meuleuse génère des étincelles ; le rattacher obligatoirement aux exigences des Travaux par point chaud (extincteur à proximité, bâche ignifugée).")

    if "pirl" in text_mop_lower or "plateforme" in text_mop_lower:
        suggestions_contexte.append("ℹ️ Équipement hauteur (PIRL) : Utilisation d'une PIRL détectée. Parfait, pas besoin de prévoir de ligne de vie ou de harnais si la PIRL dispose de garde-corps intégrés conformes, mais vérifier sa stabilisation et son freinage.")
    elif "hauteur" in text_mop_lower and not any(w in text_mop_lower for w in ["pirl", "nacelle", "échafaudage"]):
        suggestions_contexte.append("⚠️ Travaux en hauteur : Travail en hauteur mentionné sans préciser explicitement le moyen d'accès sécurisé (PIRL, échafaudage, PEMP) ni les mesures antichute.")

    if "chimique" in text_mop_lower or "produit" in text_mop_lower:
        suggestions_contexte.append("ℹ️ Produits chimiques : S'assurer que les Fiches de Données de Sécurité (FDS) associées sont jointes au dossier et que les EPI adaptés (gants spécifiques, lunettes, tablier) sont notifiés.")

    score_global = int((score_admin + score_technique) / 2)


    def get_color_badge(score):
      if score >= 85:
        return "#10B981"
      elif score >= 50:
        return "#F59E0B"
      else:
        return "#EF4444"

    color_global = get_color_badge(score_global)
    color_admin = get_color_badge(score_admin)
    color_tech = get_color_badge(score_technique)

    st.markdown("---")

    # --- BANNIÈRE DE CONFORMITÉ EXPLICITE ---
    tous_les_manquants = admin_manquants + tech_manquants
    est_conforme = (score_admin == 100 and score_technique >= 80 and len(tous_les_manquants) == 0)
    
    if est_conforme:
        st.markdown('<div class="banner-conforme">✅ Mode opératoire conforme aux attentes P&G</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner-non-conforme">❌ Mode opératoire non conforme - Éléments manquants ou bloquants</div>', unsafe_allow_html=True)

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
                      {'range': [50, 85], 'color': '#F59E0B'},
                      {'range': [85, 100], 'color': '#10B981'},
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
      if score_global >= 85:
        st.success(
            "**Statut : Favorable** — Le mode opératoire respecte les"
            " critères administratifs et techniques du site."
        )
      elif score_global >= 50:
        st.warning(
            "**Statut : En attente de corrections** — Des points obligatoires"
            " sont manquants ou incomplets."
        )
      else:
        st.error(
            "**Statut : Non-conforme / Bloquant** — Refonte nécessaire avant"
            " validation."
        )

      st.markdown(
          f"""
            * **Score Administratif & Formel :** <span style="color:{color_admin}; font-weight:bold; font-size:1.1rem;">{score_admin}%</span>
            * **Score Technique & Mise en forme :** <span style="color:{color_tech}; font-weight:bold; font-size:1.1rem;">{score_technique}%</span>
            * ⏱️ *Rappel P&G : Validation requise 48h avant le début des travaux.*
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
            "📋 Phase 1 : Vérification Administrative & Formelle",
            "⚙️ Phase 2 : Contenu Technique & Tâches à Haut Risque",
        ]
    )

    with tab1:
      st.markdown("#### Conformité Administrative du dossier")
      col_a1, col_a2 = st.columns(2)
      with col_a1:
        st.markdown("##### ✅ Éléments validés (Vert)")
        if admin_valides:
          for el in admin_valides:
            st.markdown(f"- ✅ {el}")
        else:
          st.markdown("- Aucun critère validé.")
      with col_a2:
        st.markdown("##### ❌ Éléments manquants (Rouge / À compléter)")
        if admin_manquants:
          for el in admin_manquants:
            st.markdown(f"- ❌ **{el}** : Point manquant dans le MOP.")
        else:
          st.markdown("- ✅ Tous les points administratifs requis sont présents !")

    with tab2:
      st.markdown("#### Conformité Technique & Structuration")
      col_t1, col_t2 = st.columns(2)
      with col_t1:
        st.markdown("##### ✅ Éléments validés (Vert)")
        if tech_valides:
          for el in tech_valides:
            st.markdown(f"- ✅ {el}")
        else:
          st.markdown("- Aucun critère technique validé.")
      with col_t2:
        st.markdown("##### ❌ Éléments manquants (Rouge / À compléter)")
        if tech_manquants:
          for el in tech_manquants:
            st.markdown(f"- ❌ **{el}** : Structure à revoir.")
        else:
          st.markdown("- ✅ Structure technique validée.")

      # --- ENCART DÉDIÉ AUX TÂCHES À HAUT RISQUE ---
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(
          "#### 🚨 Détection des Tâches à Haut Risque (Standards P&G)"
      )
      if taches_detectees:
        st.warning(
            f"Attention : **{len(taches_detectees)} tâche(s) à haut risque"
            f" identifiée(s)** dans ce mode opératoire."
        )
        for tache in taches_detectees:
          st.markdown(
              f"""
                    <div class="card-hr">
                        <b>⚠️ Activité à haut risque détectée :</b> {tache} <br>
                        <span style="font-size:0.85rem; color:#7F1D1D;">Vérifier l'adéquation des permis de travail et consignes spécifiques (LOTO, Point Chaud, etc.).</span>
                    </div>
                    """,
              unsafe_allow_html=True,
          )
      else:
        st.info(
            "✅ Aucune tâche à haut risque majeure détectée par mots-clés dans"
            " ce texte."
        )

      if suggestions_contexte:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 💡 Suggestions de Sécurité Contextuelles (Outils & EPI)")
        for sug in suggestions_contexte:
            st.markdown(f"- {sug}")

    # --- LISTE DÉTAILLÉE DES ÉLÉMENTS À COMPLÉTER ET PISTES D'AMÉLIORATION ---
    st.markdown(
        "<br><hr style='border: 2px solid #0B2341;'><br>",
        unsafe_allow_html=True,
    )
    st.markdown("### 🛠️ Liste Détaillée des Éléments à Compléter & Suggestions")
    st.markdown(
        "Voici le détail des points en **rouge** à rectifier et les pistes"
        " d'amélioration sécurité pour rendre le MOP conforme :"
    )

    if tous_les_manquants or suggestions_contexte or score_global < 100:
      col_p1, col_p2 = st.columns(2)
      with col_p1:
        st.markdown("#### ❌ Points administratifs et formels à rajouter :")
        if admin_manquants:
            for item in admin_manquants:
                st.markdown(f"- **{item}** : Intégrer cette information de manière explicite.")
        else:
            st.markdown("- Aucun manquement formel détecté.")
            
        st.markdown("#### ⚙️ Améliorations de structure technique :")
        if tech_manquants:
            for item in tech_manquants:
                st.markdown(f"- **{item}** : Structurer sous forme de tableau détaillé (Phase, Moyens, Risques, Prévention).")
        else:
            st.markdown("- Structure technique conforme.")

      with col_p2:
        st.markdown("#### 🛡️ Recommandations & Suggestions Sécurité sur-mesure :")
        if suggestions_contexte:
            for s in suggestions_contexte:
                st.markdown(f"- {s}")
        if len(taches_detectees) > 0:
            st.markdown(f"- **Permis requis :** Assurez-vous que les permis associés aux tâches identifiées ({', '.join(taches_detectees)}) sont formalisés.")
        st.markdown("- **Délai de soumission :** Transmettre la version corrigée au moins 48h avant le début des travaux sur le site P&G Amiens.")
    else:
      st.success(
          "🎉 Félicitations ! Le mode opératoire est complet et parfaitement"
          " aligné avec les exigences du Construction Safety Manual."
      )

    # --- FONCTION DE NETTOYAGE POUR PDF ---
    def clean_pdf_text(text):
      return (
          text.replace("é", "e")
          .replace("è", "e")
          .replace("ê", "e")
          .replace("à", "a")
          .replace("â", "a")
          .replace("ù", "u")
          .replace("î", "i")
          .replace("ï", "i")
          .replace("ô", "o")
          .replace("ç", "c")
          .replace("É", "E")
          .replace("Ê", "E")
          .replace("À", "A")
          .replace("⚠️", "[!] ")
          .replace("✅", "[OK] ")
          .replace("❌", "[X] ")
          .replace("ℹ️", "[INFO] ")
      )

    # --- GÉNÉRATION DU RAPPORT PDF FIDÈLE À L'APPLICATION ---
    class PDFReport(FPDF):
      def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, clean_pdf_text(f"Page {self.page_no()} | Validation requise 48h avant intervention - Site P&G Amiens"), 0, 0, "C")

    def create_pdf():
      pdf = PDFReport()
      pdf.add_page()
      
      # 1. BANDEAU BLEU TITRE (Similaire à l'application)
      pdf.set_fill_color(11, 35, 65) # Bleu P&G (#0B2341)
      pdf.rect(10, 10, 190, 22, style="F")
      
      if os.path.exists("P&G_Logo.svg.webp"):
          try:
              pdf.image("P&G_Logo.svg.webp", x=13, y=13, w=16)
          except Exception:
              pass

      pdf.set_xy(32, 14)
      pdf.set_font("helvetica", "B", 13)
      pdf.set_text_color(255, 255, 255)
      pdf.cell(165, 7, clean_pdf_text("Rapport de l'analyse du mode operatoire"), 0, 1, "L")
      
      pdf.set_xy(32, 21)
      pdf.set_font("helvetica", "", 9)
      pdf.set_text_color(220, 230, 242)
      pdf.cell(165, 5, clean_pdf_text("P&G Amiens | Assistant Securite Construction"), 0, 1, "L")
      
      pdf.set_y(38)
      
      # 2. SOUS-TITRE : TITRE INTERVENTION & PDP (En dehors du bandeau)
      pdf.set_font("helvetica", "B", 10)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(190, 6, clean_pdf_text(f"Titre Intervention : {intervention_title}"), 0, 1)
      pdf.set_font("helvetica", "", 9)
      pdf.set_text_color(80, 80, 80)
      pdf.cell(190, 5, clean_pdf_text(f"Reference PDP : {pdp_ref}"), 0, 1)
      pdf.ln(4)

      # 3. BANNIÈRE DE CONFORMITÉ & SYNTHÈSE
      pdf.set_font("helvetica", "B", 11)
      if est_conforme:
          pdf.set_fill_color(209, 250, 229) # Vert clair
          pdf.set_text_color(6, 95, 70)     # Vert foncé
          statut_msg = "[OK] MODE OPERATOIRE CONFORME AUX ATTENTES P&G"
      else:
          pdf.set_fill_color(254, 226, 226) # Rouge clair
          pdf.set_text_color(153, 27, 27)   # Rouge foncé
          statut_msg = "[X] MODE OPERATOIRE NON CONFORME - ELEMENTS MANQUANTS"
      
      pdf.rect(10, pdf.get_y(), 190, 10, style="F")
      pdf.cell(190, 10, clean_pdf_text(statut_msg), 0, 1, "C")
      pdf.ln(5)

      # Indicateur Global & Scores
      pdf.set_font("helvetica", "B", 10)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(190, 6, clean_pdf_text(f"Indice de Conformite Global : {score_global}%"), 0, 1)
      pdf.set_font("helvetica", "", 9)
      pdf.set_text_color(50, 50, 50)
      pdf.cell(190, 5, clean_pdf_text(f"- Score Administratif & Formel : {score_admin}%"), 0, 1)
      pdf.cell(190, 5, clean_pdf_text(f"- Score Technique & Mise en forme : {score_technique}%"), 0, 1)
      pdf.ln(6)

      # 4. TABLEAU : ANALYSE DETAILLEE PAR PHASE
      pdf.set_font("helvetica", "B", 11)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(190, 7, clean_pdf_text("Analyse DETAILLEE par Phase"), 0, 1, "L")
      
      # En-têtes du tableau
      pdf.set_font("helvetica", "B", 9)
      pdf.set_fill_color(11, 35, 65)
      pdf.set_text_color(255, 255, 255)
      pdf.cell(45, 7, clean_pdf_text("Phase / Domaine"), 1, 0, "C", True)
      pdf.cell(72, 7, clean_pdf_text("Elements Valides ([OK])"), 1, 0, "C", True)
      pdf.cell(73, 7, clean_pdf_text("Elements Manquants ([X])"), 1, 1, "C", True)

      # Lignes du tableau
      pdf.set_font("helvetica", "", 8.5)
      pdf.set_text_color(0, 0, 0)
      
      val_admin_txt = ", ".join(admin_valides) if admin_valides else "Aucun"
      manq_admin_txt = ", ".join(admin_manquants) if admin_manquants else "Aucun"
      val_tech_txt = ", ".join(tech_valides) if tech_valides else "Aucun"
      manq_tech_txt = ", ".join(tech_manquants) if tech_manquants else "Aucun"

      # Ligne 1 : Administrative
      pdf.cell(45, 12, clean_pdf_text("1. Admin. & Formel"), 1, 0, "C")
      pdf.cell(72, 12, clean_pdf_text(val_admin_txt[:100]), 1, 0, "L")
      pdf.cell(73, 12, clean_pdf_text(manq_admin_txt[:100]), 1, 1, "L")

      # Ligne 2 : Technique
      pdf.cell(45, 12, clean_pdf_text("2. Technique & MOP"), 1, 0, "C")
      pdf.cell(72, 12, clean_pdf_text(val_tech_txt[:100]), 1, 0, "L")
      pdf.cell(73, 12, clean_pdf_text(manq_tech_txt[:100]), 1, 1, "L")
      pdf.ln(6)

      # 5. TACHES A HAUT RISQUE & SUGGESTIONS CONTEXTUELLES
      pdf.set_font("helvetica", "B", 11)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(190, 7, clean_pdf_text("Taches a Haut Risque & Suggestions de Securite"), 0, 1, "L")
      pdf.set_font("helvetica", "", 9)
      pdf.set_text_color(0, 0, 0)

      if taches_detectees:
          pdf.multi_cell(190, 5, clean_pdf_text(f"[!] {len(taches_detectees)} tache(s) a haut risque identifiee(s) : " + ", ".join(taches_detectees)))
      else:
          pdf.multi_cell(190, 5, clean_pdf_text("[OK] Aucune activite a haut risque majeure detectee."))
      
      pdf.ln(3)
      if suggestions_contexte:
          for sug in suggestions_contexte:
              pdf.multi_cell(190, 5, clean_pdf_text(f"- {sug}"))
      else:
          pdf.multi_cell(190, 5, clean_pdf_text("- Aucune remarque particuliere sur les outils ou equipements."))
      pdf.ln(6)

      # 6. LISTE DETAILLEE DES ELEMENTS A COMPLETER & SUGGESTIONS
      pdf.set_font("helvetica", "B", 11)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(190, 7, clean_pdf_text("Liste DETAILLEE des Elements a Completer & Suggestions"), 0, 1, "L")
      
      pdf.set_font("helvetica", "B", 9)
      pdf.set_text_color(153, 27, 27)
      pdf.cell(190, 6, clean_pdf_text("Points administratifs et formels a rajouter :"), 0, 1)
      pdf.set_font("helvetica", "", 9)
      pdf.set_text_color(0, 0, 0)
      if admin_manquants:
          for item in admin_manquants:
              pdf.multi_cell(190, 5, clean_pdf_text(f"  - {item} : Integrer cette information de maniere explicite."))
      else:
          pdf.multi_cell(190, 5, clean_pdf_text("  - Aucun manquement formel detecte."))

      pdf.ln(3)
      pdf.set_font("helvetica", "B", 9)
      pdf.set_text_color(153, 27, 27)
      pdf.cell(190, 6, clean_pdf_text("Ameliorations de structure technique :"), 0, 1)
      pdf.set_font("helvetica", "", 9)
      pdf.set_text_color(0, 0, 0)
      if tech_manquants:
          for item in tech_manquants:
              pdf.multi_cell(190, 5, clean_pdf_text(f"  - {item} : Structurer sous forme de tableau detaille."))
      else:
          pdf.multi_cell(190, 5, clean_pdf_text("  - Structure technique conforme."))

      pdf.ln(3)
      pdf.set_font("helvetica", "B", 9)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(190, 6, clean_pdf_text("Recommandations & Suggestions Securite sur-mesure :"), 0, 1)
      pdf.set_font("helvetica", "", 9)
      pdf.set_text_color(0, 0, 0)
      if suggestions_contexte:
          for s in suggestions_contexte:
              pdf.multi_cell(190, 5, clean_pdf_text(f"  - {s}"))
      if taches_detectees:
          pdf.multi_cell(190, 5, clean_pdf_text(f"  - Permis requis : Assurez-vous que les permis associes aux taches identifiees sont formalises."))
      pdf.multi_cell(190, 5, clean_pdf_text("  - Delai de soumission : Transmettre la version corigee au moins 48h avant le debut des travaux sur le site P&G Amiens."))

      return bytes(pdf.output())

    # --- A LA FIN : BOUTON DE TÉLÉCHARGEMENT DU RAPPORT PDF ---
    st.markdown("<br><hr style='border: 1px solid #0B2341;'><br>", unsafe_allow_html=True)
    st.markdown("### 📥 Télécharger le Rapport d'Audit Officiel Complet")
    st.markdown("Cliquez sur le bouton ci-dessous pour générer et télécharger le dossier d'analyse complet reprenant l'intégralité des critères au format **PDF** professionnel :")

    pdf_bytes = create_pdf()

    st.download_button(
        label="📄 Générer et télécharger le rapport PDF complet",
        data=pdf_bytes,
        file_name="Rapport_Complet_Audit_MOP_PG_Amiens.pdf",
        mime="application/pdf",
        type="primary",
    )

elif uploaded_file is None:
  st.info(
      "👆 Le **Construction Safety Manual** est chargé automatiquement en"
      " arrière-plan. Veuillez simplement importer **le MOP de l'entreprise**"
      " pour lancer l'analyse complète."
  )
