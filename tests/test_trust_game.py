import pytest
from unittest.mock import MagicMock
from trust_game import (
    set_chat_options,
    handle_chat_message,
    handle_typing_status,
    handle_amount_sent,
    handle_amount_sent_back,
)


def mock_player(id_in_group: int):
    """Génère un objet Player simulé (mock) avec un ID spécifique dans le groupe."""
    player = MagicMock()
    player.id_in_group = id_in_group
    player.chat_history = ""
    return player


def mock_player_set_chat_options(id_in_session: int, nb_participants: int):
    """Génère un objet Player simulé pour tester la configuration du chat."""
    player = MagicMock()
    player.participant.id_in_session = id_in_session
    player.session.get_participants.return_value = [
        x for x in range(0, nb_participants)
    ]
    return player


def mock_group() -> list:
    """Simule un groupe de deux joueurs (A et B) liés l'un à l'autre."""
    player_A = mock_player(1)
    player_B = mock_player(2)

    group = MagicMock()
    group.get_players.return_value = [player_A, player_B]

    player_A.group = group
    player_B.group = group

    return group.get_players()


@pytest.mark.parametrize(
    "i, expected_behavior, expected_cheap_talk",
    [
        (1, "Non", False),
        (2, "Non", False),
        (3, "Neutre", False),
        (4, "Neutre", False),
        (5, "Stratège", False),
        (6, "Stratège", False),
        (7, "Altruiste", False),
        (8, "Altruiste", False),
        (9, "Non", True),
        (10, "Non", True),
        (11, "Neutre", True),
        (12, "Neutre", True),
        (13, "Stratège", True),
        (14, "Stratège", True),
        (15, "Altruiste", True),
        (16, "Altruiste", True),
    ],
)
def test_set_chat_options(i, expected_behavior, expected_cheap_talk):
    """Vérifie que le comportement GPT et le mode cheap talk sont correctement attribués par rotation."""
    player = mock_player_set_chat_options(i, 16)
    set_chat_options(player)
    assert player.participant.id_in_session == i
    assert player.gpt_behavior == expected_behavior
    assert player.has_cheap_talk == expected_cheap_talk


def test_handle_chat_message():
    """Teste l'envoi de messages entre joueurs et la mise à jour de l'historique partagé."""
    players = mock_group()
    player_A = players[0]
    player_B = players[1]

    data_1 = {"message": "Ceci est un message"}
    expected_message_1 = "<strong>Joueur A:</strong> Ceci est un message<br>"
    expected_result_1 = {
        1: {"new_message": expected_message_1, "sender_id": 1},
        2: {"new_message": expected_message_1, "sender_id": 1},
    }

    result = handle_chat_message(player_A, data_1)

    assert player_A.chat_history == expected_message_1
    assert player_B.chat_history == expected_message_1
    assert result == expected_result_1

    data_2 = {"message": "Voici un autre"}
    expected_message_2 = "<strong>Joueur B:</strong> Voici un autre<br>"
    expected_result_2 = {
        1: {"new_message": expected_message_2},
        2: {"new_message": expected_message_2},
    }

    result = handle_chat_message(player_B, data_2)

    assert result == expected_result_2
    assert player_A.chat_history == expected_message_1 + expected_message_2
    assert player_B.chat_history == expected_message_1 + expected_message_2


def test_handle_chat_message_but_no_msg():
    """Vérifie que le système ignore les données ne contenant pas de message valide."""
    players = mock_group()
    player_A = players[0]
    data = {"toto": "titi"}

    result = handle_chat_message(player_A, data)
    assert result == None


def test_handle_typing_status():
    """Teste la transmission de l'état 'en cours de saisie' au partenaire."""
    players = mock_group()
    player_A = players[0]
    player_B = players[1]

    # player_A est en train d'écrire
    result = handle_typing_status(player_A, {"typing_status": True})
    assert result == {2: {"other_player_typing": True, "player_id": 1}}

    # player_B arrête d'écrire
    result = handle_typing_status(player_B, {"typing_status": False})
    assert result == {1: {"other_player_typing": False, "player_id": 2}}


def test_handle_amount_sent():
    """Teste le transfert de jetons par le Joueur A."""
    players = mock_group()
    player_A = players[0]

    data = {"amount_sent": "7"}
    result = handle_amount_sent(player_A, data)
    expected_result = {
        1: {
            "status": "sent",
            "amount_sent": 7,
        },
        2: {
            "status": "received",
            "amount_sent": 7,
            "tripled_amount": 21,
        },
    }
    assert result == expected_result


def test_handle_amount_sent_invalid_amounts():
    """Vérifie le rejet des montants d'envoi invalides."""
    players = mock_group()
    player_A = players[0]

    data = {"amount_sent": -1}
    result = handle_amount_sent(player_A, data)
    assert result == None

    data = {"amount_sent": "1111"}
    result = handle_amount_sent(player_A, data)
    assert result == None


def test_handle_amount_sent_back():
    """Teste le renvoi de jetons par le Joueur B."""
    players = mock_group()
    player_B = players[1]
    player_B.group.amount_sent = 9

    data = {"amount_sent_back": "5"}
    result = handle_amount_sent_back(player_B, data)
    expected_result = {
        1: {
            "status": "complete",
            "can_proceed": True,
            "amount_sent": 9,
            "amount_sent_back": 5,
            "tripled_amount": 27,
        },
        2: {
            "status": "complete",
            "can_proceed": True,
            "amount_sent": 9,
            "amount_sent_back": 5,
            "tripled_amount": 27,
        },
    }
    assert player_B.group.amount_sent_back == 5
    assert result == expected_result


def test_handle_amount_sent_back_invalid_amounts():
    """Vérifie le rejet des montants de renvoi invalides."""
    players = mock_group()
    player_B = players[1]

    data = {"amount_sent_back": -1}
    result = handle_amount_sent_back(player_B, data)
    assert result == None

    data = {"amount_sent_back": "1111"}
    result = handle_amount_sent_back(player_B, data)
    assert result == None
