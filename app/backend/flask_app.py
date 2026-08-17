from pathlib import Path
from datetime import date
import sqlite3
import os
import secrets
import hmac

from flask import Flask, jsonify, request
from flask_cors import CORS


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = BASE_DIR / "data" / "obseques.db"

app = Flask(__name__)

# ============================================================
# CORS
# ============================================================
# Autorise le frontend Streamlit / autres interfaces
# à communiquer avec l'API Flask.

CORS(app)


# ============================================================
# AUTHENTIFICATION ADMINISTRATEUR
# ============================================================

ADMIN_PASSWORD = os.getenv(
    "OBSEQUES_ADMIN_PASSWORD"
)

# Sessions administrateur en mémoire
ADMIN_SESSIONS = set()


def verifier_mot_de_passe(password):
    """Vérifie le mot de passe administrateur."""

    if not ADMIN_PASSWORD:
        return False

    password_bytes = str(
        password
    ).encode("utf-8")

    admin_password_bytes = str(
        ADMIN_PASSWORD
    ).encode("utf-8")

    return hmac.compare_digest(
        password_bytes,
        admin_password_bytes
    )


def verifier_token_admin():
    """
    Vérifie si la requête contient
    un token administrateur valide.
    """

    token = request.headers.get(
        "X-Admin-Token"
    )

    if not token:
        return False

    return token in ADMIN_SESSIONS


# ============================================================
# CONNEXION SQLITE
# ============================================================

def get_connection():
    """Ouvre une connexion à SQLite."""

    if not DATABASE_PATH.exists():

        raise FileNotFoundError(
            f"Base de données introuvable : {DATABASE_PATH}"
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# OUTIL : SQLITE ROW -> DICTIONNAIRE
# ============================================================

def row_to_dict(row):

    if row is None:
        return None

    return dict(row)


# ============================================================
# OUTIL : MASQUAGE DU TELEPHONE
# ============================================================

def masquer_telephone(numero):
    """
    Masque le numéro sauf les 4 derniers chiffres.
    """

    if not numero:
        return ""

    numero = str(
        numero
    ).strip()

    if len(numero) <= 4:
        return "••••"

    return (
        "••••••"
        + numero[-4:]
    )


# ============================================================
# ROUTE DE TEST
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def accueil():

    return jsonify({
        "application": (
            "Obsèques MAKOSSO POATHY "
            "Jean Pierre"
        ),
        "service": "API Flask",
        "statut": "OK"
    })


# ============================================================
# ETAT DE L'API
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    try:

        connection = get_connection()

        connection.execute(
            "SELECT 1"
        )

        connection.close()

        return jsonify({
            "status": "ok",
            "database": "connected"
        })

    except Exception as erreur:

        return jsonify({
            "status": "error",
            "database": "disconnected",
            "message": str(erreur)
        }), 500


# ============================================================
# CONNEXION ADMINISTRATEUR
# ============================================================

@app.route(
    "/api/admin/login",
    methods=["POST"]
)
def admin_login():

    data = request.get_json(
        force=True,
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "error": "Données JSON absentes."
        }), 400

    password = data.get(
        "password",
        ""
    )

    if not verifier_mot_de_passe(
        password
    ):

        return jsonify({
            "success": False,
            "error": "Mot de passe incorrect."
        }), 401

    token = secrets.token_urlsafe(
        32
    )

    ADMIN_SESSIONS.add(
        token
    )

    return jsonify({
        "success": True,
        "token": token
    })


# ============================================================
# DECONNEXION ADMINISTRATEUR
# ============================================================

@app.route(
    "/api/admin/logout",
    methods=["POST"]
)
def admin_logout():

    token = request.headers.get(
        "X-Admin-Token"
    )

    if token:

        ADMIN_SESSIONS.discard(
            token
        )

    return jsonify({
        "success": True
    })


# ============================================================
# CATEGORIES
# ============================================================

@app.route(
    "/api/categories",
    methods=["GET"]
)
def categories():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            nom,
            budget_previsionnel,
            budget_detaille,
            budget_non_affecte,
            statut_detail
        FROM categories
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return jsonify([
        row_to_dict(row)
        for row in rows
    ])


