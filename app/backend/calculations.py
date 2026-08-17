from datetime import date
import sqlite3
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = BASE_DIR / "data" / "obseques.db"

DATE_OBSEQUES = date(
    2026,
    8,
    27
)


# ============================================================
# CONNEXION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# COMPTE A REBOURS
# ============================================================

def jours_avant_obseques(
    date_reference=None
):
    """
    Calcule le nombre de jours avant le 27 août 2026.
    """

    if date_reference is None:
        date_reference = date.today()

    return (
        DATE_OBSEQUES
        - date_reference
    ).days


# ============================================================
# SUIVI FINANCIER GLOBAL
# ============================================================

def calculer_suivi_financier():

    connection = get_connection()

    resultat = connection.execute(
        """
        SELECT
            COALESCE(
                SUM(montant_prevu),
                0
            ) AS previsionnel,

            COALESCE(
                SUM(montant_reel),
                0
            ) AS reel
        FROM depenses
        """
    ).fetchone()

    connection.close()

    previsionnel = float(
        resultat["previsionnel"]
    )

    reel = float(
        resultat["reel"]
    )

    ecart = (
        reel
        - previsionnel
    )

    if previsionnel > 0:

        progression = (
            reel
            / previsionnel
        ) * 100

    else:

        progression = 0

    return {
        "previsionnel": previsionnel,
        "reel": reel,
        "ecart": ecart,
        "progression": progression
    }


# ============================================================
# SUIVI FINANCIER PAR CATEGORIE
# ============================================================

def calculer_suivi_par_categorie():

    connection = get_connection()

    lignes = connection.execute(
        """
        SELECT
            c.nom AS categorie,

            COALESCE(
                SUM(d.montant_prevu),
                0
            ) AS previsionnel,

            COALESCE(
                SUM(d.montant_reel),
                0
            ) AS reel

        FROM categories c

        LEFT JOIN depenses d
            ON d.categorie_id = c.id

        GROUP BY c.id, c.nom

        ORDER BY c.id
        """
    ).fetchall()

    connection.close()

    resultat = []

    for ligne in lignes:

        previsionnel = float(
            ligne["previsionnel"]
        )

        reel = float(
            ligne["reel"]
        )

        ecart = (
            reel
            - previsionnel
        )

        if previsionnel > 0:

            progression = (
                reel
                / previsionnel
            ) * 100

        else:

            progression = 0

        resultat.append({
            "categorie": ligne["categorie"],
            "previsionnel": previsionnel,
            "reel": reel,
            "ecart": ecart,
            "progression": min(
                max(progression, 0),
                100
            )
        })

    return resultat


# ============================================================
# SUIVI OPERATIONNEL DES TACHES
# ============================================================

def calculer_suivi_taches():

    connection = get_connection()

    resultat = connection.execute(
        """
        SELECT
            COUNT(*) AS total,

            SUM(
                CASE
                    WHEN statut = 'TERMINE'
                    THEN 1
                    ELSE 0
                END
            ) AS terminees,

            SUM(
                CASE
                    WHEN statut = 'EN COURS'
                    THEN 1
                    ELSE 0
                END
            ) AS en_cours

        FROM taches
        """
    ).fetchone()

    progression_moyenne = connection.execute(
        """
        SELECT
            COALESCE(
                AVG(progression),
                0
            ) AS moyenne
        FROM taches
        """
    ).fetchone()["moyenne"]

    connection.close()

    total = int(
        resultat["total"] or 0
    )

    terminees = int(
        resultat["terminees"] or 0
    )

    en_cours = int(
        resultat["en_cours"] or 0
    )

    a_faire = max(
        total
        - terminees
        - en_cours,
        0
    )

    return {
        "total": total,
        "terminees": terminees,
        "en_cours": en_cours,
        "a_faire": a_faire,
        "progression": float(
            progression_moyenne
        )
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("CALCULS DU PROJET OBSEQUES")
    print("=" * 70)

    jours = jours_avant_obseques()

    print(
        f"\nJours avant les obsèques : "
        f"{jours}"
    )

    financier = (
        calculer_suivi_financier()
    )

    print(
        "\n--- SUIVI FINANCIER ---"
    )

    print(
        f"Prévisionnel : "
        f"{financier['previsionnel']:,.0f} FCFA"
    )

    print(
        f"Réel         : "
        f"{financier['reel']:,.0f} FCFA"
    )

    print(
        f"Écart        : "
        f"{financier['ecart']:,.0f} FCFA"
    )

    print(
        f"Progression  : "
        f"{financier['progression']:.1f} %"
    )

    taches = (
        calculer_suivi_taches()
    )

    print(
        "\n--- SUIVI OPERATIONNEL ---"
    )

    print(
        f"Tâches       : "
        f"{taches['total']}"
    )

    print(
        f"Terminées    : "
        f"{taches['terminees']}"
    )

    print(
        f"En cours     : "
        f"{taches['en_cours']}"
    )

    print(
        f"À faire      : "
        f"{taches['a_faire']}"
    )

    print(
        f"Progression  : "
        f"{taches['progression']:.1f} %"
    )