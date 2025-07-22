import pytest
from unittest.mock import MagicMock
from risk_aversion import (
    C,
    Player,
    display_logic,
    get_ball_color,
    get_final_decision,
    profit_1_2,
    profit_3_4,
    profit_5_8,
    get_absolute_profit,
)


# liste de 8 entiers
def set_real_index(player: Player, lst: list):
    for x, i in zip(lst, range(1, 9)):
        setattr(player, f"real_index_{i}", x)


def set_inv(player: Player, list_1_4: list, list_5_8=None):
    for x, i in zip(list_1_4, range(1, 5)):
        setattr(player, f"inv{i}", x)
    if list_5_8 is not None:
        for x, i in zip(list_5_8, range(5, 9)):
            setattr(player, f"inv{i}", x)


def test_get_real_index():
    player = Player()
    player.current_decision = 4
    lst = [4, 3, 2, 1, 8, 7, 6, 5]
    set_real_index(player, lst)

    result = player.get_real_index()
    assert result == 1

    for i in range(1, 9):
        result = player.get_real_index(i)
        assert result == lst[i - 1]


def test_get_all_real_index():
    player = Player()
    lst = [0, 2, 4, 6, 8, 10, 12, 14]
    set_real_index(player, lst)
    result = player.get_all_real_index()
    assert result == lst


def test_condition_met():
    player = Player()
    set_inv(player, [1, 3, 5, 7])

    for i in range(5, 9):
        result = player.condition_met(i)
        assert result == False

    set_inv(player, [10, 10, 0, 0])
    for i in range(5, 9):
        result = player.condition_met(i)
        assert result == True


def test_get_visible_index():
    player = Player()
    lst = [3, 4, 1, 2, 8, 5, 7, 6]
    set_real_index(player, lst)

    result = player.get_visible_index(1)
    assert result == 3
    result = player.get_visible_index(2)
    assert result == 4
    result = player.get_visible_index(3)
    assert result == 1
    result = player.get_visible_index(4)
    assert result == 2

    # aucune decision 5-8 ne s'affiche
    set_inv(player, [1, 3, 5, 7])
    for i in range(5, 9):
        result = player.get_visible_index(i)
        assert result == 4

    # toutes s'affichent
    set_inv(player, [10, 10, 0, 0])
    result = player.get_visible_index(5)
    assert result == 6
    result = player.get_visible_index(6)
    assert result == 8
    result = player.get_visible_index(7)
    assert result == 7
    result = player.get_visible_index(8)
    assert result == 5


def test_display_logic():
    player = Player()
    set_real_index(player, [1, 2, 3, 4, 5, 6, 7, 8])
    max = C.MAX_INVESTMENT

    # i invalide
    player.current_decision = 99
    result = display_logic(player)
    assert result == False

    # 5-8 faux
    set_inv(player, [5, 5, 5, 5])

    for i in range(1, 9):
        player.current_decision = i
        result = display_logic(player)
        assert result == (i <= 4)

    # 5-8 vrai
    set_inv(player, [max, max, 0, 0])

    for i in range(1, 9):
        player.current_decision = i
        result = display_logic(player)
        assert result == True


# Tests de proba plutot permissifs
def test_get_ball_color_without_blue():
    y_count = 0
    for i in range(0, 1000):
        result = get_ball_color(False)
        if result == "yellow":
            y_count += 1
    assert y_count > 450 and y_count < 550


def test_get_ball_color_with_blue():
    y_count = 0
    for i in range(0, 1000):
        result = get_ball_color(True)
        if result == "yellow":
            y_count += 1
    assert y_count > 280 and y_count < 580


def test_get_final_decision():
    player = Player()

    # 1 / 4
    set_inv(player, [0, 0, 0, 0])
    count = 0
    for i in range(0, 1000):
        if get_final_decision(player) == 1:
            count += 1
    assert count > 200 and count < 300

    # 1 / 8
    set_inv(player, [0, 0, 0, 0], [0, 0, 0, 0])
    count = 0
    for i in range(0, 1000):
        if get_final_decision(player) == 1:
            count += 1
    assert count > 75 and count < 175


def test_profit_1_2():
    assert profit_1_2(100, "yellow") == 300
    assert profit_1_2(100, "purple") == -100


def test_profit_3_4():
    assert profit_3_4(3, "yellow") == -7
    assert profit_3_4(3, "purple") == -16


def test_get_absolute_profit():
    n = C.MAX_INVESTMENT

    assert get_absolute_profit("A", "toto") == n

    assert get_absolute_profit("B", "yellow") == n // 2
    assert get_absolute_profit("B", "purple") == (n * 3) // 2

    assert get_absolute_profit("C", "yellow") == n // 2
    assert get_absolute_profit("C", "purple") == n
    assert get_absolute_profit("C", "blue") == (n * 3) // 2

    assert get_absolute_profit("D", "yellow") == 0
    assert get_absolute_profit("D", "purple") == n * 2


def test_profit_5_8():
    n = C.MAX_INVESTMENT

    assert profit_5_8(5, "A", "yellow") == n
    assert profit_5_8(6, "A", "yellow") == n

    assert profit_5_8(7, "A", "yellow") == -n
    assert profit_5_8(8, "A", "yellow") == -n