# ============================================================
# UNE CATEGORIE
# ============================================================

@app.route(
    "/api/categories/<int:category_id>",
    methods=["GET"]
)
def categorie(category_id):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            nom,
            budget_previsionnel,
            budget_detaille,
            budget_non_affecte,
            statut_detail
        FROM categories
        WHERE id = ?
        """,
        (category_id,)
    ).fetchone()

    connection.close()

    if row is None:

        return jsonify({
            "error": "Catégorie introuvable"
        }), 404

    return jsonify(
        row_to_dict(row)
    )


# ============================================================
# DEPENSES - LECTURE
# ============================================================

@app.route(
    "/api/depenses",
    methods=["GET"]
)
def depenses():

    categorie = request.args.get(
        "categorie"
    )

    connection = get_connection()

    if categorie:

        rows = connection.execute(
            """
            SELECT
                d.id,
                c.nom AS categorie,
                d.designation,
                d.prix_unitaire_prevu,
                d.quantite_prevue,
                d.montant_prevu,
                d.prix_unitaire_reel,
                d.quantite_reelle,
                d.montant_reel,
                d.ecart,
                d.progression,
                d.statut
            FROM depenses d
            JOIN categories c
                ON d.categorie_id = c.id
            WHERE c.nom = ?
            ORDER BY d.id
            """,
            (categorie,)
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT
                d.id,
                c.nom AS categorie,
                d.designation,
                d.prix_unitaire_prevu,
                d.quantite_prevue,
                d.montant_prevu,
                d.prix_unitaire_reel,
                d.quantite_reelle,
                d.montant_reel,
                d.ecart,
                d.progression,
                d.statut
            FROM depenses d
            JOIN categories c
                ON d.categorie_id = c.id
            ORDER BY d.id
            """
        ).fetchall()

    connection.close()

    return jsonify([
        row_to_dict(row)
        for row in rows
    ])


# ============================================================
# UNE DEPENSE - LECTURE
# ============================================================

