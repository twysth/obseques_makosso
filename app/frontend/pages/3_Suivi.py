
import sys
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


# ============================================================
# COMPOSANTS COMMUNS
# ============================================================

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

from components import (
    afficher_signature,
    afficher_espace_admin,
    get_admin_headers,
    admin_connecte,
)


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = os.getenv(
    "OBSEQUES_API_URL",
    "http://127.0.0.1:5000"
).rstrip("/")


st.set_page_config(
    page_title="Suivi",
    page_icon="✅",
    layout="wide",
)


# ============================================================
# SESSION ADMINISTRATEUR
# ============================================================

if "admin_token" not in st.session_state:

    st.session_state.admin_token = None


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


def afficher_statut(statut):

    if statut == "A FAIRE":
        return "🔴 A FAIRE"

    if statut == "EN COURS":
        return "🟠 EN COURS"

    if statut == "TERMINE":
        return "🟢 TERMINE"

    return statut


def get_api(endpoint):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            headers=get_admin_headers(),
            timeout=10
        )

        try:

            resultat = response.json()

        except ValueError:

            resultat = {
                "error": response.text
            }

        if not response.ok:

            st.error(
                resultat.get(
                    "error",
                    f"Erreur HTTP {response.status_code}"
                )
            )

            return None

        return resultat

    except requests.exceptions.RequestException as erreur:

        st.error(
            "❌ Impossible de contacter l'API Flask : "
            f"{API_URL}"
        )

        return None


def post_api(endpoint, payload):

    try:

        response = requests.post(
            f"{API_URL}{endpoint}",
            json=payload,
            headers=get_admin_headers(),
            timeout=10
        )

        try:

            resultat = response.json()

        except ValueError:

            resultat = {
                "error": response.text
            }

        return response.ok, resultat

    except requests.exceptions.RequestException as erreur:

        return False, {
            "error": str(erreur)
        }


def put_api(endpoint, payload):

    try:

        response = requests.put(
            f"{API_URL}{endpoint}",
            json=payload,
            headers=get_admin_headers(),
            timeout=10
        )

        try:

            resultat = response.json()

        except ValueError:

            resultat = {
                "error": response.text
            }

        return response.ok, resultat

    except requests.exceptions.RequestException as erreur:

        return False, {
            "error": str(erreur)
        }


def delete_api(endpoint):

    try:

        response = requests.delete(
            f"{API_URL}{endpoint}",
            headers=get_admin_headers(),
            timeout=10
        )

        try:

            resultat = response.json()

        except ValueError:

            resultat = {
                "error": response.text
            }

        return response.ok, resultat

    except requests.exceptions.RequestException as erreur:

        return False, {
            "error": str(erreur)
        }


# ============================================================
# TITRE
# ============================================================

st.title(
    "✅ Suivi des préparatifs"
)

st.caption(
    "Suivi opérationnel et financier des obsèques"
)

st.divider()


# ============================================================
# ESPACE ADMINISTRATEUR CENTRALISE
# ============================================================

afficher_espace_admin()

st.divider()


# ============================================================
# VERIFICATION FLASK
# ============================================================

health = get_api(
    "/api/health"
)

if health is None:

    afficher_signature()

    st.stop()


# ============================================================
# RECUPERATION DES DONNEES
# ============================================================

categories = get_api(
    "/api/categories"
)

depenses = get_api(
    "/api/depenses"
)

taches = get_api(
    "/api/taches"
)


if categories is None:
    categories = []

if depenses is None:
    depenses = []

if taches is None:
    taches = []


df_categories = pd.DataFrame(
    categories
)

df_depenses = pd.DataFrame(
    depenses
)

df_taches = pd.DataFrame(
    taches
)


# ============================================================
# SUIVI FINANCIER
# ============================================================

st.header(
    "💰 Suivi financier"
)


if df_categories.empty:

    budget_previsionnel = 0.0

