import subprocess
import sys
import time
import webbrowser
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FLASK_APP = (
    BASE_DIR
    / "app"
    / "backend"
    / "flask_app.py"
)

STREAMLIT_APP = (
    BASE_DIR
    / "app"
    / "frontend"
    / "0_Accueil.py"
)

STREAMLIT_URL = "http://localhost:8501"


# ============================================================
# VERIFICATION DES FICHIERS
# ============================================================

if not FLASK_APP.exists():

    print(
        f"❌ Flask introuvable : {FLASK_APP}"
    )

    raise SystemExit(1)


if not STREAMLIT_APP.exists():

    print(
        f"❌ Streamlit introuvable : {STREAMLIT_APP}"
    )

    raise SystemExit(1)


# ============================================================
# TITRE
# ============================================================

print("=" * 60)

print(
    "OBSÈQUES MAKOSSO POATHY JEAN PIERRE"
)

print(
    "Démarrage de l'application"
)

print("=" * 60)


# ============================================================
# LANCEMENT FLASK
# ============================================================

print(
    "\n🔵 Démarrage de Flask..."
)

flask_process = subprocess.Popen(
    [
        sys.executable,
        str(FLASK_APP)
    ],
    cwd=str(BASE_DIR)
)


# ============================================================
# ATTENTE DE FLASK
# ============================================================

print(
    "⏳ Attente du démarrage de l'API..."
)

time.sleep(3)


# ============================================================
# LANCEMENT STREAMLIT
# ============================================================

print(
    "\n🟢 Démarrage de Streamlit..."
)

streamlit_process = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(STREAMLIT_APP),
        "--server.headless",
        "true"
    ],
    cwd=str(BASE_DIR)
)


# ============================================================
# ATTENTE DE STREAMLIT
# ============================================================

print(
    "⏳ Attente du démarrage de Streamlit..."
)

time.sleep(5)


# ============================================================
# OUVERTURE AUTOMATIQUE DU NAVIGATEUR
# ============================================================

print(
    "\n🌐 Ouverture du navigateur..."
)

webbrowser.open(
    STREAMLIT_URL
)


# ============================================================
# INFORMATIONS
# ============================================================

print("\n" + "=" * 60)

print(
    "APPLICATION DEMARRÉE"
)

print("=" * 60)

print(
    "\n🌐 Interface : "
    f"{STREAMLIT_URL}"
)

print(
    "🔵 API Flask : "
    "http://127.0.0.1:5000"
)

print(
    "\n⚠️ Gardez cette fenêtre ouverte "
    "pendant l'utilisation."
)

print(
    "Appuyez sur CTRL+C pour arrêter."
)

print("=" * 60)


# ============================================================
# SURVEILLANCE
# ============================================================

try:

    while True:

        if flask_process.poll() is not None:

            print(
                "\n❌ Flask s'est arrêté."
            )

            break

        if streamlit_process.poll() is not None:

            print(
                "\n❌ Streamlit s'est arrêté."
            )

            break

        time.sleep(1)


except KeyboardInterrupt:

    print(
        "\n\n🛑 Arrêt de l'application..."
    )


finally:

    # ========================================================
    # ARRET STREAMLIT
    # ========================================================

    if streamlit_process.poll() is None:

        streamlit_process.terminate()

        try:

            streamlit_process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:

            streamlit_process.kill()


    # ========================================================
    # ARRET FLASK
    # ========================================================

    if flask_process.poll() is None:

        flask_process.terminate()

        try:

            flask_process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:

            flask_process.kill()


    print(
        "\n✅ Application arrêtée."
    )