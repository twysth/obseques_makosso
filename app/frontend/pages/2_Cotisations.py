
import sys
import os
from pathlib import Path
from datetime import date

import pandas as pd
import requests
import streamlit as st


# ============================================================
# IMPORT COMPOSANTS COMMUNS
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
    page_title="Cotisations",
    page_icon="👥",
    layout="wide",
)


# ============================================================
# INITIALISATION SESSION
# ============================================================

if "admin_token" not in st.session_state:

    st.session_state.admin_token = None


# ============================================================
# OUTILS
# ============================================================

def format_fcfa(valeur):
    """Formate un montant en FCFA."""

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
    """Affichage convivial des statuts."""

    if statut == "NON SOLDE":
        return "🔴 NON SOLDE"

    if statut == "PARTIEL":
        return "🟠 PARTIEL"

    if statut == "SOLDE":
        return "🟢 SOLDE"

    if statut == "SUPER":
        return "🎉 SUPER"

    return statut


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

        return None

    except requests.exceptions.RequestException as erreur:

        st.error(
            f"❌ Erreur de connexion à l'API : {erreur}"
        )

        return None


def post_api(endpoint, payload):

    try:

        response = requests.post(
            f"{API_URL}{endpoint}",
            json=payload,
            headers=get_admin_headers(),
            timeout=10,
        )

        try:

            resultat = response.json()

        except ValueError:

            resultat = {
                "message": response.text
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
            timeout=10,
        )

        try:

            resultat = response.json()

        except ValueError:

            resultat = {
                "message": response.text
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
                "message": response.text
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
    "👥 Gestion des cotisations"
)

st.caption(
    "Suivi des contributions — Famille Bayema et Enfants"
)

st.divider()


# ============================================================
# ESPACE ADMINISTRATEUR CENTRALISE
# ============================================================

afficher_espace_admin()

st.divider()


# ============================================================
# RECUPERATION DES COTISANTS
# ============================================================

cotisants = get_api(
    "/api/cotisants"
)

if cotisants is None:

    afficher_signature()

    st.stop()


df = pd.DataFrame(
    cotisants
)


colonnes = [
    "id",
    "nom",
    "liste",
    "telephone",
    "montant_prevu",
    "montant_verse",
    "reste",
    "statut",
]


if df.empty:

    df = pd.DataFrame(
        columns=colonnes
    )


# ============================================================
# INDICATEURS GENERAUX
# ============================================================

total_prevu = (
    pd.to_numeric(
        df["montant_prevu"],
        errors="coerce"
    )
    .fillna(0)
    .sum()
)


total_verse = (
    pd.to_numeric(
        df["montant_verse"],
        errors="coerce"
    )
    .fillna(0)
    .sum()
)


total_reste = (
    pd.to_numeric(
        df["reste"],
        errors="coerce"
    )
    .fillna(0)
    .sum()
)


if total_prevu > 0:

    taux_global = (
        total_verse
        / total_prevu
    ) * 100

else:

    taux_global = 0


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "💰 Total prévu",
        format_fcfa(
            total_prevu
        )
    )


with col2:

    st.metric(
        "✅ Total versé",
        format_fcfa(
            total_verse
        )
    )


with col3:

    st.metric(
        "⏳ Reste à collecter",
        format_fcfa(
            total_reste
        )
    )


with col4:

    st.metric(
        "📈 Taux de collecte",
        f"{taux_global:.1f} %"
    )


st.progress(
    min(
        max(
            taux_global / 100,
            0
        ),
        1
    )
)


# ============================================================
# SYNTHESE PAR LISTE
# ============================================================

st.divider()

st.subheader(
    "📊 Synthèse des cotisations"
)