else:

    budget_previsionnel = float(
        pd.to_numeric(
            df_categories[
                "budget_previsionnel"
            ],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


if df_depenses.empty:

    montant_reel = 0.0

else:

    montant_reel = float(
        pd.to_numeric(
            df_depenses[
                "montant_reel"
            ],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


ecart_global = float(
    montant_reel
    - budget_previsionnel
)


if budget_previsionnel > 0:

    progression_financiere = (
        montant_reel
        / budget_previsionnel
    ) * 100

else:

    progression_financiere = 0.0


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "💰 Prévisionnel",
        format_fcfa(
            budget_previsionnel
        )
    )


with col2:

    st.metric(
        "💳 Réel",
        format_fcfa(
            montant_reel
        )
    )


with col3:

    st.metric(
        "📉 Écart",
        format_fcfa(
            ecart_global
        )
    )


with col4:

    st.metric(
        "📈 Réalisation",
        f"{progression_financiere:.1f} %"
    )


st.progress(
    min(
        max(
            progression_financiere / 100,
            0
        ),
        1
    )
)


# ============================================================
# REALISATION PAR CATEGORIE
# ============================================================

st.subheader(
    "📊 Réalisation financière par poste"
)


if df_depenses.empty:

    st.info(
        "Aucune dépense disponible."
    )

else:

    resume = (
        df_depenses
        .groupby(
            "categorie",
            as_index=False
        )
        .agg(
            previsionnel=(
                "montant_prevu",
                "sum"
            ),
            reel=(
                "montant_reel",
                "sum"
            ),
            ecart=(
                "ecart",
                "sum"
            )
        )
    )

    resume["progression"] = 0.0

    masque = (
        resume[
            "previsionnel"
        ] > 0
    )

    resume.loc[
        masque,
        "progression"
    ] = (
        resume.loc[
            masque,
            "reel"
        ]
        /
        resume.loc[
            masque,
            "previsionnel"
        ]
        * 100
    )

    resume[
        "progression"
    ] = (
        resume[
            "progression"
        ].clip(
            0,
            100
        )
    )

    tableau_financier = resume.copy()

    tableau_financier[
        "previsionnel"
    ] = tableau_financier[
        "previsionnel"
    ].map(format_fcfa)

    tableau_financier[
        "reel"
    ] = tableau_financier[
        "reel"
    ].map(format_fcfa)

    tableau_financier[
        "ecart"
    ] = tableau_financier[
        "ecart"
    ].map(format_fcfa)

    tableau_financier[
        "progression"
    ] = tableau_financier[
        "progression"
    ].map(
        lambda x: f"{x:.1f} %"
    )

    tableau_financier.columns = [
        "Catégorie",
        "Prévisionnel",
        "Réel",
        "Écart",
        "Progression"
    ]

    st.dataframe(
        tableau_financier,
        width="stretch",
        hide_index=True
    )


# ============================================================
# SUIVI OPERATIONNEL
# ============================================================

st.divider()

st.header(
    "✅ Suivi opérationnel"
)


if df_taches.empty:

    total_taches = 0
    terminees = 0
    en_cours = 0
    a_faire = 0
    progression_taches = 0.0

else:

    if "progression" not in df_taches.columns:

        df_taches[
            "progression"
        ] = 0.0

    if "statut" not in df_taches.columns:

        df_taches[
            "statut"
        ] = "A FAIRE"

    df_taches[
        "progression"
    ] = pd.to_numeric(
        df_taches[
            "progression"
        ],
        errors="coerce"
    ).fillna(0.0)

    total_taches = int(
        len(df_taches)
    )

    terminees = int(
        len(
            df_taches[
                df_taches[
                    "statut"
                ] == "TERMINE"
            ]
        )
    )

    en_cours = int(
        len(
            df_taches[
                df_taches[
                    "statut"
                ] == "EN COURS"
            ]
        )
    )

    a_faire = int(
        len(
            df_taches[
                df_taches[
                    "statut"
                ] == "A FAIRE"
            ]
        )
    )

    progression_taches = float(
        df_taches[
            "progression"
        ].mean()
    )


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "📋 Tâches",
        total_taches
    )


with col2:

    st.metric(
        "🟢 Terminées",
        terminees
    )


with col3:

    st.metric(
        "🟠 En cours",
        en_cours
    )


with col4:

    st.metric(
        "📈 Avancement",
        f"{progression_taches:.1f} %"
    )


st.progress(
    min(
        max(
            progression_taches / 100,
            0
        ),
        1
    )
)


# ============================================================
# TABLEAU DES TACHES
# ============================================================

st.subheader(
    "📋 Liste des tâches"
)


if df_taches.empty:

    st.info(
        "Aucune tâche n'est encore enregistrée."
    )

else:

    colonnes_taches = [
        "nom",
        "categorie",
        "progression",
        "statut",
        "date_prevue",
        "date_realisation"
    ]

    colonnes_disponibles = [
        colonne
        for colonne in colonnes_taches
        if colonne in df_taches.columns
    ]

    tableau_taches = df_taches[
        colonnes_disponibles
    ].copy()

    if "progression" in tableau_taches.columns:

        tableau_taches[
            "progression"
        ] = pd.to_numeric(
            tableau_taches[
                "progression"
            ],
            errors="coerce"
        ).fillna(0).map(
            lambda x: f"{x:.1f} %"
        )

    if "statut" in tableau_taches.columns:

        tableau_taches[
            "statut"
        ] = tableau_taches[
            "statut"
        ].apply(
            afficher_statut
        )

    renommage = {
        "nom": "Tâche",
        "categorie": "Catégorie",
        "progression": "Progression",
        "statut": "Statut",
        "date_prevue": "Date prévue",
        "date_realisation": "Date réalisation"
    }

    tableau_taches = tableau_taches.rename(
        columns=renommage
    )

    st.dataframe(
        tableau_taches,
        width="stretch",
        hide_index=True
    )


# ============================================================
# ADMINISTRATION DES TACHES
# ============================================================

if admin_connecte():

    st.divider()

    st.subheader(
        "🔐 Administration des tâches"
    )

    # ========================================================
    # AJOUTER UNE TACHE
    # ========================================================

    with st.expander(
        "➕ Ajouter une tâche",
        expanded=False
    ):

        categories_admin = {}

        if not df_categories.empty:

            categories_admin = {
                str(ligne["nom"]): int(
                    ligne["id"]
                )
                for _, ligne
                in df_categories.iterrows()
            }

        with st.form(
            "form_ajout_tache",
            clear_on_submit=True
        ):

            nom_tache = st.text_input(
                "Nom de la tâche"
            )

            description = st.text_area(
                "Description"
            )

            if categories_admin:

                categorie_nom = st.selectbox(
                    "Catégorie",
                    [
                        "Aucune"
                    ]
                    + list(
                        categories_admin.keys()
                    )
                )

            else:

                categorie_nom = "Aucune"

            date_prevue = st.date_input(
                "Date prévue",
                value=None
            )

            creer_tache = st.form_submit_button(
                "💾 Créer la tâche"
            )

        if creer_tache:

            if not nom_tache.strip():

                st.error(
                    "Le nom de la tâche est obligatoire."
                )

            else:

                categorie_id = None

                if categorie_nom != "Aucune":

                    categorie_id = int(
                        categories_admin[
                            categorie_nom
                        ]
                    )

                payload = {
                    "nom": str(
                        nom_tache.strip()
                    ),
                    "description": str(
                        description.strip()
                    ),
                    "categorie_id": categorie_id,
                    "date_prevue": (
                        str(date_prevue)
                        if date_prevue
                        else None
                    ),
                    "progression": 0.0
                }

                succes, resultat = post_api(
                    "/api/taches",
                    payload
                )

                if succes:

                    st.success(
                        "✅ Tâche créée."
                    )

                    st.rerun()

                else:

                    st.error(
                        resultat.get(
                            "error",
                            "Erreur lors de la création."
                        )
                    )


    # ========================================================
    # MODIFIER UNE TACHE
    # ========================================================

    if not df_taches.empty:

        with st.expander(
            "✏️ Modifier une tâche",
            expanded=False
        ):

            choix_taches = {}

            for _, ligne in df_taches.iterrows():

                nom_ligne = str(
                    ligne["nom"]
                )

                progression_ligne = float(
                    ligne["progression"]
                )

                choix_taches[
                    (
                        f"{nom_ligne} "
                        f"— {progression_ligne:.0f} %"
                    )
                ] = int(
                    ligne["id"]
                )

            selection = st.selectbox(
                "Tâche",
                list(
                    choix_taches.keys()
                ),
                key="selection_tache"
            )

            tache_id = int(
                choix_taches[
                    selection
                ]
            )

            ligne = df_taches[
                df_taches[
                    "id"
                ] == tache_id
            ].iloc[0]

            description_actuelle = str(
                ligne.get(
                    "description",
                    ""
                )
                or ""
            )

            progression_actuelle = float(
                ligne.get(
                    "progression",
                    0
                )
            )

            date_prevue_actuelle = (
                ligne.get(
                    "date_prevue",
                    None
                )
            )

            # ------------------------------------------------
            # CATEGORIE ACTUELLE
            # ------------------------------------------------

            categorie_id_actuelle = (
                ligne.get(
                    "categorie_id",
                    None
                )
            )

            if pd.notna(
                categorie_id_actuelle
            ):

                categorie_id_actuelle = int(
                    categorie_id_actuelle
                )

            else:

                categorie_id_actuelle = None


            with st.form(
                "form_modification_tache"
            ):

                nouvelle_description = st.text_area(
                    "Description",
                    value=description_actuelle
                )

                nouvelle_progression = st.number_input(
                    "Progression (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=progression_actuelle,
                    step=5.0
                )

                date_prevue_modification = st.text_input(
                    "Date prévue",
                    value=(
                        str(date_prevue_actuelle)
                        if date_prevue_actuelle
                        else ""
                    )
                )

                enregistrer = st.form_submit_button(
                    "💾 Enregistrer"
                )

            if enregistrer:

                payload = {
                    "nom": str(
                        ligne["nom"]
                    ),
                    "description": str(
                        nouvelle_description
                    ),
                    "categorie_id": (
                        categorie_id_actuelle
                    ),
                    "progression": float(
                        nouvelle_progression
                    ),
                    "date_prevue": (
                        str(
                            date_prevue_modification
                        ).strip()
                        if date_prevue_modification
                        else None
                    )
                }

                succes, resultat = put_api(
                    f"/api/taches/{tache_id}",
                    payload
                )

                if succes:

                    st.success(
                        "✅ Tâche mise à jour."
                    )

                    st.rerun()

                else:

                    st.error(
                        resultat.get(
                            "error",
                            "Erreur lors de la mise à jour."
                        )
                    )

        # ====================================================
        # SUPPRIMER UNE TACHE
        # ====================================================

        with st.expander(
            "🗑️ Supprimer une tâche",
            expanded=False
        ):

            choix_suppression = {}

            for _, ligne in df_taches.iterrows():

                label = (
                    f"{ligne['nom']} "
                    f"— {ligne['statut']}"
                )

                choix_suppression[
                    label
                ] = int(
                    ligne["id"]
                )

            selection_suppression = st.selectbox(
                "Tâche à supprimer",
                list(
                    choix_suppression.keys()
                ),
                key="selection_suppression_tache"
            )

            tache_id_suppression = int(
                choix_suppression[
                    selection_suppression
                ]
            )

            confirmation = st.checkbox(
                (
                    "⚠️ Je confirme la suppression "
                    "définitive de cette tâche."
                ),
                key="confirmation_suppression_tache"
            )

            supprimer = st.button(
                "🗑️ Supprimer définitivement",
                disabled=not confirmation,
                key="bouton_suppression_tache"
            )

            if supprimer:

                succes, resultat = delete_api(
                    f"/api/taches/{tache_id_suppression}"
                )

                if succes:

                    st.success(
                        "✅ Tâche supprimée."
                    )

                    st.rerun()

                else:

                    st.error(
                        resultat.get(
                            "error",
                            "Erreur lors de la suppression."
                        )
                    )


# ============================================================
# SIGNATURE
# ============================================================

afficher_signature()

