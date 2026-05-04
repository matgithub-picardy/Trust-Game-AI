"""
Module pour le Trust Game (Jeu de Confiance) avec intégration d'un assistant IA (GPT).
Ce module gère la logique du jeu, la communication entre les joueurs et l'interaction avec l'API OpenAI.
"""
from otree.api import *
from openai import OpenAI
import random
import time
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement (clé API OpenAI)
load_dotenv()

# Initialisation du client OpenAI
key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=key)


class C(BaseConstants):
    """Constantes globales pour l'application Trust Game."""
    NAME_IN_URL = "tg"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1
    
    # Paramètres économiques
    ENDOWMENT = 10  # Dotation initiale du Joueur A
    MULTIPLIER = 3   # Facteur multiplicateur pour le transfert de A vers B
    
    # Paramètres du chat
    CHAT_DURATION = 300  # Durée de la session de communication en secondes
    USER_PREFIX = "<strong>Joueur:</strong> "  # Préfixe pour les messages du participant
    BOT_PREFIX = "<strong>GPT:</strong> "      # Préfixe pour les messages de l'アシスタント IA
    CHAT_SEPARATOR = "<br>"                    # Séparateur HTML pour l'historique
    
    # Gestion des comportements IA
    NO_GPT_BEHAVIOR = "Non"
    BEHAVIORS = ["Non", "Neutre", "Stratège", "Altruiste"] # Liste des tempéraments GPT
    
    # Validation du quiz
    MAX_QUIZ_ERRORS = 3  # Seuil d'erreurs avant masquage des explications détaillées
    
    # Configuration via variables d'environnement
    HAS_CHEAP_TALK = os.environ.get("HAS_CHEAP_TALK") == "True"
    GPT_BEHAVIOR = os.environ.get("GPT_BEHAVIOR")


class Subsession(BaseSubsession):
    """Gère la création de la session et l'attribution des options de chat au démarrage."""
    def creating_session(self):
        """Initialisation des paramètres spécifiques pour chaque joueur au début de la session."""
        for player in self.get_players():
            set_chat_options(player)


class Group(BaseGroup):
    """Représente un groupe de deux joueurs (A et B) et gère les données partagées."""
    amount_sent = models.CurrencyField(
        min=0, max=C.ENDOWMENT,
        doc="Montant envoyé par le Joueur A au Joueur B."
    )
    amount_sent_back = models.CurrencyField(
        doc="Montant renvoyé par le Joueur B au Joueur A."
    )
    talk_time = models.IntegerField(doc="Durée effective de la communication en secondes.")
    expire_time = models.FloatField(doc="Timestamp d'expiration de la session de chat.")

    def set_payoffs(self):
        """Calcule les gains finaux pour les deux membres du groupe à la fin du jeu."""
        sent = self.amount_sent
        sent_back = self.amount_sent_back
        tripled = sent * C.MULTIPLIER

        p1: Player = self.get_player_by_id(1)
        p2: Player = self.get_player_by_id(2)

        p1.payoff = C.ENDOWMENT - sent + sent_back
        p2.payoff = tripled - sent_back


class Player(BasePlayer):
    """Contient les données individuelles d'un participant et ses réponses au questionnaire/quiz."""
    tg_role = models.StringField(doc="Rôle dans le jeu (A ou B).")
    partner_id = models.StringField(doc="Identifiant interne du partenaire de jeu.")
    error_count = models.IntegerField(initial=0, doc="Nombre d'erreurs commises lors du quiz de compréhension.")
    
    # Champs du quiz de compréhension
    q1_b_receive = models.IntegerField(label="")
    q2_a_get_back = models.IntegerField(label="")
    q3_a_final = models.IntegerField(label="")
    q3_b_final = models.IntegerField(label="")
    q4_true_false = models.StringField(
        label="", choices=["Vrai", "Faux"], widget=widgets.RadioSelect
    )
    
    # Variables dynamiques pour les questions du quiz
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    
    # Historique et état de la communication
    message = models.LongStringField(blank=True)
    chat_history = models.LongStringField(initial="", doc="Historique HTML de la discussion entre joueurs.")
    gpt_history = models.LongStringField(initial="", doc="Historique HTML de la discussion avec l'IA.")

    gpt_behavior = models.StringField(initial=C.GPT_BEHAVIOR, doc="Comportement assigné à l'assistant GPT.")
    has_cheap_talk = models.BooleanField(initial=C.HAS_CHEAP_TALK, doc="Indique si le chat entre joueurs est activé.")
    participant_left = models.BooleanField(initial=False, doc="Indique si le partenaire a quitté la session prématurément.")


