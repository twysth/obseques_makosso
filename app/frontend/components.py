
import os

import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

# En local :
# http://127.0.0.1:5000
#
# En ligne :
# l'URL sera fournie par la variable d'environnement
# OBSEQUES_API_URL
API_URL = os.getenv(
    "OBSEQUES_API_URL",
    "http://127.0.0.1:5000"
).rstrip("/")


# ============================================================
# INITIALISATION DE LA SESSION
# ============================================================

def initialiser_session_admin():

    if "admin_token" not in st.session_state:

        st.session_state.admin_token = None


# ============================================================
# VERIFICATION DE LA CONNEXION
# ============================================================

def admin_connecte():

    initialiser_session_admin()

    return bool(
        st.session_state.admin_token
    )


# ============================================================
# HEADERS ADMINISTRATEUR
# ============================================================

def get_admin_headers():

    initialiser_session_admin()

    token = st.session_state.admin_token

    if token:

        return {
            "X-Admin-Token": token
        }

    return {}


# ============================================================
# CONNEXION ADMINISTRATEUR
# ============================================================

def connecter_admin(password):

    try:

        response = requests.post(
            f"{API_URL}/api/admin/login",
            json={
                "password": password
            },
            timeout=10
        )

        try:

            resultat = response.json()

        except ValueError:

            resultat = {
                "error": response.text
            }

        if not response.ok:

            return False, resultat

        if not resultat.get(
            "success",
            False
        ):

            return False, resultat

        token = resultat.get(
            "token"
        )

        if not token:

            return False, {
                "error": (
                    "Le serveur n'a pas retourné "
                    "de token administrateur."
                )
            }

        st.session_state.admin_token = token

        return True, resultat

    except requests.exceptions.RequestException as erreur:

        return False, {
            "error": (
                f"Impossible de contacter Flask : "
                f"{erreur}"
            )
        }


# ============================================================
# DECONNEXION ADMINISTRATEUR
# ============================================================

def deconnecter_admin():

    initialiser_session_admin()

    token = st.session_state.admin_token

    if token:

        try:

            requests.post(
                f"{API_URL}/api/admin/logout",
                headers={
                    "X-Admin-Token": token
                },
                timeout=10
            )

        except requests.exceptions.RequestException:

            pass

    st.session_state.admin_token = None


# ============================================================
# INTERFACE ADMINISTRATEUR
# ============================================================

def afficher_espace_admin():

    initialiser_session_admin()

    st.sidebar.divider()

    st.sidebar.subheader(
        "🔐 Administration"
    )

    # --------------------------------------------------------
    # ADMIN CONNECTE
    # --------------------------------------------------------

    if admin_connecte():

        st.sidebar.success(
            "🟢 Administrateur connecté"
        )

        st.sidebar.caption(
            "Les opérations sensibles sont autorisées."
        )

        if st.sidebar.button(
            "🚪 Déconnexion",
            width="stretch",
            key="bouton_deconnexion_global"
        ):

            deconnecter_admin()

            st.rerun()

        return True

    # --------------------------------------------------------
    # ADMIN NON CONNECTE
    # --------------------------------------------------------

    st.sidebar.info(
        "Connexion nécessaire pour effectuer "
        "des opérations d'administration."
    )

    with st.sidebar.form(
        "form_connexion_admin_global"
    ):

        password = st.text_input(
            "Mot de passe administrateur",
            type="password"
        )

        connexion = st.form_submit_button(
            "🔑 Se connecter",
            width="stretch"
        )

    if connexion:

        if not password:

            st.sidebar.error(
                "Veuillez saisir le mot de passe."
            )

        else:

            succes, resultat = connecter_admin(
                password
            )

            if succes:

                st.sidebar.success(
                    "✅ Connexion administrateur réussie."
                )

                st.rerun()

            else:

                st.sidebar.error(
                    resultat.get(
                        "error",
                        "Échec de connexion."
                    )
                )

    return False


# ============================================================
# SIGNATURE
# ============================================================

def afficher_signature():

    st.divider()

    st.markdown(
        """
        <div style="
            text-align: center;
            color: #777777;
            font-size: 0.9rem;
            padding: 12px 0;
        ">

        <strong>
            Aldrin PAMBOU
        </strong>

        <br>

        Data Scientist • Développeur IA • Chimiste analytique

        <br>

        Développeur de cette application de suivi des obsèques
        <br>

        pour un usage strictement familial

        </div>
        """,
        unsafe_allow_html=True
    )