def afficher_synthese_liste(nom_liste):

    donnees = df[
        df["liste"] == nom_liste
    ]

    prevu = (
        pd.to_numeric(
            donnees["montant_prevu"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    verse = (
        pd.to_numeric(
            donnees["montant_verse"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    reste = (
        pd.to_numeric(
            donnees["reste"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    if prevu > 0:

        taux = (
            verse
            / prevu
        ) * 100

    else:

        taux = 0


    st.markdown(
        f"### {nom_liste}"
    )


    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "Prévu",
            format_fcfa(prevu)
        )


    with c2:

        st.metric(
            "Versé",
            format_fcfa(verse)
        )


    with c3:

        st.metric(
            "Reste",
            format_fcfa(reste)
        )


    with c4:

        st.metric(
            "Collecte",
            f"{taux:.1f} %"
        )


    st.progress(
        min(
            max(
                taux / 100,
                0
            ),
            1
        )
    )


afficher_synthese_liste(
    "Famille Bayema"
)

afficher_synthese_liste(
    "Enfants"
)


# ============================================================
# LISTE DES COTISANTS
# ============================================================

st.divider()

st.subheader(
    "📋 Liste des cotisants"
)


if df.empty:

    st.info(
        "Aucun cotisant n'est encore enregistré."
    )

else:

    affichage = df[
        [
            "nom",
            "liste",
            "telephone",
            "montant_prevu",
            "montant_verse",
            "reste",
            "statut",
        ]
    ].copy()


    affichage.columns = [
        "Nom",
        "Liste",
        "Téléphone",
        "Montant prévu",
        "Montant versé",
        "Reste",
        "Statut",
    ]


    affichage[
        "Statut"
    ] = affichage[
        "Statut"
    ].apply(
        afficher_statut
    )


    st.dataframe(
        affichage,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# ADMINISTRATION
# ============================================================

if admin_connecte():

    st.divider()

    st.subheader(
        "🔐 Administration des cotisations"
    )


    # ========================================================
    # AJOUTER UN COTISANT
    # ========================================================

    with st.expander(
        "➕ Ajouter un cotisant",
        expanded=False
    ):

        with st.form(
            "form_ajout_cotisant",
            clear_on_submit=True
        ):

            nom = st.text_input(
                "Nom du cotisant"
            )

            liste = st.selectbox(
                "Liste",
                [
                    "Famille Bayema",
                    "Enfants"
                ]
            )

            telephone = st.text_input(
                "Téléphone / WhatsApp",
                help=(
                    "Le numéro complet est réservé "
                    "à l'administration."
                )
            )

            montant_prevu = st.number_input(
                "Montant prévu (FCFA)",
                min_value=0.0,
                step=5000.0,
            )

            ajouter = st.form_submit_button(
                "Ajouter le cotisant"
            )


        if ajouter:

            if not nom.strip():

                st.error(
                    "Le nom est obligatoire."
                )

            elif not telephone.strip():

                st.error(
                    "Le numéro de téléphone est obligatoire."
                )

            else:

                succes, resultat = post_api(
                    "/api/cotisants",
                    {
                        "nom": nom.strip(),
                        "liste": liste,
                        "telephone": telephone.strip(),
                        "montant_prevu": montant_prevu,
                    }
                )

                if succes:

                    st.success(
                        "✅ Cotisant ajouté."
                    )

                    st.rerun()

                else:

                    st.error(
                        resultat.get(
                            "error",
                            "Erreur lors de l'ajout."
                        )
                    )


    # ========================================================
    # MODIFIER UN COTISANT
    # ========================================================

    with st.expander(
        "✏️ Modifier un cotisant",
        expanded=False
    ):

        if df.empty:

            st.info(
                "Aucun cotisant à modifier."
            )

        else:

            choix = {
                f"{row['nom']} — {row['liste']} "
                f"(ID {int(row['id'])})":
                int(row["id"])
                for _, row in df.iterrows()
            }


            selection = st.selectbox(
                "Cotisant à modifier",
                list(choix.keys()),
                key="selection_modification",
            )


            cotisant_id = choix[
                selection
            ]


            ligne = df[
                df["id"] == cotisant_id
            ].iloc[0]


            with st.form(
                "form_modification_cotisant"
            ):

                nouveau_nom = st.text_input(
                    "Nom",
                    value=str(
                        ligne["nom"]
                    ),
                )


                nouvelles_liste = st.selectbox(
                    "Liste",
                    [
                        "Famille Bayema",
                        "Enfants"
                    ],
                    index=(
                        0
                        if ligne["liste"]
                        == "Famille Bayema"
                        else 1
                    ),
                )


                nouveau_telephone = st.text_input(
                    "Téléphone",
                    value=str(
                        ligne["telephone"]
                    ),
                )


                nouveau_prevu = st.number_input(
                    "Montant prévu",
                    min_value=0.0,
                    value=float(
                        ligne["montant_prevu"]
                    ),
                    step=5000.0,
                )


                modifier = st.form_submit_button(
                    "Enregistrer les modifications"
                )


            if modifier:

                succes, resultat = put_api(
                    f"/api/cotisants/{cotisant_id}",
                    {
                        "nom": nouveau_nom.strip(),
                        "liste": nouvelles_liste,
                        "telephone": (
                            nouveau_telephone.strip()
                        ),
                        "montant_prevu": nouveau_prevu,
                    }
                )


                if succes:

                    st.success(
                        "✅ Cotisant modifié."
                    )

                    st.rerun()

                else:

                    st.error(
                        resultat.get(
                            "error",
                            "Erreur lors de la modification."
                        )
                    )


    # ========================================================
    # SUPPRIMER UN COTISANT
    # ========================================================

    with st.expander(
        "🗑️ Supprimer un cotisant",
        expanded=False
    ):

        if df.empty:

            st.info(
                "Aucun cotisant à supprimer."
            )

        else:

            choix_suppression = {
                f"{row['nom']} — {row['liste']} "
                f"(ID {int(row['id'])})":
                int(row["id"])
                for _, row in df.iterrows()
            }


            suppression_selection = st.selectbox(
                "Cotisant à supprimer",
                list(
                    choix_suppression.keys()
                ),
                key="selection_suppression",
            )


            cotisant_id_suppression = (
                choix_suppression[
                    suppression_selection
                ]
            )


            confirmer = st.checkbox(
                "⚠️ Je confirme la suppression définitive.",
                key="confirmation_suppression_cotisant"
            )


            if st.button(
                "🗑️ Supprimer définitivement",
                disabled=not confirmer,
                key="bouton_suppression_cotisant"
            ):

                succes, resultat = delete_api(
                    "/api/cotisants/"
                    f"{cotisant_id_suppression}"
                )


                if succes:

                    st.success(
                        "✅ Cotisant supprimé."
                    )

                    st.rerun()

                else:

                    st.error(
                        resultat.get(
                            "error",
                            "Erreur lors de la suppression."
                        )
                    )


    # ========================================================
    # ENREGISTRER UN VERSEMENT
    # ========================================================

    with st.expander(
        "💳 Enregistrer un versement",
        expanded=False
    ):

        if df.empty:

            st.info(
                "Ajoutez d'abord un cotisant."
            )

        else:

            choix_versement = {
                f"{row['nom']} — {row['liste']} "
                f"(reste "
                f"{format_fcfa(row['reste'])})":
                int(row["id"])
                for _, row in df.iterrows()
            }


            selection_versement = st.selectbox(
                "Cotisant",
                list(
                    choix_versement.keys()
                ),
                key="selection_versement",
            )


            cotisant_id_versement = (
                choix_versement[
                    selection_versement
                ]
            )


            ligne_versement = df[
                df["id"]
                == cotisant_id_versement
            ].iloc[0]


            st.write(
                f"Prévu : "
                f"**{format_fcfa(ligne_versement['montant_prevu'])}**"
            )


            st.write(
                f"Déjà versé : "
                f"**{format_fcfa(ligne_versement['montant_verse'])}**"
            )


            st.write(
                f"Reste : "
                f"**{format_fcfa(ligne_versement['reste'])}**"
            )


            montant_versement = st.number_input(
                "Montant du versement (FCFA)",
                min_value=1.0,
                step=5000.0,
                key="montant_versement",
            )


            date_versement = st.date_input(
                "Date du versement",
                value=date.today(),
                key="date_versement",
            )


            commentaire = st.text_input(
                "Commentaire",
                placeholder="Ex. Versement espèces",
                key="commentaire_versement",
            )


            if st.button(
                "💳 Enregistrer le versement",
                key="bouton_enregistrer_versement"
            ):

                succes, resultat = post_api(
                    "/api/versements",
                    {
                        "cotisant_id": (
                            cotisant_id_versement
                        ),
                        "montant": (
                            montant_versement
                        ),
                        "date_versement": str(
                            date_versement
                        ),
                        "commentaire": (
                            commentaire
                        ),
                    }
                )


                if succes:

                    nouveau_statut = resultat.get(
                        "statut",
                        ""
                    )


                    if nouveau_statut == "SUPER":

                        st.success(
                            "🎉 SUPER ! "
                            "La contribution dépasse "
                            "le montant prévu."
                        )


                    elif nouveau_statut == "SOLDE":

                        st.success(
                            "🟢 Contribution soldée."
                        )


                    else:

                        st.success(
                            "✅ Versement enregistré."
                        )


                    st.rerun()


                else:

                    st.error(
                        resultat.get(
                            "error",
                            "Erreur lors du versement."
                        )
                    )


    # ========================================================
    # HISTORIQUE DES VERSEMENTS
    # ========================================================

    with st.expander(
        "📜 Historique des versements",
        expanded=False
    ):

        if df.empty:

            st.info(
                "Aucun cotisant disponible."
            )

        else:

            choix_historique = {
                f"{row['nom']} — {row['liste']}":
                int(row["id"])
                for _, row in df.iterrows()
            }


            selection_historique = st.selectbox(
                "Cotisant",
                list(
                    choix_historique.keys()
                ),
                key="selection_historique",
            )


            historique_cotisant_id = (
                choix_historique[
                    selection_historique
                ]
            )


            versements = get_api(
                "/api/versements"
                "?cotisant_id="
                f"{historique_cotisant_id}"
            )


            if versements is None:

                st.error(
                    "Impossible de récupérer "
                    "l'historique des versements."
                )

            else:

                df_versements = pd.DataFrame(
                    versements
                )


                if df_versements.empty:

                    st.info(
                        "Aucun versement enregistré "
                        "pour ce cotisant."
                    )

                else:

                    colonnes_versements = [
                        "id",
                        "date_versement",
                        "montant",
                        "commentaire",
                    ]


                    colonnes_disponibles = [
                        colonne
                        for colonne in colonnes_versements
                        if colonne in df_versements.columns
                    ]


                    affichage_versements = (
                        df_versements[
                            colonnes_disponibles
                        ].copy()
                    )


                    if "montant" in affichage_versements.columns:

                        affichage_versements[
                            "montant"
                        ] = (
                            pd.to_numeric(
                                affichage_versements[
                                    "montant"
                                ],
                                errors="coerce"
                            )
                            .fillna(0)
                            .map(format_fcfa)
                        )


                    affichage_versements = (
                        affichage_versements.rename(
                            columns={
                                "id": "ID",
                                "date_versement": "Date",
                                "montant": "Montant",
                                "commentaire": "Commentaire",
                            }
                        )
                    )


                    colonnes_affichage = [
                        colonne
                        for colonne in [
                            "Date",
                            "Montant",
                            "Commentaire",
                        ]
                        if colonne in affichage_versements.columns
                    ]


                    st.dataframe(
                        affichage_versements[
                            colonnes_affichage
                        ],
                        width="stretch",
                        hide_index=True,
                    )


                    if "montant" in df_versements.columns:

                        total_historique = (
                            pd.to_numeric(
                                df_versements[
                                    "montant"
                                ],
                                errors="coerce"
                            )
                            .fillna(0)
                            .sum()
                        )

                    else:

                        total_historique = 0


                    st.metric(
                        "💰 Total historique des versements",
                        format_fcfa(
                            total_historique
                        )
                    )


                    # ----------------------------------------
                    # SUPPRESSION D'UN VERSEMENT
                    # ----------------------------------------

                    st.divider()

                    st.markdown(
                        "### 🗑️ Suppression d'un versement"
                    )


                    choix_suppression_versement = {}


                    for _, versement in (
                        df_versements.iterrows()
                    ):

                        versement_id = int(
                            versement["id"]
                        )

                        montant_versement_ligne = float(
                            versement.get(
                                "montant",
                                0
                            )
                            or 0
                        )

                        date_versement_ligne = str(
                            versement.get(
                                "date_versement",
                                ""
                            )
                        )

                        label = (
                            f"#{versement_id} — "
                            f"{date_versement_ligne} — "
                            f"{format_fcfa(montant_versement_ligne)}"
                        )


                        choix_suppression_versement[
                            label
                        ] = versement_id


                    if choix_suppression_versement:

                        versement_selection = st.selectbox(
                            "Versement à supprimer",
                            list(
                                choix_suppression_versement.keys()
                            ),
                            key="selection_suppression_versement"
                        )


                        versement_id_suppression = (
                            choix_suppression_versement[
                                versement_selection
                            ]
                        )


                        confirmer_versement = st.checkbox(
                            (
                                "⚠️ Je confirme la suppression "
                                "définitive de ce versement."
                            ),
                            key=(
                                "confirmation_suppression_versement"
                            )
                        )


                        if st.button(
                            "🗑️ Supprimer le versement",
                            disabled=not confirmer_versement,
                            key="bouton_suppression_versement"
                        ):

                            succes, resultat = delete_api(
                                f"/api/versements/"
                                f"{versement_id_suppression}"
                            )


                            if succes:

                                st.success(
                                    "✅ Versement supprimé. "
                                    "Le total du cotisant a été recalculé."
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