@app.route(
    "/api/depenses/<int:depense_id>",
    methods=["GET"]
)
def depense(depense_id):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            d.id,
            c.nom AS categorie,
            d.designation,
            d.prix_unitaire_prevu,
            d.quantite_prevue,
            d.montant_prevu,
            d.prix_unitaire_reel,
            d.quantite_reelle,
            d.montant_reel,
            d.ecart,
            d.progression,
            d.statut
        FROM depenses d
        JOIN categories c
            ON d.categorie_id = c.id
        WHERE d.id = ?
        """,
        (depense_id,)
    ).fetchone()

    connection.close()

    if row is None:

        return jsonify({
            "error": "Dépense introuvable."
        }), 404

    return jsonify(
        row_to_dict(row)
    )


# ============================================================
# DEPENSE - MISE A JOUR DU REEL - ADMIN
# ============================================================

@app.route(
    "/api/depenses/<int:depense_id>",
    methods=["PUT"]
)
def modifier_depense(depense_id):

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    data = request.get_json(
        force=True,
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Données JSON absentes."
        }), 400

    connection = get_connection()

    depense_existante = connection.execute(
        """
        SELECT *
        FROM depenses
        WHERE id = ?
        """,
        (depense_id,)
    ).fetchone()

    if depense_existante is None:

        connection.close()

        return jsonify({
            "error": "Dépense introuvable."
        }), 404

    montant_prevu = float(
        depense_existante[
            "montant_prevu"
        ]
        or 0
    )

    try:

        quantite_reelle = float(
            data.get(
                "quantite_reelle",
                depense_existante[
                    "quantite_reelle"
                ] or 0
            )
        )

        montant_reel = float(
            data.get(
                "montant_reel",
                depense_existante[
                    "montant_reel"
                ] or 0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        connection.close()

        return jsonify({
            "error": (
                "Les données réelles doivent "
                "être numériques."
            )
        }), 400

    if quantite_reelle < 0:

        connection.close()

        return jsonify({
            "error": (
                "La quantité réelle "
                "ne peut pas être négative."
            )
        }), 400

    if montant_reel < 0:

        connection.close()

        return jsonify({
            "error": (
                "Le montant réel "
                "ne peut pas être négatif."
            )
        }), 400

    if quantite_reelle > 0:

        prix_unitaire_reel = (
            montant_reel
            / quantite_reelle
        )

    else:

        prix_unitaire_reel = 0

    if montant_prevu > 0:

        progression = (
            montant_reel
            / montant_prevu
        ) * 100

    else:

        progression = 0

    progression = max(
        0,
        min(
            progression,
            100
        )
    )

    if montant_reel <= 0:

        statut = "A FAIRE"

    elif progression < 100:

        statut = "EN COURS"

    else:

        statut = "TERMINE"

    ecart = (
        montant_reel
        - montant_prevu
    )

    connection.execute(
        """
        UPDATE depenses
        SET
            prix_unitaire_reel = ?,
            quantite_reelle = ?,
            montant_reel = ?,
            ecart = ?,
            progression = ?,
            statut = ?
        WHERE id = ?
        """,
        (
            prix_unitaire_reel,
            quantite_reelle,
            montant_reel,
            ecart,
            progression,
            statut,
            depense_id
        )
    )

    connection.commit()

    connection.close()

    return jsonify({
        "message": (
            "Suivi de la dépense mis à jour."
        ),
        "id": depense_id,
        "prix_unitaire_reel": (
            prix_unitaire_reel
        ),
        "quantite_reelle": (
            quantite_reelle
        ),
        "montant_reel": (
            montant_reel
        ),
        "ecart": ecart,
        "progression": progression,
        "statut": statut
    })


# ============================================================
# SUPPRIMER UNE DEPENSE - ADMIN
# ============================================================

@app.route(
    "/api/depenses/<int:depense_id>",
    methods=["DELETE"]
)
def supprimer_depense(depense_id):

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    connection = get_connection()

    depense_existante = connection.execute(
        """
        SELECT
            id,
            designation
        FROM depenses
        WHERE id = ?
        """,
        (depense_id,)
    ).fetchone()

    if depense_existante is None:

        connection.close()

        return jsonify({
            "error": "Dépense introuvable."
        }), 404

    connection.execute(
        """
        DELETE FROM depenses
        WHERE id = ?
        """,
        (depense_id,)
    )

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Dépense supprimée définitivement.",
        "id": depense_id,
        "designation": depense_existante[
            "designation"
        ]
    })


# ============================================================
# TABLEAU DE BORD / BUDGET GLOBAL
# ============================================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def dashboard():

    connection = get_connection()

    budget = connection.execute(
        """
        SELECT
            COALESCE(
                SUM(budget_previsionnel),
                0
            ) AS budget_previsionnel,

            COALESCE(
                SUM(budget_detaille),
                0
            ) AS budget_detaille,

            COALESCE(
                SUM(budget_non_affecte),
                0
            ) AS budget_non_affecte

        FROM categories
        """
    ).fetchone()

    reel = connection.execute(
        """
        SELECT
            COALESCE(
                SUM(montant_reel),
                0
            ) AS montant_reel
        FROM depenses
        """
    ).fetchone()

    nombre_categories = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM categories
        """
    ).fetchone()["total"]

    nombre_depenses = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM depenses
        """
    ).fetchone()["total"]

    depenses_terminees = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM depenses
        WHERE statut = 'TERMINE'
        """
    ).fetchone()["total"]

    connection.close()

    budget_previsionnel = float(
        budget["budget_previsionnel"] or 0
    )

    montant_reel = float(
        reel["montant_reel"] or 0
    )

    budget_detaille = float(
        budget["budget_detaille"] or 0
    )

    budget_non_affecte = float(
        budget["budget_non_affecte"] or 0
    )

    ecart = (
        montant_reel
        - budget_previsionnel
    )

    if budget_previsionnel > 0:

        progression_budget = (
            montant_reel
            / budget_previsionnel
        ) * 100

    else:

        progression_budget = 0

    return jsonify({
        "budget_previsionnel": (
            budget_previsionnel
        ),
        "budget_detaille": (
            budget_detaille
        ),
        "budget_non_affecte": (
            budget_non_affecte
        ),
        "montant_reel": (
            montant_reel
        ),
        "ecart": (
            ecart
        ),
        "progression_budget": (
            progression_budget
        ),
        "nombre_categories": (
            int(nombre_categories)
        ),
        "nombre_depenses": (
            int(nombre_depenses)
        ),
        "depenses_terminees": (
            int(depenses_terminees)
        )
    })


