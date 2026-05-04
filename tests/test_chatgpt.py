import pytest
from unittest.mock import MagicMock, patch


def mock_player():
    """Génère un objet Player simulé pour le module chatgpt."""
    player = MagicMock()
    player.id_in_group = 1
    player.gpt_history = ""
    player.gpt_behavior = "One Piece"
    return player


def mock_openai_response(content="Bonjour !"):
    """Génère une réponse simulée de l'API OpenAI."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


@patch("chatgpt.client")
def test_chat_with_gpt_basic(mock_client):
    """Teste un échange simple : envoi d'un message et réception d'une réponse GPT."""
    from chatgpt import chat_with_gpt, C

    mock_client.chat.completions.create.return_value = mock_openai_response("Salut !")
    player = mock_player()

    result = chat_with_gpt(player, {"message": "Bonjour"})

    assert result is not None
    assert 1 in result
    assert result[1]["reply"] == "Salut !"
    assert C.USER_PREFIX + "Bonjour" in player.gpt_history
    assert C.BOT_PREFIX + "Salut !" in player.gpt_history


@patch("chatgpt.client")
def test_chat_with_gpt_history_accumulates(mock_client):
    """Vérifie que l'historique s'accumule correctement après plusieurs messages."""
    from chatgpt import chat_with_gpt, C

    mock_client.chat.completions.create.side_effect = [
        mock_openai_response("Réponse 1"),
        mock_openai_response("Réponse 2"),
    ]
    player = mock_player()

    chat_with_gpt(player, {"message": "Premier message"})
    chat_with_gpt(player, {"message": "Deuxième message"})

    history = player.gpt_history
    assert C.USER_PREFIX + "Premier message" in history
    assert C.BOT_PREFIX + "Réponse 1" in history
    assert C.USER_PREFIX + "Deuxième message" in history
    assert C.BOT_PREFIX + "Réponse 2" in history


@patch("chatgpt.client")
def test_chat_with_gpt_sends_correct_messages_to_api(mock_client):
    """Vérifie que les messages envoyés à l'API OpenAI sont correctement formatés."""
    from chatgpt import chat_with_gpt

    mock_client.chat.completions.create.return_value = mock_openai_response("Ok")
    player = mock_player()

    chat_with_gpt(player, {"message": "Test"})

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]

    # Vérifie les messages système
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert player.gpt_behavior in messages[1]["content"]

    # Vérifie le message utilisateur
    assert messages[-1] == {"role": "user", "content": "Test"}


@patch("chatgpt.client")
def test_chat_with_gpt_rebuilds_history_for_api(mock_client):
    """Vérifie que l'historique existant est correctement reconstruit pour l'API."""
    from chatgpt import chat_with_gpt, C

    mock_client.chat.completions.create.return_value = mock_openai_response("Réponse")
    player = mock_player()
    player.gpt_history = f"{C.USER_PREFIX}Ancien msg\n{C.BOT_PREFIX}Ancienne réponse"

    chat_with_gpt(player, {"message": "Nouveau"})

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]

    # 2 system + 1 ancien user + 1 ancien assistant + 1 nouveau user = 5
    assert len(messages) == 5
    assert messages[2] == {"role": "user", "content": "Ancien msg"}
    assert messages[3] == {"role": "assistant", "content": "Ancienne réponse"}
    assert messages[4] == {"role": "user", "content": "Nouveau"}


@patch("chatgpt.client")
def test_chat_with_gpt_api_error(mock_client):
    """Teste la gestion d'erreur lorsque l'API OpenAI échoue."""
    from chatgpt import chat_with_gpt

    mock_client.chat.completions.create.side_effect = Exception("API down")
    player = mock_player()

    result = chat_with_gpt(player, {"message": "Bonjour"})

    assert result is not None
    assert 1 in result
    assert result[1]["type"] == "gpt_error"
    assert "indisponible" in result[1]["message"]


@patch("chatgpt.client")
def test_chat_with_gpt_empty_history(mock_client):
    """Teste le comportement avec un historique vide (premier message)."""
    from chatgpt import chat_with_gpt

    mock_client.chat.completions.create.return_value = mock_openai_response("Hello")
    player = mock_player()
    player.gpt_history = ""

    result = chat_with_gpt(player, {"message": "Salut"})

    assert result[1]["reply"] == "Hello"

    # Vérifie que seuls les messages système + le message user sont envoyés
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    user_messages = [m for m in messages if m["role"] == "user"]
    assert len(user_messages) == 1
