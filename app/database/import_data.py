from pathlib import Path
import sqlite3
import pandas as pd
import sys


# ============================================================
# CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

FICHIER_CATEGORIES = DATA_DIR / "categories_budget.csv"
FICHIER_DEPENSES = DATA_DIR / "depenses_propres.csv"
DATABASE_PATH = DATA_DIR / "obseques.db"


# ============================================================
# CONNEXION SQLITE
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# VERIFICATION DES FICHIERS
# ============================================================

def verifier_fichiers():

    fichiers = [
        FICHIER_CATEGORIES,
        FICHIER_DEPENSES,
        DATABASE_PATH
    ]

    for fichier in fichiers:

        if not fichier.exists():

            raise FileNotFoundError(
                f"Fichier introuvable : {fichier}"
            )


# ============================================================
# NETTOYAGE DE LA BASE
# ============================================================

def vider_tables():

    connection = get_connection()

    cursor = connection.cursor()

    # L'ordre est important à cause des relations
    cursor.execute("DELETE FROM depenses")
    cursor.execute("DELETE FROM categories")

    # Réinitialiser les identifiants
    cursor.execute(
        "DELETE FROM sqlite_sequence "
        "WHERE name IN ('categories', 'depenses')"
    )

    connection.commit()
    connection.close()


# ============================================================
# IMPORT DES CATEGORIES
# ============================================================

def importer_categories():

    df = pd.read_csv(
        FICHIER_CATEGORIES,
        encoding="utf-8-sig"
    )

    connection = get_connection()

    cursor = connection.cursor()

    nombre_importe = 0

    for _, ligne in df.iterrows():

        cursor.execute(
            """
            INSERT INTO categories (
                nom,
                budget_previsionnel,
                budget_detaille,
                budget_non_affecte,
                statut_detail
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(ligne["CATEGORIE"]),
                float(ligne["BUDGET_PREVISIONNEL"]),
                float(ligne["BUDGET_DETAILLE"]),
                float(ligne["BUDGET_NON_AFFECTE"]),
                str(ligne["STATUT_DETAIL"])
            )
        )

        nombre_importe += 1

    connection.commit()
    connection.close()

    return nombre_importe


# ============================================================
# RECUPERER ID CATEGORIE
# ============================================================

def recuperer_categories():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, nom
        FROM categories
        """
    )

    resultat = {
        ligne["nom"]: ligne["id"]
        for ligne in cursor.fetchall()
    }

    connection.close()

    return resultat


# ============================================================
# IMPORT DES DEPENSES
# ============================================================

