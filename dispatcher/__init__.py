"""
Application oTree de dispatching (aiguillage).
Cette application répartit les participants dans différentes sous-sessions oTree 
en fonction de leur ID de session, permettant ainsi de gérer des groupes avec 
des configurations de traitements distinctes.
"""
from otree.api import *
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement pour les URLs de redirection
load_dotenv()


class C(BaseConstants):
    """Paramètres globaux pour l'aiguillage des participants."""
    NAME_IN_URL = "dispatcher"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    NUM_APPS = 3
    
    # URLs de destination configurables selon l'environnement
    LOCAL_URL = os.environ.get("LOCAL_URL", "http://localhost:8000")
    HEROKU_URL = os.environ.get("HEROKU_URL", "https://trust-game-ai-f55aa68b15d2.herokuapp.com")
    
    # Identifiants d'administration par défaut (si nécessaire pour scripts externes)
    USERNAME = "admin"
    PASSWORD = "admin"


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    """Stocke le numéro de groupe assigné pour l'aiguillage."""
    group_number = models.IntegerField(doc="Numéro du groupe (1, 2 ou 3) déterminant la configuration d'arrivée.")


def set_vars(player: Player):
    """
    Assigne un numéro de groupe à chaque joueur par rotation de paires.
    Paires d'IDs 1-2 -> Groupe 1, 3-4 -> Groupe 2, 5-6 -> Groupe 3, 7-8 -> Groupe 1...
    """
    n = ((player.participant.id_in_session - 1) // 2) % 3 + 1
    player.group_number = n


def get_code(player: Player):
    """
    Récupère le code de la session oTree active correspondante au groupe assigné.
    Recherche la session la plus récente portant le nom de configuration 'groupe_n'.
    """
    from otree.models import Session
    n = player.group_number
    config_name = f"groupe_{n}"
    
    # Recherche de la session la plus récente avec cette configuration
    # En oTree 5+, on utilise objects_filter() au lieu de objects.filter() de Django
    sessions = Session.objects_filter()
    matching = [s for s in sessions if s.config and s.config.get('name') == config_name]
    
    if matching:
        session = max(matching, key=lambda s: s.id)
        return session.code
    return "NOT_FOUND"


class Welcome(Page):
    """Page d'accueil de l'expérience, effectuant l'attribution du groupe en arrière-plan."""
    def vars_for_template(player: Player):
        pass

    def before_next_page(player: Player, timeout_happened):
        """Initialisation de l'assignation du groupe avant de passer au Dispatch."""
        set_vars(player)


class Dispatch(Page):
    """Page de transition générant le lien vers la session oTree spécifique au groupe."""
    @staticmethod
    def vars_for_template(player: Player):
        """Prépare l'URL de redirection en fonction de l'environnement (Local vs Production)."""
        code = get_code(player)
        if os.getenv("IS_HEROKU", "False") == "True":
            base_url = C.HEROKU_URL
        else:
            base_url = C.LOCAL_URL

        return {
            "player_vars": player.participant.vars,
            "group_number": player.group_number,
            "code": code,
            "link": f'href="{base_url}/join/{code}"',
        }


page_sequence = [Welcome, Dispatch]