def set_participant_vars(player: Player):
    """
    Archive les données du jeu dans participant.vars pour une utilisation inter-applications.
    Cette fonction est appelée à la fin du module pour alimenter la page de résultats globaux.
    """
    player.tg_role = "A" if player.id_in_group == 1 else "B"
    player.participant.vars["tg_role"] = player.tg_role
    player.participant.vars["tg_endowment"] = C.ENDOWMENT

    group: Group = player.group
    sent = int(group.field_maybe_none("amount_sent") or 0)
    tripled = sent * C.MULTIPLIER
    sent_back = int(group.field_maybe_none("amount_sent_back") or 0)
    player.participant.vars["tg_sent"] = sent
    player.participant.vars["tg_multiplier"] = C.MULTIPLIER
    player.participant.vars["tg_sent_back"] = sent_back


def set_partner_id(player: Player):
    """Identifie et stocke l'ID ou le code du partenaire de jeu."""
    partner = player.get_others_in_group()[0]
    uid = partner.participant.code
    id = str(partner.participant.id_in_session)
    player.partner_id = uid if uid else id


def set_chat_options(player: Player):
    """
    Attribue dynamiquement un comportement GPT et active/désactive le chat direct (cheap talk).
    
    Logique de rotation et répartition :
      - Rotation par paires : chaque paire de participants consécutifs reçoit le même comportement GPT.
      - Équilibre des traitements : la moitié des participants a accès au cheap talk.
    """
    behaviors = C.BEHAVIORS
    nb_behaviors = len(behaviors)
    nb_participants = len(player.session.get_participants())
    participant_id = player.participant.id_in_session
    index = ((participant_id - 1) // 2) % nb_behaviors
    player.gpt_behavior = behaviors[index]
    player.has_cheap_talk = participant_id > nb_participants // 2


class BaseQuiz(Page):
    """Classe de base pour les pages de quiz, gérant les champs du formulaire et les variables dynamiques."""
    form_model = "player"
    form_fields = [
        "q1_b_receive",
        "q2_a_get_back",
        "q3_a_final",
        "q3_b_final",
        "q4_true_false",
    ]

    @staticmethod
    def vars_for_template(player: Player):
        """Génère des valeurs aléatoires pour personnaliser les questions du quiz pour chaque joueur."""
        player.x = random.randint(2, 10)

        mult = C.MULTIPLIER
        max_choice = mult * C.ENDOWMENT
        choice_list = [x for x in range(mult, max_choice + 1) if x % mult == 0]
        player.y = random.choice(choice_list)

        player.z = random.randint(1, player.y)
        return {
            "participant": player.participant,
            "x": player.x,
            "y": player.y,
            "z": player.z,
        }

    @staticmethod
    def error_message(player: Player, values):
        """Valide les réponses et renvoie des messages d'erreur explicatifs ou génériques selon le nombre d'échecs."""
        errors = {}
        correct_q1 = player.x * C.MULTIPLIER

        if values["q1_b_receive"] != correct_q1:
            player.error_count += 1
            if player.error_count < C.MAX_QUIZ_ERRORS:
                errors["q1_b_receive"] = (
                    f"Le joueur B reçoit {player.x} × {C.MULTIPLIER} = {correct_q1} jetons."
                )
            else:
                errors["q1_b_receive"] = "Réponse incorrecte. Relisez les instructions."

        if values["q2_a_get_back"] != player.z:
            player.error_count += 1
            if player.error_count < C.MAX_QUIZ_ERRORS:
                errors["q2_a_get_back"] = (
                    f"Le joueur A reçoit ce que B renvoie : {player.z} jetons."
                )
            else:
                errors["q2_a_get_back"] = "Réponse incorrecte. Relisez les instructions."

        if values["q3_a_final"] != 8:
            player.error_count += 1
            if player.error_count < C.MAX_QUIZ_ERRORS:
                errors["q3_a_final"] = "Revoir le calcul : 10 - 4 + 2 = 8 jetons."
            else:
                errors["q3_a_final"] = "Réponse incorrecte. Relisez les instructions."

        if values["q3_b_final"] != 10:
            player.error_count += 1
            if player.error_count < C.MAX_QUIZ_ERRORS:
                errors["q3_b_final"] = "Revoir le calcul : 12 - 2 = 10 jetons."
            else:
                errors["q3_b_final"] = "Réponse incorrecte. Relisez les instructions."

        if values["q4_true_false"] != "Faux":
            player.error_count += 1
            if player.error_count < C.MAX_QUIZ_ERRORS:
                errors["q4_true_false"] = (
                    "C'est faux : les jetons renvoyés par B ne sont pas triplés."
                )
            else:
                errors["q4_true_false"] = "Réponse incorrecte. Relisez les instructions."

        return errors or None


class QuizExample1(BaseQuiz):
    pass


class Instructions(Page):

    def vars_for_template(player: Player):
        return {
            "gpt behavior": player.gpt_behavior,
            "has cheap talk": player.has_cheap_talk,
        }

    def before_next_page(player: Player, timeout_happened):
        set_partner_id(player)


def handle_chat_message(player: Player, data: dict):
    """
    Traite les messages de chat envoyés entre les deux joueurs humains.
    Met à jour l'historique et prépare les réponses pour l'interface client.
    """
    if "message" in data:
        letter = "A" if player.id_in_group == 1 else "B"
        message_html = f"<strong>Joueur {letter}:</strong> {data['message']}<br>"
        responses = {}

        for p in player.group.get_players():
            p.chat_history += message_html
            responses[p.id_in_group] = {
                "new_message": message_html,
                "sender_id": player.id_in_group,
            }
        return responses

    # accusé de lecture : le joueur signale qu'il a vu les messages
    if "read_receipt" in data:
        partner = player.get_others_in_group()[0]
        return {partner.id_in_group: {"read_by": player.id_in_group}}

    return None


def chat_with_gpt(player: Player, data: dict):
    """
    Gère l'interaction avec l'API OpenAI (GPT-3.5) pour simuler un assistant conseil.
    Conserve le contexte de la discussion et respecte le tempérament assigné au joueur.
    """
    user_message = data["message"]
    
    # Définition du contexte système (instructions et tempérament)
    messages_list = [
        {"role": "system", "content": "Tu réponds en une à deux phrases simples."},
        {
            "role": "system",
            "content": f"Je joue au trust game. Donne moi des conseils pour favoriser un comportement {player.gpt_behavior}",
        },
    ]
    history = player.gpt_history or ""

    # Reconstruction de la liste des messages à partir de l'historique stocké
    for line in history.strip().split(C.CHAT_SEPARATOR):
        if line.startswith(C.USER_PREFIX):
            messages_list.append(
                {"role": "user", "content": line[len(C.USER_PREFIX) :]}
            )
        elif line.startswith(C.BOT_PREFIX):
            messages_list.append(
                {"role": "assistant", "content": line[len(C.BOT_PREFIX) :]}
            )

    messages_list.append({"role": "user", "content": user_message})
    history += f"{C.USER_PREFIX}{user_message}<br>"

    try:
        # Appel asynchrone (non-bloquant via timeout court) à l'API OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages_list,
            timeout=3.0,
        )
        bot_reply = response.choices[0].message.content
    except Exception:
        return {player.id_in_group: {"type": "gpt_error", "message": "Le service IA est temporairement indisponible."}}

    history += f"{C.BOT_PREFIX}{bot_reply}<br>"
    player.gpt_history = history

    return {
        player.id_in_group: {
            "is_chat_gpt": True,
            "reply": bot_reply,
            "gpt_history": history,
            "bot_prefix": C.BOT_PREFIX,
        }
    }


