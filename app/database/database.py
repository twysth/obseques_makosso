import sqlite3
from pathlib import Path


# ============================================================
# CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATA_DIR / "obseques.db"


# ============================================================
# CONNEXION
# ============================================================

def get_connection():
    """
    Retourne une connexion SQLite.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    # Permet de respecter les relations FOREIGN KEY
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# CREATION DES TABLES
# ============================================================

def create_tables():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL UNIQUE,

            budget_previsionnel REAL NOT NULL DEFAULT 0,

            budget_detaille REAL NOT NULL DEFAULT 0,

            budget_non_affecte REAL NOT NULL DEFAULT 0,

            statut_detail TEXT NOT NULL DEFAULT 'NON DETAILLE'
        )
        """
    )

    # --------------------------------------------------------
    # DEPENSES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            categorie_id INTEGER NOT NULL,

            designation TEXT NOT NULL,

            prix_unitaire_prevu REAL NOT NULL DEFAULT 0,

            quantite_prevue REAL NOT NULL DEFAULT 0,

            montant_prevu REAL NOT NULL DEFAULT 0,

            prix_unitaire_reel REAL NOT NULL DEFAULT 0,

            quantite_reelle REAL NOT NULL DEFAULT 0,

            montant_reel REAL NOT NULL DEFAULT 0,

            ecart REAL NOT NULL DEFAULT 0,

            progression REAL NOT NULL DEFAULT 0,

            statut TEXT NOT NULL DEFAULT 'A FAIRE',

            FOREIGN KEY (categorie_id)
                REFERENCES categories(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # COTISANTS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cotisants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL,

            liste TEXT NOT NULL,

            telephone TEXT,

            montant_prevu REAL NOT NULL DEFAULT 0,

            montant_verse REAL NOT NULL DEFAULT 0,

            reste REAL NOT NULL DEFAULT 0,

            statut TEXT NOT NULL DEFAULT 'NON SOLDE',

            CHECK (
                liste IN (
                    'Famille Bayema',
                    'Enfants'
                )
            )
        )
        """
    )

    # --------------------------------------------------------
    # VERSEMENTS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS versements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            cotisant_id INTEGER NOT NULL,

            date_versement TEXT NOT NULL,

            montant REAL NOT NULL DEFAULT 0,

            commentaire TEXT,

            FOREIGN KEY (cotisant_id)
                REFERENCES cotisants(id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # TACHES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS taches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            categorie_id INTEGER,

            nom TEXT NOT NULL,

            description TEXT,

            progression REAL NOT NULL DEFAULT 0,

            statut TEXT NOT NULL DEFAULT 'A FAIRE',

            date_prevue TEXT,

            date_realisation TEXT,

            FOREIGN KEY (categorie_id)
                REFERENCES categories(id)
                ON DELETE SET NULL
        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# VERIFICATION DES TABLES
# ============================================================

def lister_tables():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    )

    tables = [
        row["name"]
        for row in cursor.fetchall()
    ]

    connection.close()

    return tables


# ============================================================
# TEST DIRECT
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("INITIALISATION DE LA BASE SQLITE")
    print("=" * 60)

    create_tables()

    print(
        f"\nBase de données : {DATABASE_PATH}"
    )

    print("\nTables créées :")

    for table in lister_tables():
        print(f"  ✅ {table}")