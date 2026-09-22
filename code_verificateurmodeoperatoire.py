import os
import re
import pypdf
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
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
            background: linear-gradient(90deg, #021530 0%, #0906c7 100%);
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

# --- FONCTION ROBUSTE DE RECHERCHE DE LOGO ---
def find_logo(base_name):
    if os.path.exists(base_name):
        return base_name
    for ext in [".svg.webp", ".webp", ".jpg", ".png", ".jpeg"]:
        path = base_name + ext
        if os.path.exists(path):
            return path
    return None

# --- EN-TÊTE AVEC LE LOGO P&G ET LE TITRE ---
header_col1, header_col2 = st.columns([1, 6], gap="medium")

with header_col1:
  logo_path = find_logo("Procter_&_Gamble_logo") or find_logo("P&G_Logo")
  if logo_path and os.path.exists(logo_path):
    st.image(logo_path, width=110)
  else:
    st.markdown("### ✅")

with header_col2:
  st.markdown(
      """
        <div class="pg-header" style="margin-bottom: 0px; padding: 15px 25px;">
            <h1 style="color: white; margin: 0; font-size: 1.8rem;">P&G Amiens | Assistant Sécurité Construction</h1>
            <p style="font-size: 1rem; margin: 0; opacity: 0.9;">Plateforme intelligente de pré-validation des modes opératoires et JSA</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# --- CHARGEMENT AUTOMATIQUE DU MANUEL P&G DEPUIS LE DÉPÔT ---
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
st.markdown("### 📂 Document de l'entreprise extérieure à auditer")
uploaded_file = st.file_uploader(
    "Glissez le mode opératoire (MOP) ou la JSA au format PDF", type=["pdf"]
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
    score_tech = score_technique  # Alias sécurisé

    # Définition de la variable globale des manquants
    tous_les_manquants = admin_manquants + tech_manquants

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
            suggestions_contexte.append("⚠️ Outil (Meuleuse) : L'usage d'une meuleuse génère des étincelles ; le rattacher obligatoirement aux exigences des travaux par point chaud (extincteur à proximité, bâche ignifugée).")

    if "pirl" in text_mop_lower or "plateforme" in text_mop_lower:
        suggestions_contexte.append("ℹ️ Équipement hauteur (PIRL) : Utilisation d'une PIRL détectée. Parfait, pas besoin de prévoir de ligne de vie ou de harnais si la PIRL dispose de garde-corps intégrés conformes, mais vérifier sa stabilisation et son freinage.")
    elif "hauteur" in text_mop_lower and not any(w in text_mop_lower for w in ["pirl", "nacelle", "échafaudage"]):
        suggestions_contexte.append("⚠️ Travaux en hauteur : Travail en hauteur mentionné sans préciser explicitement le moyen d'accès sécurisé (PIRL, échafaudage, PEMP) ni les mesures antichute.")

    if "chimique" in text_mop_lower or "produit" in text_mop_lower:
        suggestions_contexte.append("ℹ️ Produits chimiques : S'assurer que les fiches de données de sécurité (FDS) associées sont jointes au dossier et que les EPI adaptés (gants spécifiques, lunettes, tablier) sont notifiés.")

    score_global = int((score_admin + score_technique) / 2)


    def get_color_badge(score):
      if score >= 85:
        return "#10B981"
      elif score >= 65:
        return "#F59E0B"
      else:
        return "#EF4444"

    color_global = get_color_badge(score_global)
    color_admin = get_color_badge(score_admin)
    color_tech = get_color_badge(score_technique)

    st.markdown("---")

    # --- BANNIÈRE DE CONFORMITÉ EXPLICITE SANS FOURCHETTE ---
    if score_global < 65:
        st.markdown('<div class="banner-non-conforme">❌ Mode opératoire non conforme aux attentes P&G</div>', unsafe_allow_html=True)
    elif score_global < 85:
        st.markdown('<div class="banner-non-conforme" style="background-color: #FEF3C7; color: #B45309; border-left-color: #F59E0B;">⚠️ Mode opératoire partiellement conforme aux attentes P&G</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner-conforme">✅ Mode opératoire conforme aux attentes P&G sous réserve de validation d\'un casque rouge</div>', unsafe_allow_html=True)

    # --- SECTION VISUELLE : JAUGE & SYNTHÈSE ---
    col_gauge, col_info = st.columns([1.1, 1.9], gap="large")

    with col_gauge:
      st.markdown("### 📊 Taux de conformité global")

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
                      {'range': [0, 65], 'color': '#EF4444'},
                      {'range': [65, 85], 'color': '#F59E0B'},
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
            "**Statut : Conforme sous réserve** — Conforme aux attentes P&G sous réserve de validation d'un casque rouge."
        )
      elif score_global >= 65:
        st.warning(
            "**Statut : Partiellement conforme** — Partiellement conforme aux attentes P&G."
        )
      else:
        st.error(
            "**Statut : Non conforme** — Non conforme aux attentes P&G."
        )

      st.markdown(
          f"""
            * **Score administratif & formel :** <span style="color:{color_admin}; font-weight:bold; font-size:1.1rem;">{score_admin}%</span>
            * **Score technique & mise en forme :** <span style="color:{color_tech}; font-weight:bold; font-size:1.1rem;">{score_tech}%</span>
            * ⏱️ *Rappel P&G : Validation requise 48h avant le début des travaux.*
            """,
          unsafe_allow_html=True,
      )

    st.markdown(
        "<br><hr style='border: 2px solid #0B2341;'><br>",
        unsafe_allow_html=True,
    )

    # --- ANALYSE DÉTAILLÉE PAR PHASE ---
    st.markdown("## 🔍 Analyse détaillée par phase")
    tab1, tab2 = st.tabs(
        [
            "📋 Phase 1 : Vérification administrative",
            "⚙️ Phase 2 : Contenu technique & Tâches à haut risque",
        ]
    )

    with tab1:
      st.markdown("#### Conformité administrative du dossier")
      col_a1, col_a2 = st.columns(2)
      with col_a1:
        st.markdown("##### ✅ Éléments validés")
        if admin_valides:
          for el in admin_valides:
            st.markdown(f"- {el}")
        else:
          st.markdown("- Aucun critère validé.")
      with col_a2:
        st.markdown("##### ❌ Éléments manquants (À compléter)")
        if admin_manquants:
          for el in admin_manquants:
            st.markdown(f"- **{el}** : Point manquant dans le MOP.")
        else:
          st.markdown("- Tous les points administratifs requis sont présents !")

    with tab2:
      st.markdown("#### Conformité technique & structuration")
      col_t1, col_t2 = st.columns(2)
      with col_t1:
        st.markdown("##### ✅ Éléments validés")
        if tech_valides:
          for el in tech_valides:
            st.markdown(f"- {el}")
        else:
          st.markdown("- Aucun critère technique validé.")
      with col_t2:
        st.markdown("##### ❌ Éléments manquants (À compléter)")
        if tech_manquants:
          for el in tech_manquants:
            st.markdown(f"- **{el}** : Structure à revoir.")
        else:
          st.markdown("- Structure technique validée.")

      # --- ENCART DÉDIÉ AUX TÂCHES À HAUT RISQUE ---
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(
          "#### 🚨 Détection des tâches à haut risque (Standards P&G)"
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
                        <b>Activité à haut risque détectée :</b> {tache} <br>
                        <span style="font-size:0.85rem; color:#7F1D1D;">Vérifier l'adéquation des permis de travail et consignes spécifiques (LOTO, point chaud, etc.).</span>
                    </div>
                    """,
              unsafe_allow_html=True,
          )
      else:
        st.info(
            "Aucune tâche à haut risque majeure détectée par mots-clés dans"
            " ce texte."
        )

      if suggestions_contexte:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 💡 Suggestions de sécurité contextuelles (Outils & EPI)")
        for sug in suggestions_contexte:
            st.markdown(f"- {sug}")

    # --- LISTE DÉTAILLÉE DES ÉLÉMENTS À COMPLÉTER ET PISTES D'AMÉLIORATION ---
    st.markdown(
        "<br><hr style='border: 2px solid #0B2341;'><br>",
        unsafe_allow_html=True,
    )
    st.markdown("### 🛠️ Liste détaillée des éléments à compléter & suggestions")
    st.markdown(
        "Voici le détail des points à rectifier et les pistes"
        " d'amélioration de la sécurité pour rendre le MOP conforme :"
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
                st.markdown(f"- **{item}** : Structurer sous forme de tableau détaillé.")
        else:
            st.markdown("- Structure technique conforme.")

      with col_p2:
        st.markdown("#### 🛡️ Recommandations & suggestions sécurité sur-mesure :")
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
          .replace("✅", "")
          .replace("❌", "")
          .replace("ℹ️", "")
      )

    # --- CONVERSION DES IMAGES WEBP/SVG POUR FPDF ---
    def get_fpdf_image(path):
        if not path or not os.path.exists(path):
            return None
        if path.lower().endswith(('.webp', '.svg.webp', '.svg')):
            try:
                img = Image.open(path).convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                tmp_path = path + ".png"
                background.save(tmp_path, "PNG")
                return tmp_path
            except Exception:
                return path
        return path

    # --- CLASSE RAPPORT PDF AVEC WRAPPER SÉCURISÉ POUR LES RECTANGLES ARRONDIS ---
    class PDFReport(FPDF):
      def rounded_rect(self, x, y, w, h, r, style='D'):
          try:
              super().rounded_rect(x, y, w, h, r, style)
          except Exception:
              self.rect(x, y, w, h, style)

      def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, clean_pdf_text(f"Page {self.page_no()} | Site P&G Amiens - Validation requise 48h avant intervention"), 0, 0, "C")

    def create_pdf():
      pdf = PDFReport()
      pdf.add_page()
      
      # 1. LOGO P&G (proportionnel sans l'étirer) + TITRE AVEC DÉGRADÉ SIMULÉ & COINS ARRONDIS
      pg_logo_file = find_logo("Procter_&_Gamble_logo") or find_logo("P&G_Logo")
      converted_pg_logo = get_fpdf_image(pg_logo_file)
      
      logo_w, logo_h = 24, 20
      if converted_pg_logo and os.path.exists(converted_pg_logo):
          try:
              with Image.open(converted_pg_logo) as im:
                  orig_w, orig_h = im.size
                  aspect = orig_w / orig_h
                  logo_w = 20 * aspect
                  if logo_w > 26:
                      logo_w = 26
                      logo_h = 26 / aspect
              pdf.image(converted_pg_logo, x=10, y=10, w=logo_w, h=logo_h)
          except Exception:
              pass

      # Titre avec dégradé simulé (bandes de dégradé de #021530 à #0906c7) et coins arrondis (r=3)
      pdf.set_draw_color(2, 21, 48)
      pdf.rounded_rect(38, 10, 162, 20, 3, 'DF')
      
      # Simulation simple d'un dégradé horizontal sur le rectangle de titre
      r1, g1, b1 = 2, 21, 48
      r2, g2, b2 = 9, 6, 199
      steps = 30
      w_step = 162 / steps
      for i in range(steps):
          curr_r = int(r1 + (r2 - r1) * (i / steps))
          curr_g = int(g1 + (g2 - g1) * (i / steps))
          curr_b = int(b1 + (b2 - b1) * (i / steps))
          pdf.set_fill_color(curr_r, curr_g, curr_b)
          pdf.rect(38 + i * w_step, 10, w_step + 0.2, 20, 'F')

      pdf.set_xy(42, 13)
      pdf.set_font("helvetica", "B", 11)
      pdf.set_text_color(255, 255, 255)
      pdf.cell(154, 5, clean_pdf_text("Rapport de l'analyse du mode opératoire"), 0, 1, "L")

      pdf.set_xy(42, 19)
      pdf.set_font("helvetica", "", 8.5)
      pdf.set_text_color(220, 230, 242)
      pdf.cell(154, 5, clean_pdf_text("P&G Amiens | Assistant sécurité construction"), 0, 1, "L")

      pdf.set_y(34)
      
      # 2. DÉTERMINATION DU NIVEAU DE CONFORMITÉ & LOGO ASSOCIÉ
      if score_global < 65:
          niveau = "rouge"
          statut_msg = "NON CONFORME AUX ATTENTES P&G"
          logo_status_name = "Logo Non conforme rouge"
          bg_color = (254, 226, 226)
          border_color = (239, 68, 68)
          text_color = (153, 27, 27)
      elif score_global < 85:
          niveau = "orange"
          statut_msg = "PARTIELLEMENT CONFORME AUX ATTENTES P&G"
          logo_status_name = "Logo partiellement conforme orange"
          bg_color = (254, 243, 199)
          border_color = (245, 158, 11)
          text_color = (180, 83, 9)
      else:
          niveau = "vert"
          statut_msg = "CONFORME AUX ATTENTES P&G SOUS RÉSERVE DE VALIDATION D'UN CASQUE ROUGE"
          logo_status_name = "Logo conforme vert"
          bg_color = (209, 250, 229)
          border_color = (16, 185, 129)
          text_color = (6, 95, 70)

      # Affichage du logo de statut juste à côté du bandeau de conformité (mêmes dimensions et longueur que le bandeau phase = 190 mm)
      current_y = pdf.get_y()
      logo_path_status = find_logo(logo_status_name)
      converted_status_logo = get_fpdf_image(logo_path_status)
      logo_w = 12
      logo_h = 12
      banner_x = 24
      banner_w = 176
      banner_h = 12
      
      if converted_status_logo and os.path.exists(converted_status_logo):
          try:
              pdf.image(converted_status_logo, x=10, y=current_y, w=logo_w, h=logo_h)
          except Exception:
              pass
      
      pdf.set_fill_color(*bg_color)
      pdf.set_draw_color(*border_color)
      pdf.rounded_rect(banner_x, current_y, banner_w, banner_h, 2, 'DF')
      
      if niveau == "vert":
          prefix = "CONFORME AUX ATTENTES P&G SOUS RÉSERVE DE VALIDATION D'UN CASQUE ROUGE"
          pdf.set_font("helvetica", "B", 7)
          width_text = pdf.get_string_width(prefix)
          casque_logo_path = find_logo("Logo casque rouge")
          converted_casque_logo = get_fpdf_image(casque_logo_path)
          img_w = 4 if converted_casque_logo else 0
          total_w = width_text + (img_w + 2 if img_w else 0)
          start_x = banner_x + (banner_w - total_w) / 2
          
          pdf.set_xy(start_x, current_y + 4)
          pdf.set_text_color(*text_color)
          pdf.write(4, clean_pdf_text(prefix))
          
          if converted_casque_logo and os.path.exists(converted_casque_logo):
              try:
                  pdf.image(converted_casque_logo, x=pdf.get_x() + 1, y=current_y + 3.5, h=3.5)
              except Exception:
                  pass
      else:
          pdf.set_xy(banner_x, current_y + 3)
          pdf.set_font("helvetica", "B", 8)
          pdf.set_text_color(*text_color)
          pdf.multi_cell(banner_w, 4, clean_pdf_text(statut_msg), 0, 'C')
          
      pdf.set_y(current_y + max(logo_h, banner_h) + 4)

      # 3. CARTE TABLEAU DE BORD (coins arrondis)
      card_y = pdf.get_y()
      pdf.set_fill_color(248, 249, 250)
      pdf.set_draw_color(210, 215, 222)
      pdf.rounded_rect(10, card_y, 190, 24, 3, 'DF')
      
      # Taux de conformité à gauche
      pdf.set_xy(12, card_y + 2)
      pdf.set_font("helvetica", "B", 8)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(75, 4, clean_pdf_text("TAUX DE CONFORMITÉ"), 0, 1, "C")
      
      bar_x = 18
      bar_y = card_y + 11
      bar_w = 60
      bar_h = 5
      pdf.set_fill_color(220, 225, 230)
      pdf.rect(bar_x, bar_y, bar_w, bar_h, 'F')
      
      fill_w = max(2, int(bar_w * (score_global / 100)))
      if score_global >= 85:
          pdf.set_fill_color(16, 185, 129)
      elif score_global >= 65:
          pdf.set_fill_color(245, 158, 11)
      else:
          pdf.set_fill_color(239, 68, 68)
      pdf.rect(bar_x, bar_y, fill_w, bar_h, 'F')
      
      pdf.set_xy(12, card_y + 17)
      pdf.set_font("helvetica", "B", 9)
      pdf.cell(75, 4, clean_pdf_text(f"Global : {score_global}%"), 0, 1, "C")

      # Ligne verticale de séparation
      pdf.set_draw_color(200, 205, 215)
      pdf.set_line_width(0.5)
      pdf.line(90, card_y + 2, 90, card_y + 22)

      # Scores Administratif & Technique
      pdf.set_xy(95, card_y + 3)
      pdf.set_font("helvetica", "B", 9)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(100, 5, clean_pdf_text("Scores par domaine d'évaluation :"), 0, 1, "L")
      
      pdf.set_x(95)
      pdf.set_font("helvetica", "", 8.5)
      pdf.set_text_color(60, 60, 60)
      pdf.cell(35, 5, clean_pdf_text("- Administratif :"), 0, 0, "L")
      pdf.set_font("helvetica", "B", 9)
      if score_admin >= 85:
          pdf.set_text_color(16, 185, 129)
      elif score_admin >= 65:
          pdf.set_text_color(245, 158, 11)
      else:
          pdf.set_text_color(239, 68, 68)
      pdf.cell(50, 5, clean_pdf_text(f"{score_admin}%"), 0, 1, "L")

      pdf.set_xy(95, card_y + 13)
      pdf.set_font("helvetica", "", 8.5)
      pdf.set_text_color(60, 60, 60)
      pdf.cell(35, 5, clean_pdf_text("- Technique :"), 0, 0, "L")
      pdf.set_font("helvetica", "B", 9)
      if score_technique >= 85:
          pdf.set_text_color(16, 185, 129)
      elif score_technique >= 65:
          pdf.set_text_color(245, 158, 11)
      else:
          pdf.set_text_color(239, 68, 68)
      pdf.cell(50, 5, clean_pdf_text(f"{score_technique}%"), 0, 1, "L")

      pdf.set_y(card_y + 28)

      # 4. BANDEAU BLEU : "ANALYSE DÉTAILLÉE PAR PHASE" (coins arrondis)
      pdf.set_fill_color(11, 35, 65)
      pdf.set_draw_color(11, 35, 65)
      pdf.rounded_rect(10, pdf.get_y(), 190, 7, 2, 'DF')
      pdf.set_xy(12, pdf.get_y() + 1)
      pdf.set_font("helvetica", "B", 9.5)
      pdf.set_text_color(255, 255, 255)
      pdf.cell(186, 5, clean_pdf_text("ANALYSE DÉTAILLÉE PAR PHASE"), 0, 1, "L")
      pdf.ln(3)

      def draw_phase_card(title, val_list, manq_list):
          pdf.set_font("helvetica", "B", 9)
          pdf.set_text_color(29, 78, 216)
          pdf.cell(190, 5, clean_pdf_text(title), 0, 1)
          
          start_y = pdf.get_y()
          pdf.set_fill_color(255, 255, 255)
          pdf.set_draw_color(210, 215, 222)
          
          lines_count = 1 + len(val_list) + len(manq_list)
          box_height = max(16, lines_count * 5 + 4)
          
          if pdf.get_y() + box_height > 275:
              pdf.add_page()
              start_y = pdf.get_y()
          
          pdf.rounded_rect(10, start_y, 190, box_height, 3, 'DF')
          pdf.set_xy(13, start_y + 2)
          
          pdf.set_font("helvetica", "B", 8)
          pdf.set_text_color(16, 185, 129)
          pdf.cell(184, 4, clean_pdf_text("Éléments validés :"), 0, 1)
          pdf.set_font("helvetica", "", 8)
          pdf.set_text_color(0, 0, 0)
          if val_list:
              for item in val_list:
                  pdf.set_x(15)
                  pdf.multi_cell(180, 4, clean_pdf_text(f"- {item}"))
          else:
              pdf.set_x(15)
              pdf.multi_cell(180, 4, clean_pdf_text("- Aucun élément validé."))
              
          pdf.set_xy(13, pdf.get_y() + 1)
          pdf.set_font("helvetica", "B", 8)
          pdf.set_text_color(239, 68, 68)
          pdf.cell(184, 4, clean_pdf_text("Éléments manquants :"), 0, 1)
          pdf.set_font("helvetica", "", 8)
          pdf.set_text_color(0, 0, 0)
          if manq_list:
              for item in manq_list:
                  pdf.set_x(15)
                  pdf.set_text_color(239, 68, 68)
                  pdf.cell(4, 4, clean_pdf_text("X"), 0, 0)
                  pdf.set_text_color(0, 0, 0)
                  pdf.multi_cell(176, 4, clean_pdf_text(f" {item}"))
          else:
              pdf.set_x(15)
              pdf.multi_cell(180, 4, clean_pdf_text("- Tous les points requis sont présents !"))
              
          pdf.set_y(start_y + box_height + 3)

      draw_phase_card("Phase 1 : Vérification administrative & formelle", admin_valides, admin_manquants)
      draw_phase_card("Phase 2 : Contenu technique & structuration", tech_valides, tech_manquants)

      # 5. TÂCHES À HAUT RISQUE & SUGGESTIONS (coins arrondis)
      if taches_detectees or suggestions_contexte:
          pdf.set_font("helvetica", "B", 9.5)
          pdf.set_text_color(11, 35, 65)
          pdf.cell(190, 5, clean_pdf_text("Tâches à haut risque & suggestions de sécurité"), 0, 1)
          pdf.ln(1)
          
          start_y = pdf.get_y()
          pdf.set_fill_color(254, 242, 242)
          pdf.set_draw_color(239, 68, 68)
          
          box_h = max(20, 6 + (len(taches_detectees) + len(suggestions_contexte)) * 6)
          if pdf.get_y() + box_h > 275:
              pdf.add_page()
              start_y = pdf.get_y()

          pdf.rounded_rect(10, start_y, 190, box_h, 3, 'DF')
          pdf.set_xy(13, start_y + 2)
          
          pdf.set_font("helvetica", "B", 8.5)
          pdf.set_text_color(153, 27, 27)
          
          if taches_detectees:
              pdf.cell(184, 4, clean_pdf_text("Tâches à haut risque identifiées :"), 0, 1)
              pdf.set_font("helvetica", "", 8)
              for tache in taches_detectees:
                  pdf.set_x(15)
                  pdf.multi_cell(180, 4, clean_pdf_text(f"- {tache}"))
          
          for sug in suggestions_contexte:
              pdf.set_x(13)
              pdf.set_font("helvetica", "", 8)
              pdf.multi_cell(180, 4, clean_pdf_text(f"- {sug}"))
              
          pdf.set_y(start_y + box_h + 3)

      # 6. LISTE DÉTAILLÉE DES ÉLÉMENTS À COMPLÉTER & SUGGESTIONS (Encadré orange dynamique aux coins arrondis)
      pdf.set_font("helvetica", "B", 9.5)
      pdf.set_text_color(11, 35, 65)
      pdf.cell(190, 5, clean_pdf_text("Liste détaillée des éléments à compléter & suggestions"), 0, 1)
      pdf.ln(1)
      
      start_y = pdf.get_y()
      pdf.set_fill_color(255, 247, 237)
      pdf.set_draw_color(245, 158, 11)
      
      action_box_h = max(30, 10 + (len(admin_manquants) + len(tech_manquants) + 2) * 6)
      if pdf.get_y() + action_box_h > 275:
          pdf.add_page()
          start_y = pdf.get_y()

      pdf.rounded_rect(10, start_y, 190, action_box_h, 3, 'DF')
      pdf.set_xy(13, start_y + 2)
      
      pdf.set_font("helvetica", "B", 8)
      pdf.set_text_color(180, 83, 9)
      pdf.cell(184, 4, clean_pdf_text("Points administratifs et formels à rajouter :"), 0, 1)
      pdf.set_font("helvetica", "", 8)
      pdf.set_text_color(0, 0, 0)
      if admin_manquants:
          for item in admin_manquants:
              pdf.set_x(15)
              pdf.multi_cell(180, 4, clean_pdf_text(f"- {item} : Intégrer explicitement dans le MOP."))
      else:
          pdf.set_x(15)
          pdf.multi_cell(180, 4, clean_pdf_text("- Aucun manquement formel détecté."))

      pdf.set_xy(13, pdf.get_y() + 1)
      pdf.set_font("helvetica", "B", 8)
      pdf.set_text_color(180, 83, 9)
      pdf.cell(184, 4, clean_pdf_text("Améliorations techniques & sécurité :"), 0, 1)
      pdf.set_font("helvetica", "", 8)
      pdf.set_text_color(0, 0, 0)
      if tech_manquants:
          for item in tech_manquants:
              pdf.set_x(15)
              pdf.multi_cell(180, 4, clean_pdf_text(f"- {item} : Structurer sous forme de tableau (Phase, Moyens, Risques, Prévention)."))
      pdf.set_x(15)
      pdf.multi_cell(180, 4, clean_pdf_text("- Délai de soumission : Transmettre la version corrigée 48h avant intervention."))

      return bytes(pdf.output())

    # --- BOUTON DE TÉLÉCHARGEMENT DU RAPPORT PDF ---
    st.markdown("<br><hr style='border: 1px solid #0B2341;'><br>", unsafe_allow_html=True)
    st.markdown("### 📥 Télécharger le rapport d'audit officiel complet")
    st.markdown("Cliquez sur le bouton ci-dessous pour générer et télécharger le dossier d'analyse complet sous forme de **rapport PDF haut de gamme** :")

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
