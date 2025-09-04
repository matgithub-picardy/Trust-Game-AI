from otree.api import *
import random

doc = """
App oTree : risk_aversion

Description : 
- une tâche rémunérée qui permet de gagner C.ENDOWMENT jetons
- une série de jeux de décisions où le hasard joue un rôle
- une seule des décisions est tirée au sort pour déterminer le gain ou la perte.

Suite à des modifications de dernière minute, j'ai dû rajouter des fonctionnalités à la volée, en appliquant des rustines par-ci par là. 
J'en suis conscient mais je n'ai pas le temps de refaire proprement.

Auteur : Matthieu Comme (LEFMI)
Version : oTree 5+
"""


class C(BaseConstants):
    NAME_IN_URL = "risk_aversion"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    ENDOWMENT = cu(30)  # somme gagnée à la fin de la tâche
    MAX_INVESTMENT = 10
    PI_DIGITS = (
        "141 592 653 589 793 238 462 643 383 279 502 884 197 169 399 375 10"
        "5 820 974 944 592 307 816 406 286 208 998 628 034 825 342 117 067 9"
        "82 148 086 513 282 306 647 093 844 609 550 582 231 725 359 408 128"
        "48 111 745 028 410 270 193 852 110 555 964 462 294 895 493 038 196"
    )
    BALL_NUMBER = 60  # nombre total de boules dans l'urne
    CONVERSION_RATE = 0.5
    # RG, AG, RP, AP, CRG, CAG, CRP, CAP


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    # ces indices facilitent la lecture dans la base de données (ils sont = aux real_index)
    # sans devoir changer toute la structure logique
    # risque gain, ambiguite gain, ..., complement risque perte, complement ambiguite perte
    ordre_rg = models.IntegerField(initial=-1)
    ordre_ag = models.IntegerField(initial=-1)
    ordre_rp = models.IntegerField(initial=-1)
    ordre_ap = models.IntegerField(initial=-1)
    ordre_crg = models.IntegerField(initial=-1)
    ordre_cag = models.IntegerField(initial=-1)
    ordre_crp = models.IntegerField(initial=-1)
    ordre_cap = models.IntegerField(initial=-1)

    # Sommes investies à chaque décision
    # l'ordre suit celui défini juste au dessus
    inv1 = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
        blank=False,
    )
    inv2 = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
    )
    inv3 = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
    )
    inv4 = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
    )
    inv5 = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )
    inv6 = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )
    inv7 = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )
    inv8 = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )

    # indice réel de la décision choisie
    real_chosen_decision = models.IntegerField(initial=-1)

    ball_color = models.StringField(initial="")  # couleur de la boule
    profit = models.CurrencyField(initial=0)  # profit décision

    # chiffre à compter lors de la tâche, généré dans GeneralInfo
    target_digit = models.IntegerField(initial=0)
    pi_count = models.IntegerField(label="Combien de fois ce chiffre apparaît-il ?")

    # l'ordre des decisions 1 à 8 étant randomisés, ces indices sont ceux correspondant au cahier des charges
    real_index_1 = models.IntegerField(initial=-1)
    real_index_2 = models.IntegerField(initial=-1)
    real_index_3 = models.IntegerField(initial=-1)
    real_index_4 = models.IntegerField(initial=-1)
    real_index_5 = models.IntegerField(initial=-1)
    real_index_6 = models.IntegerField(initial=-1)
    real_index_7 = models.IntegerField(initial=-1)
    real_index_8 = models.IntegerField(initial=-1)

    # compteur suivant l'avancée dans les decisions
    current_decision = models.IntegerField(initial=1)

    confirmed_decision_count = models.IntegerField(initial=1)
    # indice relatif de la décision tirée au sort
    chosen_decision = models.IntegerField(initial=-1)

    # retourne l'indice réel de décision, conforme au cahier des charges
    def get_real_index(self, i=None) -> int:
        if i is None:
            i = self.current_decision
        if 1 <= i <= 8:
            return getattr(self, f"real_index_{i}")

    def get_all_real_index(self) -> list:
        return [getattr(self, f"real_index_{i}") for i in range(1, 9)]

    # opération inverse de la fonction précédente
    def get_index_from_real(self, real: int):
        real_index_list = [getattr(self, f"real_index_{i}") for i in range(1, 9)]
        return real_index_list.index(real) + 1

    # set la correspondance entre l'indice visible et le réel indice
    def init_real_index(self):
        index_map = create_index_map()
        set_ordre_risque_ambiguite(self, index_map)
        for i in range(1, 9):
            setattr(self, f"real_index_{i}", index_map[i - 1])

    # retourne vrai si la condition d'apparition de la décision real_index est remplie, faux sinon
    def condition_met(self, real_index: int) -> bool:

        # conditions d'affichage des décisions 5 à 8
        condition1 = self.inv1 == C.MAX_INVESTMENT
        condition2 = self.inv2 == C.MAX_INVESTMENT
        condition3 = self.inv3 == 0
        condition4 = self.inv4 == 0

        match real_index:
            case 5:
                result = condition1
            case 6:
                result = condition2
            case 7:
                result = condition3
            case 8:
                result = condition4

        return result

    # prend en entrée un indice réel
    # retourne l'indice visible par le joueur en prenant en compte celles qui sont masquées par des conditions
    def get_visible_index(self, indice) -> int:
        all_real_index = self.get_all_real_index()
        matching_index = all_real_index.index(indice) + 1

        if indice <= 4:
            return matching_index

        result = 4  # les 4 premières sont toujours visibles

        for i in range(4, matching_index):
            if self.condition_met(all_real_index[i]):
                result += 1

        return result

    # conserve les infos importantes concernant la décision tirée au sort pour les afficher à la toute fin de l'expérience
    def set_participant_vars(self):
        bc = self.ball_color
        """
        if bc is "yellow":
            bc = "jaune"
        elif bc is "purple":
            bc = "violette"
        else:
            bc = "bleue"
        """

        vars = self.participant.vars
        vars["chosen_decision"] = self.chosen_decision
        vars["invested"] = getattr(self, f"inv{self.real_chosen_decision}")
        vars["ball_color"] = bc
        vars["initial_amount"] = C.ENDOWMENT
        vars["profit_risk_aversion"] = self.profit
        vars["total_risk_aversion"] = self.payoff