def importer_depenses():

    df = pd.read_csv(
        FICHIER_DEPENSES,
        encoding="utf-8-sig"
    )

    categories = recuperer_categories()

    connection = get_connection()

    cursor = connection.cursor()

    nombre_importe = 0

    for _, ligne in df.iterrows():

        categorie = str(
            ligne["CATEGORIE"]
        ).strip()

        if categorie not in categories:

            raise ValueError(
                f"Catégorie inconnue : {categorie}"
            )

        categorie_id = categories[categorie]

        cursor.execute(
            """
            INSERT INTO depenses (
                categorie_id,
                designation,
                prix_unitaire_prevu,
                quantite_prevue,
                montant_prevu,
                prix_unitaire_reel,
                quantite_reelle,
                montant_reel,
                ecart,
                progression,
                statut
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                categorie_id,

                str(
                    ligne["DESIGNATION"]
                ),

                float(
                    ligne["PRIX_UNITAIRE"]
                ),

                float(
                    ligne["QUANTITE"]
                ),

                float(
                    ligne["MONTANT"]
                ),

                0.0,
                0.0,
                0.0,

                float(
                    ligne["ECART"]
                ),

                float(
                    ligne["PROGRESSION"]
                ),

                str(
                    ligne["STATUT"]
                )
            )
        )

        nombre_importe += 1

    connection.commit()
    connection.close()

    return nombre_importe


# ============================================================
# CONTROLE DES DONNEES
# ============================================================

def controle_base():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Nombre de catégories
    # --------------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) AS nombre FROM categories"
    )

    nombre_categories = cursor.fetchone()["nombre"]

    # --------------------------------------------------------
    # Nombre de dépenses
    # --------------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) AS nombre FROM depenses"
    )

    nombre_depenses = cursor.fetchone()["nombre"]

    # --------------------------------------------------------
    # Budget prévisionnel
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(budget_previsionnel), 0)
        AS total
        FROM categories
        """
    )

    budget_previsionnel = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # Budget détaillé
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(budget_detaille), 0)
        AS total
        FROM categories
        """
    )

    budget_detaille = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # Budget non affecté
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(budget_non_affecte), 0)
        AS total
        FROM categories
        """
    )

    budget_non_affecte = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # Total des dépenses détaillées
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(montant_prevu), 0)
        AS total
        FROM depenses
        """
    )

    total_depenses = cursor.fetchone()["total"]

    connection.close()

    return {
        "nombre_categories": nombre_categories,
        "nombre_depenses": nombre_depenses,
        "budget_previsionnel": budget_previsionnel,
        "budget_detaille": budget_detaille,
        "budget_non_affecte": budget_non_affecte,
        "total_depenses": total_depenses
    }


# ============================================================
# AFFICHAGE
# ============================================================

def afficher_resultat(resultat):

    print()
    print("=" * 70)
    print("CONTROLE DE LA BASE SQLITE")
    print("=" * 70)

    print(
        f"\nNombre de catégories : "
        f"{resultat['nombre_categories']}"
    )

    print(
        f"Nombre de dépenses   : "
        f"{resultat['nombre_depenses']}"
    )

    print(
        f"\nBudget prévisionnel  : "
        f"{resultat['budget_previsionnel']:,.0f} FCFA"
    )

    print(
        f"Budget détaillé      : "
        f"{resultat['budget_detaille']:,.0f} FCFA"
    )

    print(
        f"Budget non affecté   : "
        f"{resultat['budget_non_affecte']:,.0f} FCFA"
    )

    print(
        f"Dépenses détaillées  : "
        f"{resultat['total_depenses']:,.0f} FCFA"
    )

    # Contrôle principal
    controle = (
        resultat["budget_previsionnel"]
        - resultat["budget_detaille"]
        - resultat["budget_non_affecte"]
    )

    print(
        f"\nContrôle budget      : "
        f"{controle:,.0f} FCFA"
    )

    # Contrôle détaillé
    ecart_detail = (
        resultat["budget_detaille"]
        - resultat["total_depenses"]
    )

    print(
        f"Contrôle détail      : "
        f"{ecart_detail:,.0f} FCFA"
    )

    if (
        abs(controle) < 0.01
        and abs(ecart_detail) < 0.01
    ):
        print(
            "\n✅ IMPORT SQLITE VALIDE"
        )
    else:
        print(
            "\n⚠️ ANOMALIE DETECTEE"
        )


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    print("=" * 70)
    print("IMPORT DES DONNEES VERS SQLITE")
    print("=" * 70)

    try:

        verifier_fichiers()

        print(
            "\n1. Nettoyage des anciennes données..."
        )

        vider_tables()

        print(
            "✅ Tables nettoyées"
        )

        print(
            "\n2. Import des catégories..."
        )

        nombre_categories = importer_categories()

        print(
            f"✅ {nombre_categories} catégories importées"
        )

        print(
            "\n3. Import des dépenses..."
        )

        nombre_depenses = importer_depenses()

        print(
            f"✅ {nombre_depenses} dépenses importées"
        )

        resultat = controle_base()

        afficher_resultat(
            resultat
        )

    except Exception as erreur:

        print(
            "\n❌ ERREUR :"
        )

        print(
            erreur
        )

        sys.exit(1)


if __name__ == "__main__":
    main()