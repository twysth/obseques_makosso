
import sys
import os
from pathlib import Path

import requests
import pandas as pd
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
    page_title="Dépenses",
    page_icon="💰",
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


def get_api(endpoint):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            headers=get_admin_headers(),
            timeout=10,
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

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ Impossible de contacter l'API Flask : "
            f"{API_URL}"
        )

        st.stop()

    except requests.exceptions.RequestException as erreur:

        st.error(
            f"❌ Erreur de connexion à l'API : {erreur}"
        )

        st.stop()


def put_api(endpoint, payload):

    try:

        response = requests.put(
            f"{API_URL}{endpoint}",
            json=payload,
            headers=get_admin_headers(),
            timeout=10,
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
            timeout=10,
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
    "💰 Dépenses prévisionnelles et suivi réel"
)

st.caption(
    "Analyse des 10 grands postes budgétaires "
    "et saisie des dépenses réelles"
)

st.divider()


# ============================================================
# ESPACE ADMINISTRATEUR CENTRALISE
# ============================================================

afficher_espace_admin()

st.divider()


# ============================================================
# RECUPERATION DES CATEGORIES
# ============================================================

categories = get_api(
    "/api/categories"
)

if categories is None:

    afficher_signature()

    st.stop()


df_categories = pd.DataFrame(
    categories
)


if df_categories.empty:

    st.warning(
        "Aucune catégorie disponible."
    )

    afficher_signature()

    st.stop()


# ============================================================
# SELECTION CATEGORIE
# ============================================================

categorie_selectionnee = st.selectbox(
    "📂 Sélectionner un poste budgétaire",
    df_categories["nom"].tolist(),
)


# ============================================================
# INFORMATIONS CATEGORIE
# ============================================================

categorie = df_categories[
    df_categories["nom"]
    == categorie_selectionnee
].iloc[0]


budget_previsionnel = float(
    categorie[
        "budget_previsionnel"
    ]
)

budget_detaille = float(
    categorie[
        "budget_detaille"
    ]
)

budget_non_affecte = float(
    categorie[
        "budget_non_affecte"
    ]
)

statut_detail = categorie[
    "statut_detail"
]


# ============================================================
# CARTES
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "💰 Budget prévisionnel",
        format_fcfa(
            budget_previsionnel
        ),
    )


with col2:

    st.metric(
        "📋 Budget détaillé",
        format_fcfa(
            budget_detaille
        ),
    )


with col3:

    st.metric(
        "⚠️ Budget non affecté",
        format_fcfa(
            budget_non_affecte
        ),
    )


with col4:

    st.metric(
        "📌 Statut",
        statut_detail,
    )


# ============================================================
# NIVEAU DE DETAIL
# ============================================================

if budget_previsionnel > 0:

    progression_detail = (
        budget_detaille
        / budget_previsionnel
        * 100
    )

else:

    progression_detail = 0


st.subheader(
    "📊 Niveau de détail du budget"
)

st.progress(
    min(
        max(
            progression_detail / 100,
            0
        ),
        1
    )
)

st.write(
    f"Budget détaillé : "
    f"**{progression_detail:.1f} %**"
)


# ============================================================
# RECUPERATION DES DEPENSES
# ============================================================

depenses = get_api(
    "/api/depenses"
)

if depenses is None:

    afficher_signature()

    st.stop()


df_depenses = pd.DataFrame(
    depenses
)


if not df_depenses.empty:

    df_depenses = df_depenses[
        df_depenses[
            "categorie"
        ]
        == categorie_selectionnee
    ].copy()


# ============================================================
# REEL DE LA CATEGORIE
# ============================================================

if df_depenses.empty:

    total_reel_categorie = 0
    total_ecart_categorie = 0
    progression_categorie = 0