# ============================================================
# COTISANTS - LECTURE
# ============================================================

@app.route(
    "/api/cotisants",
    methods=["GET"]
)
def get_cotisants():

    admin = verifier_token_admin()

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            nom,
            liste,
            telephone,
            montant_prevu,
            montant_verse,
            reste,
            statut
        FROM cotisants
        ORDER BY liste, nom
        """
    ).fetchall()

    connection.close()

    resultat = []

    for row in rows:

        item = row_to_dict(
            row
        )

        telephone = item.pop(
            "telephone",
            ""
        )

        if admin:

            item["telephone"] = (
                telephone
            )

        else:

            item["telephone"] = (
                masquer_telephone(
                    telephone
                )
            )

        resultat.append(
            item
        )

    return jsonify(
        resultat
    )


# ============================================================
# AJOUTER UN COTISANT - ADMIN
# ============================================================

@app.route(
    "/api/cotisants",
    methods=["POST"]
)
def ajouter_cotisant():

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    data = request.get_json(
        force=True,
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Données JSON absentes."
        }), 400

    champs_obligatoires = [
        "nom",
        "liste",
        "telephone",
        "montant_prevu"
    ]

    for champ in champs_obligatoires:

        if champ not in data:

            return jsonify({
                "error": (
                    f"Champ manquant : {champ}"
                )
            }), 400

    nom = str(
        data["nom"]
    ).strip()

    liste = str(
        data["liste"]
    ).strip()

    telephone = str(
        data["telephone"]
    ).strip()

    try:

        montant_prevu = float(
            data["montant_prevu"]
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error": (
                "Le montant prévu "
                "doit être numérique."
            )
        }), 400

    if montant_prevu < 0:

        return jsonify({
            "error": (
                "Le montant prévu "
                "ne peut pas être négatif."
            )
        }), 400

    if liste not in [
        "Famille Bayema",
        "Enfants"
    ]:

        return jsonify({
            "error": "Liste invalide."
        }), 400

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO cotisants (
            nom,
            liste,
            telephone,
            montant_prevu,
            montant_verse,
            reste,
            statut
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nom,
            liste,
            telephone,
            montant_prevu,
            0,
            montant_prevu,
            "NON SOLDE"
        )
    )

    connection.commit()

    cotisant_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "message": "Cotisant ajouté.",
        "id": cotisant_id
    }), 201


# ============================================================
# MODIFIER UN COTISANT - ADMIN
# ============================================================

@app.route(
    "/api/cotisants/<int:cotisant_id>",
    methods=["PUT"]
)
def modifier_cotisant(cotisant_id):

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    data = request.get_json(
        force=True,
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Données JSON absentes."
        }), 400

    connection = get_connection()

    ancien = connection.execute(
        """
        SELECT *
        FROM cotisants
        WHERE id = ?
        """,
        (cotisant_id,)
    ).fetchone()

    if ancien is None:

        connection.close()

        return jsonify({
            "error": "Cotisant introuvable."
        }), 404

    nom = str(
        data.get(
            "nom",
            ancien["nom"]
        )
    ).strip()

    liste = str(
        data.get(
            "liste",
            ancien["liste"]
        )
    ).strip()

    telephone = str(
        data.get(
            "telephone",
            ancien["telephone"] or ""
        )
    ).strip()

    try:

        montant_prevu = float(
            data.get(
                "montant_prevu",
                ancien["montant_prevu"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        connection.close()

        return jsonify({
            "error": "Montant prévu invalide."
        }), 400

    if montant_prevu < 0:

        connection.close()

        return jsonify({
            "error": (
                "Le montant prévu "
                "ne peut pas être négatif."
            )
        }), 400

    if liste not in [
        "Famille Bayema",
        "Enfants"
    ]:

        connection.close()

        return jsonify({
            "error": "Liste invalide."
        }), 400

    montant_verse = float(
        ancien["montant_verse"] or 0
    )

    reste = max(
        montant_prevu - montant_verse,
        0
    )

    if montant_verse > montant_prevu:

        statut = "SUPER"

    elif montant_verse == montant_prevu:

        statut = "SOLDE"

    elif montant_verse > 0:

        statut = "PARTIEL"

    else:

        statut = "NON SOLDE"

    connection.execute(
        """
        UPDATE cotisants
        SET
            nom = ?,
            liste = ?,
            telephone = ?,
            montant_prevu = ?,
            reste = ?,
            statut = ?
        WHERE id = ?
        """,
        (
            nom,
            liste,
            telephone,
            montant_prevu,
            reste,
            statut,
            cotisant_id
        )
    )

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Cotisant modifié."
    })


# ============================================================
# SUPPRIMER UN COTISANT - ADMIN
# ============================================================

@app.route(
    "/api/cotisants/<int:cotisant_id>",
    methods=["DELETE"]
)
def supprimer_cotisant(cotisant_id):

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM cotisants
        WHERE id = ?
        """,
        (cotisant_id,)
    )

    if cursor.rowcount == 0:

        connection.close()

        return jsonify({
            "error": "Cotisant introuvable."
        }), 404

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Cotisant supprimé."
    })