def handle_typing_status(player: Player, data: dict) -> dict:
    """Envoie l'état de frappe (typing status) au partenaire de jeu."""
    is_typing = data["typing_status"]
    responses = {}
    for p in player.group.get_players():
        if p.id_in_group != player.id_in_group:
            responses[p.id_in_group] = {
                "other_player_typing": is_typing,
                "player_id": player.id_in_group,
            }
    return responses


def handle_amount_sent(player: Player, data: dict) -> dict:
    """Transfère les jetons du Joueur A au Joueur B et déclenche la notification temps réel."""
    amount = int(data["amount_sent"])
    group: Group = player.group
    if 0 <= amount <= C.ENDOWMENT:
        group.amount_sent = amount
        group.talk_time = int(C.CHAT_DURATION - (group.expire_time - time.time()))
        
        responses = {}
        for p in group.get_players():
            if p.id_in_group == 1:  # Confirmation Joueur A
                responses[p.id_in_group] = {
                    "status": "sent",
                    "amount_sent": amount,
                }
            else:  # Notification Joueur B avec montant multiplié
                responses[p.id_in_group] = {
                    "status": "received",
                    "amount_sent": amount,
                    "tripled_amount": int(amount * C.MULTIPLIER),
                }
        return responses


def handle_amount_sent_back(player: Player, data: dict) -> dict:
    """Consigne le renvoi de jetons par le Joueur B et clôture la transaction."""
    group: Group = player.group
    amount_back = int(data["amount_sent_back"])
    tripled_amount = int(group.amount_sent * C.MULTIPLIER)

    if 0 <= amount_back <= tripled_amount:
        group.amount_sent_back = amount_back
        
        responses = {}
        for p in group.get_players():
            responses[p.id_in_group] = {
                "status": "complete",
                "can_proceed": True,
                "amount_sent": group.amount_sent,
                "amount_sent_back": amount_back,
                "tripled_amount": tripled_amount,
            }
        group.set_payoffs()  # Mise à jour des payoffs définitifs
        return responses