else:

    total_reel_categorie = (
        pd.to_numeric(
            df_depenses[
                "montant_reel"
            ],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    total_ecart_categorie = (
        pd.to_numeric(
            df_depenses[
                "ecart"
            ],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    if budget_previsionnel > 0:

        progression_categorie = (
            total_reel_categorie
            / budget_previsionnel
            * 100
        )

    else:

        progression_categorie = 0


st.subheader(
    "💳 Situation réelle du poste"
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Réel engagé",
        format_fcfa(
            total_reel_categorie
        )
    )


with col2:

    st.metric(
        "Écart",
        format_fcfa(
            total_ecart_categorie
        )
    )


with col3:

    st.metric(
        "Réalisation",
        f"{progression_categorie:.1f} %"
    )


# ============================================================
# TABLEAU DES DEPENSES
# ============================================================

st.subheader(
    f"📋 Dépenses — {categorie_selectionnee}"
)


if df_depenses.empty:

    st.info(
        "Aucune dépense détaillée pour cette catégorie."
    )

else:

    affichage = df_depenses[
        [
            "designation",
            "prix_unitaire_prevu",
            "quantite_prevue",
            "montant_prevu",
            "prix_unitaire_reel",
            "quantite_reelle",
            "montant_reel",
            "ecart",
            "progression",
            "statut",
        ]
    ].copy()


    affichage.columns = [
        "Désignation",
        "PU prévu",
        "Qté prévue",
        "Montant prévu",
        "PU réel",
        "Qté réelle",
        "Montant réel",
        "Écart",
        "Progression %",
        "Statut",
    ]


    st.dataframe(
        affichage,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# ADMINISTRATION DES DEPENSES
# ============================================================

if admin_connecte():

    st.divider()

    st.subheader(
        "🔐 Administration des dépenses"
    )


    if df_depenses.empty:

        st.info(
            "Aucune dépense détaillée à modifier "
            "dans cette catégorie."
        )

    else:

        # ====================================================
        # SELECTION DEPENSE
        # ====================================================

        choix_depenses = {}


        for _, ligne in df_depenses.iterrows():

            designation = str(
                ligne["designation"]
            )

            montant_prevu = float(
                ligne["montant_prevu"]
            )

            choix_depenses[
                (
                    f"{designation} "
                    f"— prévu : "
                    f"{format_fcfa(montant_prevu)}"
                )
            ] = int(
                ligne["id"]
            )


        selection = st.selectbox(
            "Sélectionner une dépense à mettre à jour",
            list(
                choix_depenses.keys()
            ),
            key="selection_depense"
        )


        depense_id = int(
            choix_depenses[
                selection
            ]
        )


        ligne_depense = df_depenses[
            df_depenses[
                "id"
            ] == depense_id
        ].iloc[0]


        # ====================================================
        # INFORMATIONS PREVISIONNELLES
        # ====================================================

        designation = str(
            ligne_depense[
                "designation"
            ]
        )


        montant_prevu_depense = float(
            ligne_depense[
                "montant_prevu"
            ]
        )


        quantite_prevue = float(
            ligne_depense[
                "quantite_prevue"
            ]
        )


        ancien_montant_reel = float(
            ligne_depense[
                "montant_reel"
            ]
        )


        ancienne_quantite_reelle = float(
            ligne_depense[
                "quantite_reelle"
            ]
        )


        st.markdown(
            f"### 🧾 {designation}"
        )


        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "Montant prévu",
                format_fcfa(
                    montant_prevu_depense
                )
            )


        with c2:

            st.metric(
                "Quantité prévue",
                f"{quantite_prevue:g}"
            )


        with c3:

            st.metric(
                "Montant réel actuel",
                format_fcfa(
                    ancien_montant_reel
                )
            )


        # ====================================================
        # FORMULAIRE REEL
        # ====================================================

        with st.form(
            "form_depense_reelle"
        ):

            st.write(
                "### ✏️ Saisie de la réalisation"
            )


            quantite_reelle = st.number_input(
                "Quantité réelle",
                min_value=0.0,
                value=ancienne_quantite_reelle,
                step=1.0,
            )


            montant_reel = st.number_input(
                "Montant réel payé",
                min_value=0.0,
                value=ancien_montant_reel,
                step=1000.0,
            )


            enregistrer = st.form_submit_button(
                "💾 Enregistrer la dépense réelle"
            )


        # ====================================================
        # CALCULS PREVISUELS
        # ====================================================

        if montant_prevu_depense > 0:

            progression_preview = (
                montant_reel
                / montant_prevu_depense
                * 100
            )

        else:

            progression_preview = 0


        if quantite_reelle > 0:

            prix_unitaire_reel_preview = (
                montant_reel
                / quantite_reelle
            )

        else:

            prix_unitaire_reel_preview = 0


        ecart_preview = (
            montant_reel
            - montant_prevu_depense
        )


        if montant_reel <= 0:

            statut_preview = "A FAIRE"

        elif progression_preview < 100:

            statut_preview = "EN COURS"

        else:

            statut_preview = "TERMINE"


        st.write(
            "### 👁️ Aperçu"
        )


        a1, a2, a3, a4 = st.columns(4)


        with a1:

            st.metric(
                "PU réel",
                format_fcfa(
                    prix_unitaire_reel_preview
                )
            )


        with a2:

            st.metric(
                "Écart",
                format_fcfa(
                    ecart_preview
                )
            )


        with a3:

            st.metric(
                "Progression",
                f"{min(max(progression_preview, 0), 100):.1f} %"
            )


        with a4:

            st.metric(
                "Statut",
                statut_preview
            )


        # ====================================================
        # ENREGISTREMENT
        # ====================================================

        if enregistrer:

            succes, resultat = put_api(
                f"/api/depenses/{depense_id}",
                {
                    "quantite_reelle": float(
                        quantite_reelle
                    ),
                    "montant_reel": float(
                        montant_reel
                    )
                }
            )


            if succes:

                st.success(
                    "✅ Dépense réelle mise à jour."
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
        # SUPPRESSION D'UNE DEPENSE
        # ====================================================

        st.divider()


        with st.expander(
            "🗑️ Supprimer une dépense",
            expanded=False
        ):

            st.warning(
                "Cette opération supprimera définitivement "
                "la dépense sélectionnée de la base de données."
            )


            confirmation_suppression = st.checkbox(
                (
                    "⚠️ Je confirme vouloir supprimer "
                    "définitivement cette dépense."
                ),
                key=(
                    "confirmation_suppression_"
                    f"{depense_id}"
                )
            )


            supprimer_depense = st.button(
                "🗑️ Supprimer définitivement",
                disabled=not confirmation_suppression,
                key=(
                    "bouton_suppression_"
                    f"{depense_id}"
                )
            )


            if supprimer_depense:

                succes, resultat = delete_api(
                    f"/api/depenses/{depense_id}"
                )


                if succes:

                    st.success(
                        "✅ Dépense supprimée définitivement."
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
# RAPPEL CAVEAU
# ============================================================

if (
    categorie_selectionnee
    == "CAVEAU"
):

    st.divider()

    st.info(
        "ℹ️ Le CAVEAU dispose actuellement "
        "d'un budget prévisionnel global de "
        f"{format_fcfa(budget_previsionnel)}, "
        "mais son détail n'est pas encore affecté. "
        "Le budget reste donc enregistré comme "
        "« non affecté » jusqu'à sa ventilation."
    )


# ============================================================
# SIGNATURE
# ============================================================

afficher_signature()