# ============================================================
# VERSEMENTS - ADMIN
# ============================================================

@app.route(
    "/api/versements",
    methods=["POST"]
)
def ajouter_versement():

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    data = request.get_json(
        force=True,
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Données JSON absentes."
        }), 400

    cotisant_id = data.get(
        "cotisant_id"
    )

    montant = data.get(
        "montant"
    )

    date_versement = data.get(
        "date_versement"
    )

    commentaire = data.get(
        "commentaire",
        ""
    )

    if (
        cotisant_id is None
        or montant is None
        or not date_versement
    ):

        return jsonify({
            "error": (
                "cotisant_id, montant et "
                "date_versement sont obligatoires."
            )
        }), 400

    try:

        cotisant_id = int(
            cotisant_id
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error": "cotisant_id invalide."
        }), 400

    try:

        montant = float(
            montant
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error": "Montant invalide."
        }), 400

    if montant <= 0:

        return jsonify({
            "error": (
                "Le montant du versement "
                "doit être supérieur à 0."
            )
        }), 400

    connection = get_connection()

    cotisant = connection.execute(
        """
        SELECT *
        FROM cotisants
        WHERE id = ?
        """,
        (cotisant_id,)
    ).fetchone()

    if cotisant is None:

        connection.close()

        return jsonify({
            "error": "Cotisant introuvable."
        }), 404

    montant_prevu = float(
        cotisant["montant_prevu"] or 0
    )

    montant_deja_verse = float(
        cotisant["montant_verse"] or 0
    )

    nouveau_verse = (
        montant_deja_verse
        + montant
    )

    reste = max(
        montant_prevu - nouveau_verse,
        0
    )

    if nouveau_verse > montant_prevu:

        statut = "SUPER"

    elif nouveau_verse == montant_prevu:

        statut = "SOLDE"

    elif nouveau_verse > 0:

        statut = "PARTIEL"

    else:

        statut = "NON SOLDE"

    connection.execute(
        """
        INSERT INTO versements (
            cotisant_id,
            date_versement,
            montant,
            commentaire
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            cotisant_id,
            date_versement,
            montant,
            commentaire
        )
    )

    connection.execute(
        """
        UPDATE cotisants
        SET
            montant_verse = ?,
            reste = ?,
            statut = ?
        WHERE id = ?
        """,
        (
            nouveau_verse,
            reste,
            statut,
            cotisant_id
        )
    )

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Versement enregistré.",
        "montant_verse": nouveau_verse,
        "reste": reste,
        "statut": statut
    }), 201


# ============================================================
# VERSEMENTS - LECTURE
# ============================================================

@app.route(
    "/api/versements",
    methods=["GET"]
)
def get_versements():

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    cotisant_id = request.args.get(
        "cotisant_id"
    )

    connection = get_connection()

    if cotisant_id:

        try:

            cotisant_id = int(
                cotisant_id
            )

        except (
            TypeError,
            ValueError
        ):

            connection.close()

            return jsonify({
                "error": "cotisant_id invalide."
            }), 400

        rows = connection.execute(
            """
            SELECT
                id,
                cotisant_id,
                date_versement,
                montant,
                commentaire
            FROM versements
            WHERE cotisant_id = ?
            ORDER BY date_versement DESC, id DESC
            """,
            (cotisant_id,)
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT
                id,
                cotisant_id,
                date_versement,
                montant,
                commentaire
            FROM versements
            ORDER BY date_versement DESC, id DESC
            """
        ).fetchall()

    connection.close()

    return jsonify([
        row_to_dict(row)
        for row in rows
    ])


