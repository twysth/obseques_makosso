from pathlib import Path
import pandas as pd


# ============================================================
# CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FICHIER_EXCEL = BASE_DIR / "data" / "depenses.xlsx"

FICHIER_DEPENSES = BASE_DIR / "data" / "depenses_propres.csv"
FICHIER_CATEGORIES = BASE_DIR / "data" / "categories_budget.csv"


# ============================================================
# STRUCTURE DES 10 SOUS-TABLEAUX
# Les numéros correspondent aux lignes Excel.
# ============================================================

SOUS_TABLEAUX = [
    {
        "categorie": "SAFF",
        "debut": 5,
        "fin": 17,
    },
    {
        "categorie": "EXPOSITION A SAFF",
        "debut": 18,
        "fin": 22,
    },
    {
        "categorie": "TRANSPORT",
        "debut": 23,
        "fin": 25,
    },
    {
        "categorie": "CAVEAU",
        "debut": 26,
        "fin": 36,
    },
    {
        "categorie": "VEILLEE A MAYUMBA",
        "debut": 37,
        "fin": 44,
    },
    {
        "categorie": "RESTAURATION A MAYUMBA",
        "debut": 45,
        "fin": 77,
    },
    {
        "categorie": "BOISSON",
        "debut": 78,
        "fin": 81,
    },
    {
        "categorie": "VAISSELLE ET NETTOYAGE",
        "debut": 82,
        "fin": 90,
    },
    {
        "categorie": "COMMUNICATION",
        "debut": 91,
        "fin": 95,
    },
    {
        "categorie": "DIVERS",
        "debut": 96,
        "fin": 100,
    },
]


# ============================================================
# LECTURE DU FICHIER EXCEL
# ============================================================

def lire_excel():
    """Lit le fichier Excel sans utiliser la première ligne comme en-tête."""

    if not FICHIER_EXCEL.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {FICHIER_EXCEL}"
        )

    return pd.read_excel(
        FICHIER_EXCEL,
        header=None
    )


# ============================================================
# CONVERSION DES NOMBRES
# ============================================================

def nettoyer_nombre(valeur):
    """Transforme une valeur Excel en nombre."""

    if pd.isna(valeur):
        return 0.0

    if isinstance(valeur, str):
        valeur = (
            valeur
            .replace("\xa0", "")
            .replace(" ", "")
            .replace(",", ".")
        )

    nombre = pd.to_numeric(
        valeur,
        errors="coerce"
    )

    if pd.isna(nombre):
        return 0.0

    return float(nombre)


# ============================================================
# EXTRACTION DES SOUS-TABLEAUX
# ============================================================

