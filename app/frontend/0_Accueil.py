import sys
import os
from pathlib import Path
from datetime import date

import pandas as pd
import requests
import streamlit as st


# ============================================================
# COMPOSANT COMMUN
# ============================================================

sys.path.append(
    str(Path(__file__).resolve().parent)
)

from components import afficher_signature


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = os.getenv(
    "OBSEQUES_API_URL",
    "http://127.0.0.1:5000"
).rstrip("/")

DATE_OBSEQUES = date(
    2026,
    8,
    27
)

st.set_page_config(
    page_title="Obsèques MAKOSSO POATHY Jean Pierre",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .bloc-titre {
        text-align: center;
        padding: 10px 0 5px 0;
    }

    .bloc-sous-titre {
        text-align: center;
        color: #666666;
        margin-bottom: 25px;
    }

    .carte-info {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 10px;
    }

    .titre-module {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 5px;
    }

    .texte-module {
        color: #666666;
        font-size: 0.95rem;
    }

    .footer-accueil {
        text-align: center;
        color: #777777;
        margin-top: 35px;
        padding-top: 15px;
        border-top: 1px solid rgba(128,128,128,0.25);
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# OUTILS
# ============================================================

def format_fcfa(valeur):

    try:

        return (
            f"{float(valeur):,.0f} FCFA"
            .replace(",", " ")
        )

    except (
        TypeError,
        ValueError
    ):

        return "0 FCFA"


def get_api(endpoint):

    url = f"{API_URL}{endpoint}"

    for tentative in range(1, 4):

        try:

            response = requests.get(
                url,
                timeout=15
            )

            try:
                resultat = response.json()
            except ValueError:
                resultat = None

            if response.ok and resultat is not None:
                return resultat

        except requests.exceptions.RequestException:

            if tentative < 3:
                import time
                time.sleep(3)

    return None


# ============================================================
# EN-TÊTE
# ============================================================

st.markdown(
    """
    <div class="bloc-titre">
        <h1>🕊️ Obsèques de Feu MAKOSSO POATHY Jean Pierre</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="bloc-sous-titre">
        Application de suivi budgétaire, financier
        et opérationnel des obsèques
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATE DES OBSÈQUES
# ============================================================

jours_restants = (
    DATE_OBSEQUES
    - date.today()
).days


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "📅 Date des obsèques",
        DATE_OBSEQUES.strftime("%d/%m/%Y")
    )


with col2:

    if jours_restants > 0:

        st.metric(
            "⏳ Compte à rebours",
            f"J-{jours_restants}"
        )

    elif jours_restants == 0:

        st.metric(
            "⏳ Compte à rebours",
            "AUJOURD'HUI"
        )

    else:

        st.metric(
            "⏳ Situation",
            f"J+{abs(jours_restants)}"
        )


with col3:

    st.metric(
        "📍 Destination",
        "Mayumba"
    )


st.divider()


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

dashboard = get_api(
    "/api/dashboard"
)

cotisants = get_api(
    "/api/cotisants"
)

taches = get_api(
    "/api/taches"
)


# ============================================================
# INDICATEURS D'ACCUEIL
# ============================================================

budget_previsionnel = 0.0
montant_reel = 0.0
ecart = 0.0

total_cotisations = 0.0
total_verse = 0.0
total_reste = 0.0

nombre_taches = 0
taches_terminees = 0
avancement_taches = 0.0


if dashboard:

    budget_previsionnel = float(
        dashboard.get(
            "budget_previsionnel",
            0
        )
    )

    montant_reel = float(
        dashboard.get(
            "montant_reel",
            0
        )
    )

    ecart = float(
        dashboard.get(
            "ecart",
            0
        )
    )


if cotisants:

    df_cotisants = pd.DataFrame(
        cotisants
    )

    if not df_cotisants.empty:

        total_cotisations = float(
            pd.to_numeric(
                df_cotisants[
                    "montant_prevu"
                ],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

        total_verse = float(
            pd.to_numeric(
                df_cotisants[
                    "montant_verse"
                ],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

        total_reste = float(
            pd.to_numeric(
                df_cotisants[
                    "reste"
                ],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )


if taches:

    df_taches = pd.DataFrame(
        taches
    )

    if not df_taches.empty:

        nombre_taches = int(
            len(df_taches)
        )

        taches_terminees = int(
            len(
                df_taches[
                    df_taches[
                        "statut"
                    ] == "TERMINE"
                ]
            )
        )

        avancement_taches = float(
            pd.to_numeric(
                df_taches[
                    "progression"
                ],
                errors="coerce"
            )
            .fillna(0)
            .mean()
        )


# ============================================================
# RÉSUMÉ GÉNÉRAL
# ============================================================

st.header(
    "📊 Situation générale"
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "💰 Budget prévisionnel",
        format_fcfa(
            budget_previsionnel
        )
    )


with c2:

    st.metric(
        "💳 Dépenses réelles",
        format_fcfa(
            montant_reel
        )
    )


with c3:

    st.metric(
        "👥 Cotisations versées",
        format_fcfa(
            total_verse
        )
    )


with c4:

    st.metric(
        "✅ Tâches terminées",
        taches_terminees
    )


# ============================================================
# ÉTAT DU PROJET
# ============================================================

st.subheader(
    "📈 État global du projet"
)


c1, c2, c3 = st.columns(3)


with c1:

    if budget_previsionnel > 0:

        progression_budget = (
            montant_reel
            / budget_previsionnel
        ) * 100

    else:

        progression_budget = 0

    st.write(
        f"**Budget consommé : "
        f"{progression_budget:.1f} %**"
    )

    st.progress(
        min(
            max(
                progression_budget / 100,
                0
            ),
            1
        )
    )


with c2:

    if total_cotisations > 0:

        progression_cotisations = (
            total_verse
            / total_cotisations
        ) * 100

    else:

        progression_cotisations = 0

    st.write(
        f"**Collecte des cotisations : "
        f"{progression_cotisations:.1f} %**"
    )

    st.progress(
        min(
            max(
                progression_cotisations / 100,
                0
            ),
            1
        )
    )


with c3:

    st.write(
        f"**Préparatifs : "
        f"{avancement_taches:.1f} %**"
    )

    st.progress(
        min(
            max(
                avancement_taches / 100,
                0
            ),
            1
        )
    )


# ============================================================
# SITUATION BUDGÉTAIRE
# ============================================================

if ecart > 0:

    st.error(
        f"⚠️ Le budget présente actuellement "
        f"un dépassement de {format_fcfa(ecart)}."
    )

elif ecart < 0:

    st.success(
        f"✅ La dépense réelle reste inférieure "
        f"au prévisionnel de {format_fcfa(abs(ecart))}."
    )

else:

    st.info(
        "ℹ️ Les dépenses réelles correspondent "
        "exactement au budget prévisionnel."
    )


# ============================================================
# MODULES DE L'APPLICATION
# ============================================================

st.divider()

st.header(
    "🧭 Modules de l'application"
)


col1, col2 = st.columns(2)


with col1:

    st.markdown(
        """
        <div class="carte-info">

        <div class="titre-module">
        💰 Dépenses
        </div>

        <div class="texte-module">
        Consultation des postes budgétaires,
        dépenses prévues, dépenses réelles,
        écarts et progression.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="carte-info">

        <div class="titre-module">
        👥 Cotisations
        </div>

        <div class="texte-module">
        Gestion des cotisants, contributions,
        versements, soldes et reste à collecter.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="carte-info">

        <div class="titre-module">
        ✅ Suivi
        </div>

        <div class="texte-module">
        Gestion des tâches, progression,
        échéances et état des préparatifs.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        """
        <div class="carte-info">

        <div class="titre-module">
        📊 Tableau de bord
        </div>

        <div class="texte-module">
        Vision consolidée du budget,
        des dépenses, des cotisations
        et des préparatifs.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="carte-info">

        <div class="titre-module">
        📑 Reporting
        </div>

        <div class="texte-module">
        Synthèses détaillées, alertes
        et exports des données du dossier.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="carte-info">

        <div class="titre-module">
        🔐 Administration
        </div>

        <div class="texte-module">
        Les opérations sensibles sont
        protégées par authentification
        administrateur.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# INFORMATIONS DU DOSSIER
# ============================================================

st.divider()

st.header(
    "🕊️ Informations du dossier"
)


c1, c2 = st.columns(2)


with c1:

    st.write(
        "**Défunt :** "
        "MAKOSSO POATHY Jean Pierre"
    )

    st.write(
        "**Date des obsèques :** "
        "27 août 2026"
    )

    st.write(
        "**Lieu prévu :** "
        "Mayumba"
    )


with c2:

    st.write(
        "**Base de données :** "
        "SQLite"
    )

    st.write(
        "**API :** "
        "Flask"
    )

    st.write(
        "**Interface :** "
        "Streamlit"
    )


# ============================================================
# ÉTAT DU SERVEUR
# ============================================================

st.divider()

st.subheader(
    "🖥️ État de l'application"
)


health = get_api(
    "/api/health"
)


if health:

    if health.get(
        "status"
    ) == "ok":

        st.success(
            "🟢 Service Flask opérationnel — "
            "base de données connectée."
        )

    else:

        st.warning(
            "🟠 Le service Flask répond, "
            "mais la base de données nécessite une vérification."
        )

else:

    st.warning(
        "🟠 Le service Flask n'est pas actuellement accessible."
    )


# ============================================================
# PIED DE PAGE
# ============================================================

st.markdown(
    """
    <div class="footer-accueil">
        Application de suivi des obsèques —
        MAKOSSO POATHY Jean Pierre
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIGNATURE
# ============================================================

afficher_signature()