# ============================================================
# SUPPRIMER UN VERSEMENT - ADMIN
# ============================================================

@app.route(
    "/api/versements/<int:versement_id>",
    methods=["DELETE"]
)
def supprimer_versement(versement_id):

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    connection = get_connection()

    versement = connection.execute(
        """
        SELECT
            id,
            cotisant_id,
            montant
        FROM versements
        WHERE id = ?
        """,
        (versement_id,)
    ).fetchone()

    if versement is None:

        connection.close()

        return jsonify({
            "error": "Versement introuvable."
        }), 404

    cotisant_id = int(
        versement["cotisant_id"]
    )

    connection.execute(
        """
        DELETE FROM versements
        WHERE id = ?
        """,
        (versement_id,)
    )

    # Recalcul du total versé du cotisant
    total_verse = connection.execute(
        """
        SELECT
            COALESCE(
                SUM(montant),
                0
            ) AS total
        FROM versements
        WHERE cotisant_id = ?
        """,
        (cotisant_id,)
    ).fetchone()["total"]

    cotisant = connection.execute(
        """
        SELECT
            montant_prevu
        FROM cotisants
        WHERE id = ?
        """,
        (cotisant_id,)
    ).fetchone()

    if cotisant is not None:

        montant_prevu = float(
            cotisant["montant_prevu"] or 0
        )

        total_verse = float(
            total_verse or 0
        )

        reste = max(
            montant_prevu - total_verse,
            0
        )

        if total_verse > montant_prevu:

            statut = "SUPER"

        elif total_verse == montant_prevu:

            statut = "SOLDE"

        elif total_verse > 0:

            statut = "PARTIEL"

        else:

            statut = "NON SOLDE"

        connection.execute(
            """
            UPDATE cotisants
            SET
                montant_verse = ?,
                reste = ?,
                statut = ?
            WHERE id = ?
            """,
            (
                total_verse,
                reste,
                statut,
                cotisant_id
            )
        )

    connection.commit()

    connection.close()

    return jsonify({
        "message": (
            "Versement supprimé et "
            "cotisant recalculé."
        ),
        "id": versement_id
    })


# ============================================================
# TACHES - LECTURE
# ============================================================