def extraire_sous_tableaux():

    excel = lire_excel()

    toutes_les_depenses = []
    categories = []

    for bloc in SOUS_TABLEAUX:

        categorie = bloc["categorie"]

        # Excel commence à 1
        # Pandas commence à 0
        debut = bloc["debut"] - 1
        fin = bloc["fin"] - 1

        tableau = excel.iloc[
            debut:fin + 1,
            0:4
        ].copy()

        tableau.columns = [
            "DESIGNATION",
            "PRIX_UNITAIRE",
            "QUANTITE",
            "MONTANT"
        ]

        # ----------------------------------------------------
        # Nettoyage
        # ----------------------------------------------------

        tableau["DESIGNATION"] = (
            tableau["DESIGNATION"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        tableau["PRIX_UNITAIRE"] = (
            tableau["PRIX_UNITAIRE"]
            .apply(nettoyer_nombre)
        )

        tableau["QUANTITE"] = (
            tableau["QUANTITE"]
            .apply(nettoyer_nombre)
        )

        tableau["MONTANT"] = (
            tableau["MONTANT"]
            .apply(nettoyer_nombre)
        )

        # ----------------------------------------------------
        # Identifier la ligne TOTAL
        # ----------------------------------------------------

        masque_total = (
            tableau["DESIGNATION"]
            .str.upper()
            .str.contains("TOTAL", na=False)
        )

        lignes_total = tableau[masque_total]

        # Budget global de la catégorie
        budget_previsionnel = 0.0

        if not lignes_total.empty:
            budget_previsionnel = float(
                lignes_total["MONTANT"].iloc[0]
            )

        # ----------------------------------------------------
        # Garder uniquement les vraies dépenses
        # ----------------------------------------------------

        depenses = tableau[
            ~masque_total
            & (tableau["DESIGNATION"] != "")
            & (tableau["DESIGNATION"].str.upper() != "NAN")
        ].copy()

        # Ajouter la catégorie
        depenses.insert(
            0,
            "CATEGORIE",
            categorie
        )

        # ----------------------------------------------------
        # Budget détaillé
        # ----------------------------------------------------

        budget_detaille = float(
            depenses["MONTANT"].sum()
        )

        # Budget restant à détailler
        budget_non_affecte = (
            budget_previsionnel
            - budget_detaille
        )

        # Éviter les petits écarts dus aux arrondis
        if abs(budget_non_affecte) < 0.01:
            budget_non_affecte = 0.0

        # ----------------------------------------------------
        # Statut de détail
        # ----------------------------------------------------

        if budget_previsionnel == 0:
            statut_detail = "SANS BUDGET"

        elif budget_detaille == 0:
            statut_detail = "NON DETAILLE"

        elif budget_non_affecte > 0:
            statut_detail = "PARTIELLEMENT DETAILLE"

        else:
            statut_detail = "DETAILLE"

        # ----------------------------------------------------
        # Table catégorie
        # ----------------------------------------------------

        categories.append(
            {
                "CATEGORIE": categorie,
                "BUDGET_PREVISIONNEL": budget_previsionnel,
                "BUDGET_DETAILLE": budget_detaille,
                "BUDGET_NON_AFFECTE": budget_non_affecte,
                "STATUT_DETAIL": statut_detail,
            }
        )

        toutes_les_depenses.append(
            depenses
        )

    depenses = pd.concat(
        toutes_les_depenses,
        ignore_index=True
    )

    categories = pd.DataFrame(
        categories
    )

    return depenses, categories


# ============================================================
# PREPARATION DES DEPENSES
# ============================================================

def preparer_depenses(depenses):
    """Prépare les colonnes nécessaires au suivi réel."""

    depenses = depenses.copy()

    # Colonnes réelles
    depenses["QUANTITE_REELLE"] = 0.0
    depenses["MONTANT_REEL"] = 0.0

    # Écart réel - prévisionnel
    depenses["ECART"] = (
        depenses["MONTANT_REEL"]
        - depenses["MONTANT"]
    )

    # Progression de la dépense
    depenses["PROGRESSION"] = 0.0

    # Statut
    depenses["STATUT"] = "A FAIRE"

    return depenses


# ============================================================
# PREPARATION DES CATEGORIES
# ============================================================

def preparer_categories(categories):
    """Ajoute les indicateurs nécessaires au tableau de bord."""

    categories = categories.copy()

    categories["POURCENTAGE_DETAIL"] = 0.0

    masque = (
        categories["BUDGET_PREVISIONNEL"] > 0
    )

    categories.loc[masque, "POURCENTAGE_DETAIL"] = (
        categories.loc[masque, "BUDGET_DETAILLE"]
        / categories.loc[masque, "BUDGET_PREVISIONNEL"]
        * 100
    )

    return categories


# ============================================================
# EXPORT
# ============================================================

def exporter_donnees():

    depenses, categories = extraire_sous_tableaux()

    depenses = preparer_depenses(
        depenses
    )

    categories = preparer_categories(
        categories
    )

    # Export dépenses
    depenses.to_csv(
        FICHIER_DEPENSES,
        index=False,
        encoding="utf-8-sig"
    )

    # Export catégories
    categories.to_csv(
        FICHIER_CATEGORIES,
        index=False,
        encoding="utf-8-sig"
    )

    return depenses, categories


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 75)
    print("ANALYSE DU BUDGET DES OBSEQUES")
    print("=" * 75)

    depenses, categories = exporter_donnees()

    # --------------------------------------------------------
    # TABLEAU DES CATEGORIES
    # --------------------------------------------------------

    print("\n--- BUDGET PAR CATEGORIE ---\n")

    affichage = categories[
        [
            "CATEGORIE",
            "BUDGET_PREVISIONNEL",
            "BUDGET_DETAILLE",
            "BUDGET_NON_AFFECTE",
            "POURCENTAGE_DETAIL",
            "STATUT_DETAIL",
        ]
    ]

    print(
        affichage.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # TOTAL GENERAL
    # --------------------------------------------------------

    total_previsionnel = categories[
        "BUDGET_PREVISIONNEL"
    ].sum()

    total_detaille = categories[
        "BUDGET_DETAILLE"
    ].sum()

    total_non_affecte = categories[
        "BUDGET_NON_AFFECTE"
    ].sum()

    print("\n--- TOTAL GENERAL ---\n")

    print(
        f"Budget prévisionnel : "
        f"{total_previsionnel:,.0f} FCFA"
    )

    print(
        f"Budget détaillé     : "
        f"{total_detaille:,.0f} FCFA"
    )

    print(
        f"Budget non affecté  : "
        f"{total_non_affecte:,.0f} FCFA"
    )

    # --------------------------------------------------------
    # CONTROLE
    # --------------------------------------------------------

    print("\n--- CONTROLE ---\n")

    controle = (
        total_previsionnel
        - total_detaille
        - total_non_affecte
    )

    print(
        f"Contrôle : {controle:,.0f} FCFA"
    )

    if abs(controle) < 0.01:
        print("✅ Cohérence des totaux")
    else:
        print("⚠️ Vérifier les données")

    # --------------------------------------------------------
    # FOCUS CAVEAU
    # --------------------------------------------------------

    print("\n--- FOCUS CAVEAU ---\n")

    caveau = categories[
        categories["CATEGORIE"] == "CAVEAU"
    ]

    if not caveau.empty:

        ligne = caveau.iloc[0]

        print(
            f"Budget prévisionnel : "
            f"{ligne['BUDGET_PREVISIONNEL']:,.0f} FCFA"
        )

        print(
            f"Budget détaillé     : "
            f"{ligne['BUDGET_DETAILLE']:,.0f} FCFA"
        )

        print(
            f"Budget non affecté  : "
            f"{ligne['BUDGET_NON_AFFECTE']:,.0f} FCFA"
        )

        print(
            f"Statut              : "
            f"{ligne['STATUT_DETAIL']}"
        )

    print("\nFichiers générés :")

    print(
        f"- {FICHIER_DEPENSES}"
    )

    print(
        f"- {FICHIER_CATEGORIES}"
    )