class SyncWaitPage(WaitPage):

    def after_all_players_arrive(group: Group):
        if (
            group.field_maybe_none("expire_time") is None
        ):  # set le compte à rebours du chat
            group.expire_time = time.time() + C.CHAT_DURATION

    def vars_for_template(player: Player):
        other_player = player.get_others_in_group()[0]
        other_participant_number = other_player.participant.id_in_session
        return {
            "other_player": other_player,
            "other_participant_number": other_participant_number,
        }


class GamePlay(Page):

    def vars_for_template(player: Player):
        return {
            "has_chat_gpt": player.gpt_behavior != C.NO_GPT_BEHAVIOR,
            "gpt_behavior": player.gpt_behavior,
            "gpt_history": player.gpt_history,
            "chat_history": player.chat_history,
        }

    @staticmethod
    def live_method(player: Player, data):
        if "is_chat_gpt" in data:
            return chat_with_gpt(player, data)

        # cheap talk + accusé de lecture
        if "message" in data or "read_receipt" in data:
            return handle_chat_message(player, data)

        # indicateur de frappe
        if "typing_status" in data:
            return handle_typing_status(player, data)

        # envoi de jetons par le joueur A
        if "amount_sent" in data and player.id_in_group == 1:
            return handle_amount_sent(player, data)

        # renvoi de jetons par le joueur B
        if "amount_sent_back" in data and player.id_in_group == 2:
            return handle_amount_sent_back(player, data)

        # heartbeat : le client envoie {"ping": true} toutes les 30s
        if "ping" in data:
            responses = {}
            for p in player.group.get_players():
                if p.id_in_group != player.id_in_group:
                    responses[p.id_in_group] = {"partner_alive": True}
            return responses

        # le client signale qu'il quitte (beforeunload)
        if "leaving" in data:
            responses = {}
            for p in player.group.get_players():
                if p.id_in_group != player.id_in_group:
                    p.participant_left = True
                    responses[p.id_in_group] = {"partner_left": True}
            return responses

        return None

    @staticmethod
    def js_vars(player: Player):
        group: Group = player.group
        return {
            "id_in_group": player.id_in_group,
            "endowment": C.ENDOWMENT,
            "multiplier": C.MULTIPLIER,
            "amount_sent": group.field_maybe_none("amount_sent"),
            "amount_sent_back": group.field_maybe_none("amount_sent_back"),
        }


    def before_next_page(player: Player, timeout_happened):
        """
        Si le timer expire sans que les jetons aient été échangés,
        on fixe des valeurs par défaut pour ne pas bloquer le partenaire.
        - Joueur A : amount_sent = 0
        - Joueur B : amount_sent_back = 0
        Les gains sont ensuite calculés (payoff nul pour le joueur fautif).
        """
        if timeout_happened:
            group: Group = player.group
            if player.id_in_group == 1 and group.field_maybe_none("amount_sent") is None:
                group.amount_sent = 0
                group.amount_sent_back = 0
                group.talk_time = C.CHAT_DURATION
                group.set_payoffs()
            elif player.id_in_group == 2 and group.field_maybe_none("amount_sent_back") is None:
                group.amount_sent_back = 0
                group.set_payoffs()


class Results(Page):
    """Page finale affichant le bilan de la transaction de confiance pour chaque joueur."""
    @staticmethod
    def vars_for_template(player: Player):
        """Récupère les montants réels du groupe pour l'affichage final (avec sécurité anti-null)."""
        group: Group = player.group
        sent = int(group.field_maybe_none("amount_sent") or 0)
        sent_back = int(group.field_maybe_none("amount_sent_back") or 0)
        tripled = sent * C.MULTIPLIER
        return dict(
            sent=sent,
            sent_back=sent_back,
            tripled=tripled,
            payoff=int(player.payoff),
            is_test_round=(player.round_number == 1),
        )

    def before_next_page(player: Player, timeout_happened):
        """Sauvegarde les résultats du TG dans les variables globales du participant."""
        set_participant_vars(player)


page_sequence = [
    Instructions,
    QuizExample1,
    SyncWaitPage,
    GamePlay,
    Results,
]