# ----- FONCTIONS -----


# crée un ordre aléatoire de décisions. exemple : [4, 1, 3, 2, 7, 5, 8, 6]
# 1-4 sont première moitié de liste, 5-8 deuxième moitié
def create_index_map() -> list:
    liste1 = [1, 2, 3, 4]
    liste2 = [5, 6, 7, 8]

    random.shuffle(liste1)
    random.shuffle(liste2)

    return liste1 + liste2


# définit ordre_rg, ordre_ag etc...
def set_ordre_risque_ambiguite(player: Player, index_map: list):
    attr_names = [
        "ordre_rg",
        "ordre_ag",
        "ordre_rp",
        "ordre_ap",
        "ordre_crg",
        "ordre_cag",
        "ordre_crp",
        "ordre_cap",
    ]
    for attr, n in zip(attr_names, range(1, 9)):
        setattr(player, attr, index_map.index(n) + 1)


# logique d'affichage : vrai si décision 1 à 4, ou respecte les conditions pour 5 à 8, faux sinon
def display_logic(player: Player) -> bool:
    i = player.get_real_index()
    if i is None:
        return False
    max = C.MAX_INVESTMENT
    result = (
        i <= 4
        or (i == 5 and player.inv1 == max)
        or (i == 6 and player.inv2 == max)
        or (i == 7 and player.inv3 == 0)
        or (i == 8 and player.inv4 == 0)
    )
    return result


# utilisée pour debugger
def getTemplate(player: Player) -> dict:
    return {
        "confirmed_decision_count": player.confirmed_decision_count,
        "participant.payoff": player.participant.payoff,
        "current_decision": player.current_decision,
        "real_current_decision": player.get_real_index(),
        "chosen_decision": player.chosen_decision,
        "real_chosen_decision": player.real_chosen_decision,
        "real_index": player.get_all_real_index(),
        "inv1_4": [player.inv1, player.inv2, player.inv3, player.inv4],
        "inv5_8": [
            player.field_maybe_none("inv5"),
            player.field_maybe_none("inv6"),
            player.field_maybe_none("inv7"),
            player.field_maybe_none("inv8"),
        ],
    }


# retourne la couleur de la boule tirée au hasard
def get_ball_color(is_blue: bool) -> str:
    i = random.randint(0, (1 + is_blue))
    if i == 0:
        result = "yellow"
    elif i == 1:
        result = "purple"
    else:
        result = "blue"
    return result


# retourne l'indice réel de la décision tirée au sort
def get_final_decision(player: Player) -> int:
    decisions = [
        player.inv1,
        player.inv2,
        player.inv3,
        player.inv4,
        player.field_maybe_none("inv5"),
        player.field_maybe_none("inv6"),
        player.field_maybe_none("inv7"),
        player.field_maybe_none("inv8"),
    ]
    while True:
        i = random.randint(1, 8)
        if decisions[i - 1] is not None:
            break
    return i


