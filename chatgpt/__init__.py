from otree.api import *
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# récupère la clé openai
key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=key)


class C(BaseConstants):
    NAME_IN_URL = "chatgpt"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    USER_PREFIX = "Joueur: "  # nom du joueur affiché avant son message dans le chat
    BOT_PREFIX = "GPT: "  # pareil pour gpt
    GPT_BEHAVIOR = os.environ.get("GPT_BEHAVIOR")


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    gpt_history = models.LongStringField(initial="")  # texte concaténé
    gpt_behavior = models.StringField(initial=C.GPT_BEHAVIOR)  # comportement du bot


def chat_with_gpt(player: Player, data):
    # player.gpt_behavior = "One Piece"
    user_message = data["message"]
    # historique sous forme de liste pour la requête
    messages_list = [
        {"role": "system", "content": "Tu réponds en une à deux phrases simples."},
        {"role": "system", "content": f"Tu vas me parler de {player.gpt_behavior}"},
    ]
    history = player.gpt_history or ""

    # reconstruit messages_list
    for line in history.strip().split("\n"):
        if line.startswith(C.USER_PREFIX):  # message de user
            messages_list.append(
                {"role": "user", "content": line[len(C.USER_PREFIX) :]}
            )
        elif line.startswith(C.BOT_PREFIX):  # message de gpt
            messages_list.append(
                {"role": "assistant", "content": line[len(C.BOT_PREFIX) :]}
            )

    messages_list.append({"role": "user", "content": user_message})

    history += f"\n{C.USER_PREFIX}{user_message}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages_list,
        )
        bot_reply = response.choices[0].message.content
    except Exception:
        return {player.id_in_group: {"type": "gpt_error", "message": "Le service IA est temporairement indisponible."}}

    history += f"\n{C.BOT_PREFIX}{bot_reply}"
    player.gpt_history = history

    return {player.id_in_group: {"reply": bot_reply, "gpt_history": history}}


# PAGES
class ChatPage(Page):

    live_method = "chat_with_gpt"

    def vars_for_template(player: Player):
        return {"gpt_history": player.gpt_history}


page_sequence = [ChatPage]
