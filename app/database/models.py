from dataclasses import dataclass
from typing import Optional


# ============================================================
# CATEGORIES BUDGETAIRES
# ============================================================

@dataclass
class Categorie:
    id: Optional[int]
    nom: str
    budget_previsionnel: float
    budget_detaille: float
    budget_non_affecte: float
    statut_detail: str


# ============================================================
# DEPENSES
# ============================================================

@dataclass
class Depense:
    id: Optional[int]
    categorie_id: int
    designation: str

    prix_unitaire_prevu: float
    quantite_prevue: float
    montant_prevu: float

    prix_unitaire_reel: float
    quantite_reelle: float
    montant_reel: float

    ecart: float
    progression: float
    statut: str


# ============================================================
# COTISANTS
# ============================================================

@dataclass
class Cotisant:
    id: Optional[int]
    nom: str
    liste: str
    telephone: str
    montant_prevu: float
    montant_verse: float
    reste: float
    statut: str


# ============================================================
# VERSEMENTS
# ============================================================

@dataclass
class Versement:
    id: Optional[int]
    cotisant_id: int
    date_versement: str
    montant: float
    commentaire: Optional[str] = None


# ============================================================
# TACHES / SUIVI DES PREPARATIFS
# ============================================================

@dataclass
class Tache:
    id: Optional[int]
    categorie_id: Optional[int]
    nom: str
    description: Optional[str]
    progression: float
    statut: str
    date_prevue: Optional[str]
    date_realisation: Optional[str]