@app.route(
    "/api/taches",
    methods=["GET"]
)
def get_taches():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            t.id,
            t.categorie_id,
            t.nom,
            t.description,
            t.progression,
            t.statut,
            t.date_prevue,
            t.date_realisation,
            c.nom AS categorie

        FROM taches t

        LEFT JOIN categories c
            ON t.categorie_id = c.id

        ORDER BY t.id
        """
    ).fetchall()

    connection.close()

    return jsonify([
        row_to_dict(row)
        for row in rows
    ])


# ============================================================
# AJOUTER UNE TACHE - ADMIN
# ============================================================

@app.route(
    "/api/taches",
    methods=["POST"]
)
def ajouter_tache():

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    data = request.get_json(
        force=True,
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Données JSON absentes."
        }), 400

    nom = str(
        data.get(
            "nom",
            ""
        )
    ).strip()

    description = str(
        data.get(
            "description",
            ""
        )
    ).strip()

    categorie_id = data.get(
        "categorie_id"
    )

    date_prevue = data.get(
        "date_prevue"
    )

    if not nom:

        return jsonify({
            "error": (
                "Le nom de la tâche "
                "est obligatoire."
            )
        }), 400

    if categorie_id in (
        "",
        None
    ):

        categorie_id = None

    else:

        try:

            categorie_id = int(
                categorie_id
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "error": "Catégorie invalide."
            }), 400

    try:

        progression = float(
            data.get(
                "progression",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error": "Progression invalide."
        }), 400

    progression = max(
        0,
        min(
            progression,
            100
        )
    )

    if progression <= 0:

        statut = "A FAIRE"

    elif progression < 100:

        statut = "EN COURS"

    else:

        statut = "TERMINE"

    if progression >= 100:

        date_realisation = (
            date.today().isoformat()
        )

    else:

        date_realisation = None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO taches (
            categorie_id,
            nom,
            description,
            progression,
            statut,
            date_prevue,
            date_realisation
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            categorie_id,
            nom,
            description,
            progression,
            statut,
            date_prevue,
            date_realisation
        )
    )

    connection.commit()

    tache_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "message": "Tâche créée.",
        "id": tache_id
    }), 201


# ============================================================
# MODIFIER UNE TACHE - ADMIN
# ============================================================

@app.route(
    "/api/taches/<int:tache_id>",
    methods=["PUT"]
)
def modifier_tache(tache_id):

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    data = request.get_json(
        force=True,
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Données JSON absentes."
        }), 400

    connection = get_connection()

    ancienne = connection.execute(
        """
        SELECT *
        FROM taches
        WHERE id = ?
        """,
        (tache_id,)
    ).fetchone()

    if ancienne is None:

        connection.close()

        return jsonify({
            "error": "Tâche introuvable."
        }), 404

    nom = str(
        data.get(
            "nom",
            ancienne["nom"]
        )
    ).strip()

    description = str(
        data.get(
            "description",
            ancienne["description"] or ""
        )
    ).strip()

    categorie_id = data.get(
        "categorie_id",
        ancienne["categorie_id"]
    )

    if categorie_id in (
        "",
        None
    ):

        categorie_id = None

    else:

        try:

            categorie_id = int(
                categorie_id
            )

        except (
            TypeError,
            ValueError
        ):

            connection.close()

            return jsonify({
                "error": "Catégorie invalide."
            }), 400

    try:

        progression = float(
            data.get(
                "progression",
                ancienne["progression"] or 0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        connection.close()

        return jsonify({
            "error": "Progression invalide."
        }), 400

    progression = max(
        0,
        min(
            progression,
            100
        )
    )

    date_prevue = data.get(
        "date_prevue",
        ancienne["date_prevue"]
    )

    if progression <= 0:

        statut = "A FAIRE"
        date_realisation = None

    elif progression < 100:

        statut = "EN COURS"
        date_realisation = None

    else:

        statut = "TERMINE"

        date_realisation = data.get(
            "date_realisation"
        )

        if not date_realisation:

            date_realisation = (
                date.today().isoformat()
            )

    connection.execute(
        """
        UPDATE taches
        SET
            categorie_id = ?,
            nom = ?,
            description = ?,
            progression = ?,
            statut = ?,
            date_prevue = ?,
            date_realisation = ?
        WHERE id = ?
        """,
        (
            categorie_id,
            nom,
            description,
            progression,
            statut,
            date_prevue,
            date_realisation,
            tache_id
        )
    )

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Tâche mise à jour.",
        "id": tache_id,
        "progression": progression,
        "statut": statut
    })


# ============================================================
# SUPPRIMER UNE TACHE - ADMIN
# ============================================================

@app.route(
    "/api/taches/<int:tache_id>",
    methods=["DELETE"]
)
def supprimer_tache(tache_id):

    if not verifier_token_admin():

        return jsonify({
            "error": (
                "Accès administrateur requis."
            )
        }), 403

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM taches
        WHERE id = ?
        """,
        (tache_id,)
    )

    if cursor.rowcount == 0:

        connection.close()

        return jsonify({
            "error": "Tâche introuvable."
        }), 404

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Tâche supprimée."
    })


# ============================================================
# LANCEMENT DE L'API
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "API FLASK - "
        "OBSEQUES MAKOSSO POATHY JEAN PIERRE"
    )

    print("=" * 60)

    print(
        f"\nBase SQLite : "
        f"{DATABASE_PATH}"
    )

    # ========================================================
    # MODIFICATION ETAPE 1
    # ========================================================
    # PORT configurable pour le développement local
    # et pour le déploiement.

    PORT = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    print(
        f"\nServeur : "
        f"http://127.0.0.1:{PORT}"
    )

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )