
import sys
import os
from pathlib import Path
from datetime import date, datetime

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
    page_title="Reporting - Obsèques MAKOSSO",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# SESSION ADMIN
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


def statut_cotisation(statut):

    correspondance = {
        "NON SOLDE": "🔴 NON SOLDE",
        "PARTIEL": "🟠 PARTIEL",
        "SOLDE": "🟢 SOLDE",
        "SUPER": "⭐ SUPER"
    }

    return correspondance.get(
        statut,
        statut
    )


def statut_tache(statut):

    correspondance = {
        "A FAIRE": "🔴 A FAIRE",
        "EN COURS": "🟠 EN COURS",
        "TERMINE": "🟢 TERMINE"
    }

    return correspondance.get(
        statut,
        statut
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


# ============================================================
# TITRE
# ============================================================

st.title(
    "📊 Reporting global des obsèques"
)

st.caption(
    "Synthèse financière, cotisations, préparatifs et alertes"
)

st.divider()


# ============================================================
# DATE / COMPTE A REBOURS
# ============================================================

jours_restants = (
    DATE_OBSEQUES
    - date.today()
).days


st.subheader(
    "📅 Situation au "
    + date.today().strftime("%d/%m/%Y")
)


if jours_restants > 0:

    st.info(
        f"⏳ J-{jours_restants} avant les obsèques "
        f"du 27/08/2026."
    )

elif jours_restants == 0:

    st.success(
        "🕊️ Jour des obsèques : 27/08/2026."
    )

else:

    st.warning(
        "Les obsèques du 27/08/2026 sont passées."
    )


# ============================================================
# CHARGEMENT
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
        "❌ Impossible de construire le reporting."
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
# 1. SYNTHESE FINANCIERE
# ============================================================

st.divider()

st.header(
    "💰 1. Synthèse financière"
)


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

depenses_reelles = float(
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

    taux_realisation = (
        depenses_reelles
        / budget_previsionnel
    ) * 100

else:

    taux_realisation = 0.0


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
        "Budget non affecté",
        format_fcfa(
            budget_non_affecte
        )
    )


with c4:

    st.metric(
        "Dépenses réelles",
        format_fcfa(
            depenses_reelles
        )
    )


st.write(
    f"**Taux de réalisation : "
    f"{taux_realisation:.1f} %**"
)


st.progress(
    min(
        max(
            taux_realisation / 100,
            0
        ),
        1
    )
)


if ecart < 0:

    st.success(
        "✅ Situation favorable : "
        f"{format_fcfa(abs(ecart))} "
        "restent sous le budget."
    )

elif ecart > 0:

    st.error(
        "⚠️ Dépassement budgétaire : "
        f"{format_fcfa(ecart)}."
    )

else:

    st.info(
        "Budget prévisionnel atteint exactement."
    )


# ============================================================
# 2. ANALYSE PAR CATEGORIE
# ============================================================

st.divider()

st.header(
    "📋 2. Analyse financière par catégorie"
)


if df_depenses.empty:

    st.info(
        "Aucune dépense disponible."
    )

else:

    df_depenses["montant_prevu"] = (
        pd.to_numeric(
            df_depenses["montant_prevu"],
            errors="coerce"
        )
        .fillna(0)
    )


    df_depenses["montant_reel"] = (
        pd.to_numeric(
            df_depenses["montant_reel"],
            errors="coerce"
        )
        .fillna(0)
    )


    df_depenses["ecart"] = (
        pd.to_numeric(
            df_depenses["ecart"],
            errors="coerce"
        )
        .fillna(0)
    )


    analyse = (
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


    analyse["progression"] = 0.0


    masque = (
        analyse["previsionnel"] > 0
    )


    analyse.loc[
        masque,
        "progression"
    ] = (
        analyse.loc[
            masque,
            "reel"
        ]
        /
        analyse.loc[
            masque,
            "previsionnel"
        ]
        * 100
    )


    analyse["progression"] = (
        analyse["progression"]
        .clip(
            0,
            100
        )
    )


    tableau_analyse = analyse.copy()


    tableau_analyse[
        "previsionnel"
    ] = tableau_analyse[
        "previsionnel"
    ].map(format_fcfa)


    tableau_analyse[
        "reel"
    ] = tableau_analyse[
        "reel"
    ].map(format_fcfa)


    tableau_analyse[
        "ecart"
    ] = tableau_analyse[
        "ecart"
    ].map(format_fcfa)


    tableau_analyse[
        "progression"
    ] = tableau_analyse[
        "progression"
    ].map(
        lambda x: f"{x:.1f} %"
    )


    tableau_analyse.columns = [
        "Catégorie",
        "Prévisionnel",
        "Réel",
        "Écart",
        "Progression"
    ]


    st.dataframe(
        tableau_analyse,
        width="stretch",
        hide_index=True
    )


# ============================================================
# 3. COTISATIONS
# ============================================================

st.divider()

st.header(
    "💳 3. Situation des cotisations"
)


if df_cotisants.empty:

    total_prevu_cotisations = 0.0
    total_verse = 0.0
    total_reste = 0.0

    st.info(
        "Aucun cotisant enregistré."
    )

else:

    total_prevu_cotisations = float(
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


if total_prevu_cotisations > 0:

    taux_collecte = (
        total_verse
        / total_prevu_cotisations
    ) * 100

else:

    taux_collecte = 0.0


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Total prévu",
        format_fcfa(
            total_prevu_cotisations
        )
    )


with c2:

    st.metric(
        "Total versé",
        format_fcfa(
            total_verse
        )
    )


with c3:

    st.metric(
        "Reste à collecter",
        format_fcfa(
            total_reste
        )
    )


with c4:

    st.metric(
        "Taux de collecte",
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


if not df_cotisants.empty:

    resume_listes = (
        df_cotisants
        .groupby(
            "liste",
            as_index=False
        )
        .agg(
            previsionnel=(
                "montant_prevu",
                "sum"
            ),
            verse=(
                "montant_verse",
                "sum"
            ),
            reste=(
                "reste",
                "sum"
            )
        )
    )


    resume_listes["taux"] = 0.0


    masque = (
        resume_listes[
            "previsionnel"
        ] > 0
    )


    resume_listes.loc[
        masque,
        "taux"
    ] = (
        resume_listes.loc[
            masque,
            "verse"
        ]
        /
        resume_listes.loc[
            masque,
            "previsionnel"
        ]
        * 100
    )


    tableau_listes = resume_listes.copy()


    for colonne in [
        "previsionnel",
        "verse",
        "reste"
    ]:

        tableau_listes[
            colonne
        ] = tableau_listes[
            colonne
        ].map(format_fcfa)


    tableau_listes[
        "taux"
    ] = tableau_listes[
        "taux"
    ].map(
        lambda x: f"{x:.1f} %"
    )


    tableau_listes.columns = [
        "Liste",
        "Prévisionnel",
        "Versé",
        "Reste",
        "Taux collecte"
    ]


    st.subheader(
        "Répartition des cotisations"
    )


    st.dataframe(
        tableau_listes,
        width="stretch",
        hide_index=True
    )


# ============================================================
# 4. SUIVI OPERATIONNEL
# ============================================================

st.divider()

st.header(
    "✅ 4. Avancement des préparatifs"
)


if df_taches.empty:

    total_taches = 0
    taches_terminees = 0
    taches_en_cours = 0
    taches_a_faire = 0
    avancement = 0.0

else:

    df_taches["progression"] = (
        pd.to_numeric(
            df_taches["progression"],
            errors="coerce"
        )
        .fillna(0)
    )


    total_taches = int(
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


    taches_en_cours = int(
        len(
            df_taches[
                df_taches[
                    "statut"
                ] == "EN COURS"
            ]
        )
    )


    taches_a_faire = int(
        len(
            df_taches[
                df_taches[
                    "statut"
                ] == "A FAIRE"
            ]
        )
    )


    avancement = float(
        df_taches[
            "progression"
        ].mean()
    )


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Tâches",
        total_taches
    )


with c2:

    st.metric(
        "Terminées",
        taches_terminees
    )


with c3:

    st.metric(
        "En cours",
        taches_en_cours
    )


with c4:

    st.metric(
        "À faire",
        taches_a_faire
    )


st.write(
    f"**Avancement opérationnel moyen : "
    f"{avancement:.1f} %**"
)


st.progress(
    min(
        max(
            avancement / 100,
            0
        ),
        1
    )
)


# ============================================================
# 5. PROCHAINES ECHEANCES
# ============================================================

st.divider()

st.header(
    "📅 5. Prochaines échéances"
)


if df_taches.empty:

    st.info(
        "Aucune tâche planifiée."
    )

else:

    prochaines = df_taches.copy()


    prochaines["date_prevue"] = (
        pd.to_datetime(
            prochaines["date_prevue"],
            errors="coerce"
        )
    )


    prochaines = prochaines[
        prochaines["date_prevue"].notna()
    ]


    prochaines = prochaines[
        prochaines["statut"] != "TERMINE"
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
            "✅ Toutes les tâches planifiées sont terminées."
        )

    else:

        prochaines["Date prévue"] = (
            prochaines[
                "date_prevue"
            ].dt.strftime(
                "%d/%m/%Y"
            )
        )


        prochaines["Progression"] = (
            prochaines[
                "progression"
            ].map(
                lambda x: f"{float(x):.0f} %"
            )
        )


        prochaines["Statut"] = (
            prochaines[
                "statut"
            ].apply(
                statut_tache
            )
        )


        tableau_prochaines = prochaines[
            [
                "nom",
                "categorie",
                "Date prévue",
                "Progression",
                "Statut"
            ]
        ].copy()


        tableau_prochaines.columns = [
            "Tâche",
            "Catégorie",
            "Date prévue",
            "Progression",
            "Statut"
        ]


        st.dataframe(
            tableau_prochaines,
            width="stretch",
            hide_index=True
        )


# ============================================================
# 6. ALERTES
# ============================================================

st.divider()

st.header(
    "⚠️ 6. Alertes et points d'attention"
)


alertes = []


if budget_non_affecte > 0:

    alertes.append(
        "💰 "
        f"{format_fcfa(budget_non_affecte)} "
        "de budget restent non affectés."
    )


if not df_depenses.empty:

    depassements = df_depenses[
        df_depenses[
            "ecart"
        ] > 0
    ]


    if not depassements.empty:

        alertes.append(
            "📈 "
            f"{len(depassements)} dépense(s) "
            "dépassent le montant prévisionnel."
        )


if not df_cotisants.empty:

    non_soldees = df_cotisants[
        df_cotisants[
            "statut"
        ].isin(
            [
                "NON SOLDE",
                "PARTIEL"
            ]
        )
    ]


    if not non_soldees.empty:

        alertes.append(
            "💳 "
            f"{len(non_soldees)} cotisant(s) "
            "ne sont pas encore soldé(s)."
        )


if not df_taches.empty:

    taches_non_terminees = df_taches[
        df_taches[
            "statut"
        ] != "TERMINE"
    ]


    if not taches_non_terminees.empty:

        alertes.append(
            "✅ "
            f"{len(taches_non_terminees)} tâche(s) "
            "ne sont pas encore terminée(s)."
        )


if alertes:

    for alerte in alertes:

        st.warning(
            alerte
        )

else:

    st.success(
        "✅ Aucun point d'attention détecté."
    )


# ============================================================
# 7. ETAT DES COTISANTS
# ============================================================

st.divider()

st.header(
    "👥 7. État des cotisants"
)


if df_cotisants.empty:

    st.info(
        "Aucun cotisant enregistré."
    )

else:

    tableau_cotisants = df_cotisants[
        [
            "nom",
            "liste",
            "montant_prevu",
            "montant_verse",
            "reste",
            "statut"
        ]
    ].copy()


    tableau_cotisants[
        "montant_prevu"
    ] = tableau_cotisants[
        "montant_prevu"
    ].map(format_fcfa)


    tableau_cotisants[
        "montant_verse"
    ] = tableau_cotisants[
        "montant_verse"
    ].map(format_fcfa)


    tableau_cotisants[
        "reste"
    ] = tableau_cotisants[
        "reste"
    ].map(format_fcfa)


    tableau_cotisants[
        "statut"
    ] = tableau_cotisants[
        "statut"
    ].apply(
        statut_cotisation
    )


    tableau_cotisants.columns = [
        "Nom",
        "Liste",
        "Montant prévu",
        "Montant versé",
        "Reste",
        "Statut"
    ]


    st.dataframe(
        tableau_cotisants,
        width="stretch",
        hide_index=True
    )


# ============================================================
# 8. EXPORT CSV
# ============================================================

st.divider()

st.header(
    "📥 8. Export des données"
)


if not df_depenses.empty:

    csv_financier = (
        df_depenses
        .to_csv(
            index=False,
            encoding="utf-8-sig"
        )
    )


    st.download_button(
        "📥 Télécharger le suivi financier CSV",
        data=csv_financier,
        file_name="suivi_financier_obseques.csv",
        mime="text/csv",
        width="stretch"
    )


if not df_cotisants.empty:

    csv_cotisations = (
        df_cotisants
        .to_csv(
            index=False,
            encoding="utf-8-sig"
        )
    )


    st.download_button(
        "📥 Télécharger les cotisations CSV",
        data=csv_cotisations,
        file_name="cotisations_obseques.csv",
        mime="text/csv",
        width="stretch"
    )


if not df_taches.empty:

    csv_taches = (
        df_taches
        .to_csv(
            index=False,
            encoding="utf-8-sig"
        )
    )


    st.download_button(
        "📥 Télécharger le suivi des tâches CSV",
        data=csv_taches,
        file_name="suivi_taches_obseques.csv",
        mime="text/csv",
        width="stretch"
    )


# ============================================================
# 9. SYNTHESE FINALE
# ============================================================

st.divider()

st.header(
    "📝 9. Synthèse exécutive"
)


if jours_restants > 0:

    situation_echeance = (
        "J-" + str(jours_restants)
    )

elif jours_restants == 0:

    situation_echeance = (
        "Jour des obsèques"
    )

else:

    situation_echeance = (
        "Échéance passée"
    )


st.write(
    f"""
### Situation financière

- **Budget prévisionnel :** {format_fcfa(budget_previsionnel)}
- **Budget détaillé :** {format_fcfa(budget_detaille)}
- **Budget non affecté :** {format_fcfa(budget_non_affecte)}
- **Dépenses réelles :** {format_fcfa(depenses_reelles)}
- **Écart budgétaire :** {format_fcfa(ecart)}
- **Taux de réalisation :** {taux_realisation:.1f} %

### Cotisations

- **Total prévu :** {format_fcfa(total_prevu_cotisations)}
- **Total versé :** {format_fcfa(total_verse)}
- **Reste à collecter :** {format_fcfa(total_reste)}
- **Taux de collecte :** {taux_collecte:.1f} %

### Préparatifs

- **Nombre de tâches :** {total_taches}
- **Tâches terminées :** {taches_terminees}
- **Tâches en cours :** {taches_en_cours}
- **Tâches à faire :** {taches_a_faire}
- **Avancement opérationnel :** {avancement:.1f} %

### Échéance

- **Date des obsèques :** 27/08/2026
- **Situation :** {situation_echeance}
"""
)


# ============================================================
# RAPPEL
# ============================================================

st.info(
    "🕊️ Ce reporting constitue une synthèse de pilotage "
    "familiale des obsèques de Feu MAKOSSO POATHY Jean Pierre."
)


# ============================================================
# SIGNATURE
# ============================================================

afficher_signature()