# retourne le profit final
def final_profit(player: Player) -> Currency:

    i = player.real_chosen_decision = get_final_decision(player)
    player.chosen_decision = player.get_visible_index(i)
    invested = getattr(player, f"inv{i}")  # somme investie à cette décision

    # tirage de la boule, bleue uniquement présente si tirage = C
    ball_color = get_ball_color(False) if invested != "C" else get_ball_color(True)
    profit = 0
    if i == 1 or i == 2:
        profit = profit_1_2(invested, ball_color)
    elif i == 3 or i == 4:
        profit = profit_3_4(invested, ball_color)
    else:
        profit = profit_5_8(i, invested, ball_color)
    player.ball_color = ball_color
    return cu(profit)


# retourne le profit pour les décisions 1-8
def profit_1_2(invested: int, ball_color: str) -> int:
    return 3 * invested if ball_color == "yellow" else -invested


def profit_3_4(invested: int, ball_color: str) -> int:
    kept = C.MAX_INVESTMENT - invested
    return -kept if ball_color == "yellow" else -(3 * invested + kept)


def profit_5_8(current_decision: int, invested: int, ball_color: str) -> int:
    profit = get_absolute_profit(invested, ball_color)  # profit positif si i=5|6
    if current_decision == 7 or current_decision == 8:  # sinon profit négatif
        profit *= -1
    return profit


# retourne abs(profit) pour décisions 5-8
def get_absolute_profit(invested: str, ball_color: str) -> int:
    n = C.MAX_INVESTMENT

    match invested:
        case "A":
            result = n
        case "B":
            result = n // 2 if ball_color == "yellow" else (n * 3) // 2
        case "C":
            if ball_color == "yellow":
                result = n // 2
            elif ball_color == "purple":
                result = n
            else:
                result = (n * 3) // 2
        case "D":
            result = 0 if ball_color == "yellow" else n * 2

    return result


# retourne la balise pour l'emoji de boule
def get_ball_emoji(color) -> str:
    return f"<span class='ball {color}'></span>"


# les 3 fonctions suivantes servent à la mise en page des décisions 5-8
def get_li_items_5_8(known: bool) -> list:
    if known:
        n = C.BALL_NUMBER
        result = [
            f"Urne avec {n} {get_ball_emoji('yellow')} : vous êtes certain de tirer une boule {get_ball_emoji('yellow')}.",
            f"Urne avec {n//2} {get_ball_emoji('yellow')} et {n//2} {get_ball_emoji('purple')} : vous avez 1 chance sur 2 de tirer l’une des 2 couleurs.",
            f"Urne avec {n//3} {get_ball_emoji('yellow')}, {n//3} {get_ball_emoji('purple')} et {n//3} {get_ball_emoji('blue')} : vous avez 1 chance sur 3 de tirer l’une des 3 couleurs.",
        ]
    else:
        result = [
            f"Urne avec {get_ball_emoji('yellow')} : vous êtes certain de tirer une boule {get_ball_emoji('yellow')}.",
            f"Urne avec {get_ball_emoji('yellow')} et {get_ball_emoji('purple')} : vous ne connaissez pas vos chances de tirer chacune des 2 couleurs.",
            f"Urne avec {get_ball_emoji('yellow')}, {get_ball_emoji('purple')} et {get_ball_emoji('blue')} : vous ne connaissez pas vos chances de tirer chacune des 3 couleurs.",
        ]
    return result


# retourne les résultats des tirages 5 à 8 en adaptant si c'est un gain ou une perte de jetons
def get_results(win: bool) -> list:
    n = C.MAX_INVESTMENT
    if win:
        word = "gagnez"
    else:
        word = "perdez"

    return [
        f"Vous {word} {n} jetons",
        f"Boule {get_ball_emoji('yellow')} → vous {word} {n//2} jetons<br>Boule {get_ball_emoji('purple')}→ vous {word} {n*3//2} jetons",
        f"Boule {get_ball_emoji('yellow')} → vous {word} {n//2} jetons<br>Boule {get_ball_emoji('purple')}→ vous {word} {n} jetons<br>Boule {get_ball_emoji('blue')} → vous {word} {n*3//2} jetons",
        f"Boule {get_ball_emoji('yellow')} → vous {word} 0 jeton<br>Boule {get_ball_emoji('purple')}→ vous {word} {n*2} jetons",
    ]


# retourne le contenu des urnes, prend en compte s'il est connu ou non
def get_boxes(known: bool) -> list:
    n = demi = tier = ""
    if known:
        n = C.BALL_NUMBER
        demi = n // 2
        tier = n // 3

    return [
        f"{n} boules {get_ball_emoji('yellow')}",
        f"{demi} boules {get_ball_emoji('yellow')}<br>{demi} boules {get_ball_emoji('purple')}",
        f"{tier} boules {get_ball_emoji('yellow')}<br>{tier} boules {get_ball_emoji('purple')}<br>{tier} boules {get_ball_emoji('blue')}",
        f"{demi} boules {get_ball_emoji('yellow')}<br>{demi} boules {get_ball_emoji('purple')}",
    ]


# ----- PAGES -----


class GeneralInfo(Page):
    def vars_for_template(player: Player):
        rate = C.CONVERSION_RATE
        exemple1 = C.ENDOWMENT
        exemple2 = exemple1 // 3
        return {
            "rate": int(rate * 100),
            "exemple1_euros": int(exemple1 * rate),
            "exemple2": exemple2,
            "exemple2_euros": int(exemple2 * rate),
        }

    # Génère aléatoirement le chiffre à compter
    def before_next_page(player: Player, timeout_happened):
        player.init_real_index()
        player.target_digit = random.randint(0, 9)


class CountDigitTask(Page):
    form_model = "player"
    form_fields = ["pi_count"]

    @staticmethod
    def error_message(player: Player, values):
        correct_count = C.PI_DIGITS.count(str(player.target_digit))
        if values["pi_count"] != correct_count:
            return f"Incorrect. Réessayez."

    def vars_for_template(player: Player):
        return getTemplate(player) | dict(
            pi_digits=C.PI_DIGITS,
            digit=player.target_digit,
        )

    def before_next_page(player, timeout_happened):
        player.payoff = C.ENDOWMENT


class TaskSuccess(Page):

    def before_next_page(player: Player, timeout_happened):
        pass

    def vars_for_template(player: Player):
        return getTemplate(player)


class InvestmentConfirm(Page):

    def is_displayed(player: Player):
        result = display_logic(player)
        if not result:  # incrémente ici car on ne passera pas par before_next_page
            player.current_decision += 1
        return result

    def before_next_page(player: Player, timeout_happened):
        if player.current_decision <= 8:
            player.current_decision += 1
            player.confirmed_decision_count += 1

    def vars_for_template(player: Player):
        return getTemplate(player)


class InvestmentIntro1_4(Page):
    def vars_for_template(player: Player):
        return {"ball_number_per_color": C.BALL_NUMBER // 2} | getTemplate(player)


class InvestmentDecision1_4(Page):
    form_model = "player"

    def get_form_fields(player: Player):
        i = str(getattr(player, f"real_index_{player.current_decision}"))
        return ["inv" + i]

    def vars_for_template(player: Player):
        return getTemplate(player)


class InvestmentDecision5_8(Page):
    form_model = "player"

    def get_form_fields(player: Player):
        i = str(player.get_real_index())
        return ["inv" + i]

    def is_displayed(player: Player):
        return display_logic(player)

    # pour construire les tableaux
    def vars_for_template(player: Player):
        match player.get_real_index():
            case 5:
                known = True
                win = True
            case 6:
                known = False
                win = True
            case 7:
                known = True
                win = False
            case 8:
                known = False
                win = False

        return getTemplate(player) | {
            "rows": zip(["A", "B", "C", "D"], get_boxes(known), get_results(win)),
            "li_items": get_li_items_5_8(known),
        }


class TirageFinal(Page):

    def vars_for_template(player: Player):

        return getTemplate(player) | {"profit": player.profit}

    def before_next_page(player: Player, timeout_happened):
        player.profit = final_profit(player)
        player.payoff += player.profit


class Fin(Page):
    # pour essayer plusieurs tirages consécutifs
    # def is_displayed(player: Player):
    #    player.profit = final_profit(player)
    #    player.payoff += player.profit
    #    return True

    def vars_for_template(player: Player):
        return getTemplate(player) | {
            "initial_amount": C.ENDOWMENT,
            "invested": getattr(player, f"inv{player.real_chosen_decision}"),
            "ball_color": player.ball_color,
            "profit_risk_aversion": player.profit,
            "total_risk_aversion": player.payoff,
            "participant.payoff": player.participant.payoff,
        }

    def before_next_page(player: Player, timeout_happened):
        player.set_participant_vars()


# Création de page_sequence

page_sequence = [
    GeneralInfo,
    CountDigitTask,
    TaskSuccess,
]

# Ajoute les décisions 1-4

for i in range(0, 4):
    page_sequence.extend([InvestmentIntro1_4, InvestmentDecision1_4, InvestmentConfirm])

# Ajoute les décisions 5-8
for i in range(0, 4):
    page_sequence.extend([InvestmentDecision5_8, InvestmentConfirm])

page_sequence.extend([TirageFinal, Fin])
