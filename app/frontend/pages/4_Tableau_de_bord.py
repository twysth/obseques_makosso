
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
    str(Path(__file__).resolve().parents[1])
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
    page_title="Tableau de bord - Obsèques MAKOSSO",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# SESSION ADMINISTRATEUR
# ============================================================

if "admin_token" not in st.session_state:

    st.session_state.admin_token = None


def get_headers():

    if st.session_state.admin_token:

        return {
            "X-Admin-Token": (
                st.session_state.admin_token
            )
        }

    return {}


# ============================================================
# OUTILS
# ============================================================

def format_fcfa(valeur):

    return (
        f"{float(valeur):,.0f} FCFA"
        .replace(",", " ")
    )


def get_api(endpoint):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            headers=get_headers(),
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
                    f"Erreur API {endpoint} "
                    f"HTTP {response.status_code}"
                )
            )

            return None

        return resultat

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ L'API Flask n'est pas accessible sur : "
            f"{API_URL}"
        )

        return None

    except requests.exceptions.RequestException as erreur:

        st.error(
            f"❌ Erreur de connexion à l'API : {erreur}"
        )

        return None


def statut_tache(statut):

    if statut == "A FAIRE":
        return "🔴 A FAIRE"

    if statut == "EN COURS":
        return "🟠 EN COURS"

    if statut == "TERMINE":
        return "🟢 TERMINE"

    return statut


def statut_cotisation(statut):

    if statut == "NON SOLDE":
        return "🔴 NON SOLDE"

    if statut == "PARTIEL":
        return "🟠 PARTIEL"

    if statut == "SOLDE":
        return "🟢 SOLDE"

    if statut == "SUPER":
        return "🎉 SUPER"

    return statut


# ============================================================
# TITRE
# ============================================================

st.title(
    "📊 Tableau de bord"
)

st.subheader(
    "Obsèques de Feu MAKOSSO POATHY Jean Pierre"
)

st.caption(
    "Pilotage financier, contributions et préparatifs"
)

st.divider()


# ============================================================
# COMPTE A REBOURS
# ============================================================

jours_restants = (
    DATE_OBSEQUES
    - date.today()
).days


col_date, col_jours = st.columns(2)


with col_date:

    st.metric(
        "📅 Date des obsèques",
        DATE_OBSEQUES.strftime("%d/%m/%Y")
    )


with col_jours:

    if jours_restants > 0:

        st.metric(
            "⏳ Temps restant",
            f"J-{jours_restants}"
        )

    elif jours_restants == 0:

        st.metric(
            "⏳ Temps restant",
            "AUJOURD'HUI"
        )

    else:

        st.metric(
            "⏳ Temps écoulé",
            f"J+{abs(jours_restants)}"
        )


# ============================================================
# CHARGEMENT API
# ============================================================

dashboard = get_api(
    "/api/dashboard"
)

categories = get_api(
    "/api/categories"
)

depenses = get_api(
    "/api/depenses"
)

cotisants = get_api(
    "/api/cotisants"
)

taches = get_api(
    "/api/taches"
)


if (
    dashboard is None
    or categories is None
    or depenses is None
    or cotisants is None
    or taches is None
):

    st.error(
        "❌ Impossible de charger toutes les "
        "données du tableau de bord."
    )

    afficher_signature()

    st.stop()


# ============================================================
# DATAFRAMES
# ============================================================

df_categories = pd.DataFrame(
    categories
)

df_depenses = pd.DataFrame(
    depenses
)

df_cotisants = pd.DataFrame(
    cotisants
)

df_taches = pd.DataFrame(
    taches
)


# ============================================================
# INDICATEURS FINANCIERS
# ============================================================

budget_previsionnel = float(
    dashboard[
        "budget_previsionnel"
    ]
)

budget_detaille = float(
    dashboard[
        "budget_detaille"
    ]
)

budget_non_affecte = float(
    dashboard[
        "budget_non_affecte"
    ]
)

montant_reel = float(
    dashboard[
        "montant_reel"
    ]
)

ecart = float(
    dashboard[
        "ecart"
    ]
)

if budget_previsionnel > 0:

    progression_budget = (
        montant_reel
        / budget_previsionnel
    ) * 100

else:

    progression_budget = 0.0


# ============================================================
# VUE FINANCIERE
# ============================================================

st.header(
    "💰 Vue financière"
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Budget prévisionnel",
        format_fcfa(
            budget_previsionnel
        )
    )


with c2:

    st.metric(
        "Budget détaillé",
        format_fcfa(
            budget_detaille
        )
    )


with c3:

    st.metric(
        "Dépenses réelles",
        format_fcfa(
            montant_reel
        )
    )


with c4:

    st.metric(
        "Écart",
        format_fcfa(
            ecart
        )
    )


st.write(
    f"### 📈 Réalisation financière : "
    f"{progression_budget:.1f} %"
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


# ============================================================
# ALERTE BUDGET
# ============================================================

if ecart > 0:

    st.error(
        f"⚠️ Dépassement actuel : "
        f"{format_fcfa(ecart)}"
    )

elif ecart < 0:

    st.success(
        f"✅ Budget sous contrôle — marge restante : "
        f"{format_fcfa(abs(ecart))}"
    )

else:

    st.info(
        "Budget prévisionnel atteint exactement."
    )


if budget_non_affecte > 0:

    st.warning(
        f"⚠️ Budget non affecté : "
        f"{format_fcfa(budget_non_affecte)}"
    )


# ============================================================
# PREVISIONNEL VS REEL
# ============================================================

st.divider()

st.header(
    "📊 Prévisionnel vs Réel"
)


comparaison = pd.DataFrame(
    {
        "Montant": [
            budget_previsionnel,
            montant_reel
        ]
    },
    index=[
        "Prévisionnel",
        "Réel"
    ]
)


st.bar_chart(
    comparaison
)


# ============================================================
# BUDGET PAR CATEGORIE
# ============================================================

st.header(
    "📋 Budget par catégorie"
)


if not df_categories.empty:

    graphique_categories = df_categories[
        [
            "nom",
            "budget_previsionnel"
        ]
    ].copy()


    graphique_categories[
        "budget_previsionnel"
    ] = pd.to_numeric(
        graphique_categories[
            "budget_previsionnel"
        ],
        errors="coerce"
    ).fillna(0)


    graphique_categories = (
        graphique_categories
        .set_index("nom")
    )


    graphique_categories.columns = [
        "Budget prévisionnel"
    ]


    st.bar_chart(
        graphique_categories
    )


# ============================================================
# PRINCIPALES DEPENSES
# ============================================================

st.subheader(
    "💸 Principales dépenses prévisionnelles"
)


if not df_depenses.empty:

    top_depenses = (
        df_depenses[
            [
                "designation",
                "categorie",
                "montant_prevu"
            ]
        ]
        .copy()
    )


    top_depenses[
        "montant_prevu"
    ] = pd.to_numeric(
        top_depenses[
            "montant_prevu"
        ],
        errors="coerce"
    ).fillna(0)


    top_depenses = (
        top_depenses
        .sort_values(
            "montant_prevu",
            ascending=False
        )
        .head(10)
    )


    top_depenses[
        "montant_prevu"
    ] = top_depenses[
        "montant_prevu"
    ].map(
        format_fcfa
    )


    top_depenses.columns = [
        "Désignation",
        "Catégorie",
        "Montant prévu"
    ]


    st.dataframe(
        top_depenses,
        width="stretch",
        hide_index=True
    )


# ============================================================
# COTISATIONS
# ============================================================

st.divider()

st.header(
    "💳 Situation des cotisations"
)


if df_cotisants.empty:

    total_prevu = 0.0
    total_verse = 0.0
    total_reste = 0.0
    taux_collecte = 0.0

else:

    total_prevu = float(
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


    if total_prevu > 0:

        taux_collecte = (
            total_verse
            / total_prevu
        ) * 100

    else:

        taux_collecte = 0.0


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Prévu",
        format_fcfa(
            total_prevu
        )
    )


with c2:

    st.metric(
        "Versé",
        format_fcfa(
            total_verse
        )
    )


with c3:

    st.metric(
        "Reste",
        format_fcfa(
            total_reste
        )
    )


with c4:

    st.metric(
        "Collecte",
        f"{taux_collecte:.1f} %"
    )


st.progress(
    min(
        max(
            taux_collecte / 100,
            0
        ),
        1
    )
)


# ============================================================
# PREPARATIFS
# ============================================================

st.divider()

st.header(
    "✅ Avancement des préparatifs"
)


if df_taches.empty:

    nombre_taches = 0
    terminees = 0
    en_cours = 0
    a_faire = 0
    avancement_taches = 0.0

else:

    df_taches[
        "progression"
    ] = pd.to_numeric(
        df_taches[
            "progression"
        ],
        errors="coerce"
    ).fillna(0)


    nombre_taches = int(
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


    avancement_taches = float(
        df_taches[
            "progression"
        ].mean()
    )


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Tâches",
        nombre_taches
    )


with c2:

    st.metric(
        "Terminées",
        terminees
    )


with c3:

    st.metric(
        "En cours",
        en_cours
    )


with c4:

    st.metric(
        "À faire",
        a_faire
    )


st.write(
    f"### 📈 Avancement opérationnel : "
    f"{avancement_taches:.1f} %"
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
# PROCHAINES TACHES
# ============================================================

st.subheader(
    "📅 Prochaines échéances"
)


if df_taches.empty:

    st.info(
        "Aucune tâche planifiée."
    )

else:

    prochaines = df_taches.copy()


    prochaines[
        "date_prevue"
    ] = pd.to_datetime(
        prochaines[
            "date_prevue"
        ],
        errors="coerce"
    )


    prochaines = prochaines[
        prochaines[
            "date_prevue"
        ].notna()
    ]


    prochaines = prochaines[
        prochaines[
            "statut"
        ] != "TERMINE"
    ]


    prochaines = (
        prochaines
        .sort_values(
            "date_prevue"
        )
        .head(10)
    )


    if prochaines.empty:

        st.success(
            "✅ Aucune échéance ouverte."
        )

    else:

        prochaines[
            "Date prévue"
        ] = prochaines[
            "date_prevue"
        ].dt.strftime(
            "%d/%m/%Y"
        )


        prochaines[
            "Progression"
        ] = pd.to_numeric(
            prochaines[
                "progression"
            ],
            errors="coerce"
        ).fillna(0).map(
            lambda x: f"{x:.0f} %"
        )


        prochaines[
            "Statut"
        ] = prochaines[
            "statut"
        ].apply(
            statut_tache
        )


        prochaines.columns = [
            "ID",
            "Catégorie ID",
            "Tâche",
            "Description",
            "Progression brute",
            "Statut brut",
            "Date prévue brute",
            "Date réalisation",
            "Catégorie",
            "Date prévue",
            "Progression",
            "Statut"
        ][:len(prochaines.columns)]


        colonnes_affichage = [
            "Tâche",
            "Catégorie",
            "Date prévue",
            "Progression",
            "Statut"
        ]


        # Sécurité si certaines colonnes n'existent pas
        colonnes_affichage = [
            colonne
            for colonne in colonnes_affichage
            if colonne in prochaines.columns
        ]


        st.dataframe(
            prochaines[
                colonnes_affichage
            ],
            width="stretch",
            hide_index=True
        )


# ============================================================
# SYNTHESE PAR CATEGORIE
# ============================================================

st.divider()

st.header(
    "📌 Synthèse par catégorie"
)


if not df_depenses.empty:

    synthese = (
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
            )
        )
    )


    synthese["ecart"] = (
        synthese["reel"]
        - synthese["previsionnel"]
    )


    synthese["progression"] = 0.0


    masque = (
        synthese[
            "previsionnel"
        ] > 0
    )


    synthese.loc[
        masque,
        "progression"
    ] = (
        synthese.loc[
            masque,
            "reel"
        ]
        /
        synthese.loc[
            masque,
            "previsionnel"
        ]
        * 100
    )


    synthese[
        "progression"
    ] = synthese[
        "progression"
    ].clip(
        0,
        100
    )


    affichage = synthese.copy()


    affichage[
        "previsionnel"
    ] = affichage[
        "previsionnel"
    ].map(format_fcfa)


    affichage[
        "reel"
    ] = affichage[
        "reel"
    ].map(format_fcfa)


    affichage[
        "ecart"
    ] = affichage[
        "ecart"
    ].map(format_fcfa)


    affichage[
        "progression"
    ] = affichage[
        "progression"
    ].map(
        lambda x: f"{x:.1f} %"
    )


    affichage.columns = [
        "Catégorie",
        "Prévisionnel",
        "Réel",
        "Écart",
        "Progression"
    ]


    st.dataframe(
        affichage,
        width="stretch",
        hide_index=True
    )


