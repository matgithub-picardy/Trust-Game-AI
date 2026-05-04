from os import environ
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement (.env)
load_dotenv()

# Nombre de joueurs par groupe pour le Trust Game
PLAYERS_PER_GROUP = 2

SESSION_CONFIGS = [
    dict(
        name="risk_aversion",
        display_name="Mesure d'aversion au risque",
        num_demo_participants=1,
        app_sequence=["risk_aversion"],
    ),
    dict(
        name="trust_game",
        display_name="Trust Game (Jeu de Confiance)",
        num_demo_participants=PLAYERS_PER_GROUP,
        app_sequence=["trust_game"],
    ),
    dict(
        name="dispatcher",
        display_name="Dispatcher (Aiguillage)",
        num_demo_participants=3 * PLAYERS_PER_GROUP,
        app_sequence=["dispatcher"],
    ),
    # Configurations par groupes de traitement
    dict(
        name="groupe_1",
        display_name="Groupe 1 (Q/A/TG)",
        num_demo_participants=PLAYERS_PER_GROUP,
        app_sequence=["questionnaire", "risk_aversion", "trust_game", "results"],
    ),
    dict(
        name="groupe_2",
        display_name="Groupe 2 (A/Q/TG)",
        num_demo_participants=PLAYERS_PER_GROUP,
        app_sequence=["risk_aversion", "questionnaire", "trust_game", "results"],
    ),
    dict(
        name="groupe_3",
        display_name="Groupe 3 (Q/TG/A)",
        num_demo_participants=PLAYERS_PER_GROUP,
        app_sequence=["questionnaire", "trust_game", "risk_aversion", "results"],
    ),
    # Tests unitaires et debugging
    dict(
        name="test_results",
        display_name="Test Results (Synthèse)",
        num_demo_participants=1,
        app_sequence=["risk_aversion", "results"],
    ),
    dict(
        name="test_questionnaire",
        display_name="Test Questionnaire",
        num_demo_participants=1,
        app_sequence=["questionnaire"],
    ),
    dict(
        name="test_chatgpt",
        display_name="Test ChatGPT (Chat IA)",
        num_demo_participants=1,
        app_sequence=["chatgpt"],
    ),
]

# Paramètres par défaut des sessions
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.50,
    participation_fee=10.00,
    doc="Configuration par défaut pour les sessions de Trust Game AI."
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# Paramètres de langue et monnaie
LANGUAGE_CODE = "fr"
USE_POINTS = False
REAL_WORLD_CURRENCY_CODE = "jetons"

# Définition des salles (Rooms)
ROOMS = [
    dict(
        name="econ101",
        display_name="Salle Économie 101",
        participant_label_file="_rooms/econ101.txt",
    ),
    dict(name="live_demo", display_name="Salle de démonstration (sans étiquettes)"),
]

# Sécurité et Administration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = environ.get("OTREE_ADMIN_PASSWORD")
AUTH_LEVEL = os.getenv("OTREE_AUTH_LEVEL", "STUDY")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fallback-dev-key-change-in-production")

# Paramètres de débogage et environnement
DEBUG = os.getenv("DEBUG", "False") == "True"
DEMO_PAGE_INTRO_HTML = "<h3>Trust Game AI - Plateforme d'expérimentation</h3>"

# Applications installées
INSTALLED_APPS = ["otree", "dispatcher", "otree.chat"]

# Rémunération globale
SHOW_UP_FEE = 5        # Participation fixe
CONVERSION_RATE = 0.5  # Taux de conversion : 1 jeton = 0.50 euro