# ============================================================
# ETAT DES COTISANTS
# ============================================================

st.divider()

st.subheader(
    "👥 État des cotisants"
)


if df_cotisants.empty:

    st.info(
        "Aucun cotisant enregistré."
    )

else:

    statut_counts = (
        df_cotisants[
            "statut"
        ]
        .value_counts()
        .rename_axis(
            "Statut"
        )
        .reset_index(
            name="Nombre"
        )
    )


    statut_counts[
        "Statut"
    ] = statut_counts[
        "Statut"
    ].apply(
        statut_cotisation
    )


    st.dataframe(
        statut_counts,
        width="stretch",
        hide_index=True
    )


# ============================================================
# ALERTES RAPIDES
# ============================================================

st.divider()

st.header(
    "⚠️ Points d'attention"
)


nb_alertes = 0


# Budget non affecté
if budget_non_affecte > 0:

    st.warning(
        f"💰 {format_fcfa(budget_non_affecte)} "
        "de budget reste non affecté."
    )

    nb_alertes += 1


# Cotisants non soldés
if not df_cotisants.empty:

    non_solde = df_cotisants[
        df_cotisants[
            "statut"
        ].isin(
            [
                "NON SOLDE",
                "PARTIEL"
            ]
        )
    ]


    if not non_solde.empty:

        st.warning(
            f"💳 {len(non_solde)} cotisant(s) "
            "non soldé(s) ou partiel(s)."
        )

        nb_alertes += 1


# Tâches non terminées
if not df_taches.empty:

    non_terminees = df_taches[
        df_taches[
            "statut"
        ] != "TERMINE"
    ]


    if not non_terminees.empty:

        st.warning(
            f"✅ {len(non_terminees)} tâche(s) "
            "reste(nt) à terminer."
        )

        nb_alertes += 1


# Dépenses en dépassement
if not df_depenses.empty:

    depassements = df_depenses[
        pd.to_numeric(
            df_depenses[
                "ecart"
            ],
            errors="coerce"
        ).fillna(0)
        > 0
    ]


    if not depassements.empty:

        st.warning(
            f"📈 {len(depassements)} dépense(s) "
            "en dépassement."
        )

        nb_alertes += 1


# Échéances proches
if not df_taches.empty:

    prochaines_alertes = df_taches.copy()


    prochaines_alertes[
        "date_prevue"
    ] = pd.to_datetime(
        prochaines_alertes[
            "date_prevue"
        ],
        errors="coerce"
    )


    prochaines_alertes = prochaines_alertes[
        prochaines_alertes[
            "date_prevue"
        ].notna()
    ]


    prochaines_alertes = prochaines_alertes[
        prochaines_alertes[
            "statut"
        ] != "TERMINE"
    ]


    proximite = (
        prochaines_alertes[
            "date_prevue"
        ]
        <= pd.Timestamp.today()
        + pd.Timedelta(days=3)
    )


    if proximite.any():

        st.warning(
            f"📅 {int(proximite.sum())} tâche(s) "
            "ont une échéance dans les 3 prochains jours."
        )

        nb_alertes += 1


if nb_alertes == 0:

    st.success(
        "✅ Aucun point d'attention détecté."
    )


# ============================================================
# RAPPEL DU PILOTAGE
# ============================================================

st.divider()

st.info(
    "🕊️ Ce tableau de bord présente une vue "
    "de pilotage familiale des obsèques. "
    "Les données réelles sont mises à jour "
    "au fur et à mesure des dépenses, "
    "cotisations et préparatifs."
)


# ============================================================
# SIGNATURE
# ============================================================

afficher_signature()

