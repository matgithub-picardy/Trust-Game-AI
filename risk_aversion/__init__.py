"""
Application oTree pour la mesure de l'aversion au risque et à l'ambiguïté.

Description :
- Tâche de comptage de chiffres (PI) rémunérée à hauteur de C.ENDOWMENT.
- Série de 8 décisions d'investissement (Risque/Ambiguïté) en jetons et par tirage.
- Tirage au sort d'une décision finale pour déterminer le gain additionnel.
"""
from otree.api import *
import random


class C(BaseConstants):
    """Constantes globales pour la mesure d'aversion au risque."""
    NAME_IN_URL = "risk_aversion"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    
    ENDOWMENT = cu(30)  # Rémunération de la tâche initiale
    MAX_INVESTMENT = 10
    
    # Données pour la tâche de comptage (PI)
    PI_DIGITS = (
        "141 592 653 589 793 238 462 643 383 279 502 884 197 169 399 375 10"
        "5 820 974 944 592 307 816 406 286 208 998 628 034 825 342 117 067 9"
        "82 148 086 513 282 306 647 093 844 609 550 582 231 725 359 408 128"
        "48 111 745 028 410 270 193 852 110 555 964 462 294 895 493 038 196"
    )
    BALL_NUMBER = 60  # Population totale de l'urne
    CONVERSION_RATE = 0.5 # Taux de conversion jetons -> euros
    
    # Mapping des indices de décision vers les champs de données
    FIELD_MAP = {
        1: 'dec_risque_gain',
        2: 'dec_ambig_gain',
        3: 'dec_risque_perte',
        4: 'dec_ambig_perte',
        5: 'dec_comp_risque_gain',
        6: 'dec_comp_ambig_gain',
        7: 'dec_comp_risque_perte',
        8: 'dec_comp_ambig_perte'
    }


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    """Contenu des données par participant pour l'application risk_aversion."""
    
    # Positionnement aléatoire pour l'export des données
    ordre_rg = models.IntegerField(initial=-1, doc="Ordre d'affichage de Risque Gain")
    ordre_ag = models.IntegerField(initial=-1, doc="Ordre d'affichage de Ambiguïté Gain")
    ordre_rp = models.IntegerField(initial=-1, doc="Ordre d'affichage de Risque Perte")
    ordre_ap = models.IntegerField(initial=-1, doc="Ordre d'affichage de Ambiguïté Perte")
    ordre_crg = models.IntegerField(initial=-1, doc="Ordre d'affichage de Complément Risque Gain")
    ordre_cag = models.IntegerField(initial=-1, doc="Ordre d'affichage de Complément Ambiguïté Gain")
    ordre_crp = models.IntegerField(initial=-1, doc="Ordre d'affichage de Complément Risque Perte")
    ordre_cap = models.IntegerField(initial=-1, doc="Ordre d'affichage de Complément Ambiguïté Perte")

    # Décisions 1 à 4 (Investissement direct)
    dec_risque_gain = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
        blank=False,
    )
    dec_ambig_gain = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
    )
    dec_risque_perte = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
    )
    dec_ambig_perte = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, C.MAX_INVESTMENT + 1)],
        initial=-1,
        label="Je décide d'investir :",
    )
    
    # Décisions 5 à 8 (Choix de tirage)
    dec_comp_risque_gain = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )
    dec_comp_ambig_gain = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )
    dec_comp_risque_perte = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )
    dec_comp_ambig_perte = models.StringField(
        choices=["A", "B", "C", "D"], label="Je choisis le tirage :"
    )

    # État du tirage final et résultats
    real_chosen_decision = models.IntegerField(initial=-1, doc="Indice réel de la décision tirée au sort.")
    ball_color = models.StringField(initial="", doc="Couleur de la boule résultant du tirage.")
    profit = models.CurrencyField(initial=0, doc="Gain ou perte généré par la décision finale.")

    # Tâche préliminaire (PI)
    target_digit = models.IntegerField(initial=0, doc="Chiffre cible à compter dans PI.")
    pi_count = models.IntegerField(label="Combien de fois ce chiffre apparaît-il ?")

    # Mapping interne pour la randomisation
    real_index_1 = models.IntegerField(initial=-1)
    real_index_2 = models.IntegerField(initial=-1)
    real_index_3 = models.IntegerField(initial=-1)
    real_index_4 = models.IntegerField(initial=-1)
    real_index_5 = models.IntegerField(initial=-1)
    real_index_6 = models.IntegerField(initial=-1)
    real_index_7 = models.IntegerField(initial=-1)
    real_index_8 = models.IntegerField(initial=-1)

    current_decision = models.IntegerField(initial=1, doc="Numéro de l'étape de décision en cours.")
    confirmed_decision_count = models.IntegerField(initial=1)
    chosen_decision = models.IntegerField(initial=-1, doc="Indice relatif affiché au joueur pour le résultat.")

    def get_real_index(self, i=None) -> int:
        """Retourne l'indice réel (1-8) correspondant à la position d'affichage i."""
        if i is None:
            i = self.current_decision
        if 1 <= i <= 8:
            return getattr(self, f"real_index_{i}")

    def get_all_real_index(self) -> list:
        """Récupère la liste complète du mapping de randomisation."""
        return [getattr(self, f"real_index_{i}") for i in range(1, 9)]

    def get_index_from_real(self, real: int):
        """Détermine la position d'affichage d'une décision réelle donnée."""
        real_index_list = [getattr(self, f"real_index_{i}") for i in range(1, 9)]
        return real_index_list.index(real) + 1

    def init_real_index(self):
        """Initialise le mapping aléatoire des décisions au début de la session pour un joueur."""
        index_map = create_index_map()
        set_ordre_risque_ambiguite(self, index_map)
        for i in range(1, 9):
            setattr(self, f"real_index_{i}", index_map[i - 1])

    def condition_met(self, real_index: int) -> bool:
        """Vérifie si les conditions d'affichage pour les décisions complexes (5-8) sont remplies."""
        condition1 = self.dec_risque_gain == C.MAX_INVESTMENT
        condition2 = self.dec_ambig_gain == C.MAX_INVESTMENT
        condition3 = self.dec_risque_perte == 0
        condition4 = self.dec_ambig_perte == 0

        match real_index:
            case 5: result = condition1
            case 6: result = condition2
            case 7: result = condition3
            case 8: result = condition4
            case _: result = True
        return result

    def get_visible_index(self, indice) -> int:
        """Calcule l'indice séquentiel visible par le participant, en sautant les décisions masquées."""
        all_real_index = self.get_all_real_index()
        matching_index = all_real_index.index(indice) + 1

        if indice <= 4:
            return matching_index

        result = 4  # Les 4 premières décisions sont toujours affichées
        for i in range(4, matching_index):
            if self.condition_met(all_real_index[i]):
                result += 1
        return result

    def set_participant_vars(self):
        """Exporte les résultats du tirage final vers participant.vars pour synthèse globale."""
        bc = self.ball_color
        
        # Traduction des noms de couleurs pour l'interface finale
        if bc == "yellow":
            bc = "jaune"
        elif bc == "purple":
            bc = "violette"
        else:
            bc = "bleue"

        vars = self.participant.vars
        vars["chosen_decision"] = self.chosen_decision
        vars["invested"] = getattr(self, C.FIELD_MAP[self.real_chosen_decision])
        vars["ball_color"] = bc
        vars["initial_amount"] = C.ENDOWMENT
        vars["profit_risk_aversion"] = self.profit
        vars["total_risk_aversion"] = self.payoff


# ----- FONCTIONS -----


# --- Logique d'index mapping ---
#
# Les 8 décisions du cahier des charges sont présentées dans un ordre aléatoire au participant.
# On distingue deux groupes :
#   - Décisions 1-4 : gain/perte avec investissement en jetons (int)
#   - Décisions 5-8 : gain/perte avec choix de tirage (lettre A-D)
# L'ordre est randomisé à l'intérieur de chaque groupe, mais le groupe 1-4
# est toujours présenté avant le groupe 5-8.
#
# Exemple de mapping généré : [3, 1, 4, 2, 6, 8, 5, 7]
# → la 1ère décision affichée correspond à la décision réelle n°3, etc.
#
# Les attributs "ordre_rg", "ordre_ag" etc. stockent la position d'affichage
# de chaque type de décision (RG = Risque Gain, AG = Ambiguïté Gain, etc.)
# pour faciliter la lecture des données exportées.

def create_index_map() -> list:
    """Génère un ordre aléatoire des 8 décisions, en conservant le bloc 1-4 avant 5-8."""
    groupe_1_4 = [1, 2, 3, 4]
    groupe_5_8 = [5, 6, 7, 8]
    random.shuffle(groupe_1_4)
    random.shuffle(groupe_5_8)
    return groupe_1_4 + groupe_5_8


def set_ordre_risque_ambiguite(player: Player, index_map: list):
    """Stocke la position d'affichage de chaque type de décision pour l'export des données."""
    attr_names = [
        "ordre_rg", "ordre_ag", "ordre_rp", "ordre_ap",
        "ordre_crg", "ordre_cag", "ordre_crp", "ordre_cap"
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
        or (i == 5 and player.dec_risque_gain == max)
        or (i == 6 and player.dec_ambig_gain == max)
        or (i == 7 and player.dec_risque_perte == 0)
        or (i == 8 and player.dec_ambig_perte == 0)
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
        "inv1_4": [player.dec_risque_gain, player.dec_ambig_gain, player.dec_risque_perte, player.dec_ambig_perte],
        "inv5_8": [
            player.field_maybe_none("dec_comp_risque_gain"),
            player.field_maybe_none("dec_comp_ambig_gain"),
            player.field_maybe_none("dec_comp_risque_perte"),
            player.field_maybe_none("dec_comp_ambig_perte"),
        ],
    }


def get_ball_color(has_blue_ball: bool) -> str:
    """Tire au hasard une couleur de boule (Jaune, Violette ou Bleue si applicable)."""
    i = random.randint(0, (1 + has_blue_ball))
    if i == 0: return "yellow"
    if i == 1: return "purple"
    return "blue"


def get_final_decision(player: Player) -> int:
    """Tire au sort une décision valide parmi celles effectivement présentées au participant."""
    decisions = [
        player.dec_risque_gain,
        player.dec_ambig_gain,
        player.dec_risque_perte,
        player.dec_ambig_perte,
        player.field_maybe_none("dec_comp_risque_gain"),
        player.field_maybe_none("dec_comp_ambig_gain"),
        player.field_maybe_none("dec_comp_risque_perte"),
        player.field_maybe_none("dec_comp_ambig_perte"),
    ]
    while True:
        i = random.randint(1, 8)
        value = decisions[i - 1]
        if value is not None and value != -1:
            break
    return i


# retourne le profit final
def final_profit(player: Player) -> Currency:
    """
    Calcule le profit de la décision tirée au sort.
    Étapes :
      1. Tirer une décision valide (non -1, non None)
      2. Récupérer la mise correspondante
      3. Tirer la couleur de boule (bleue uniquement possible pour le tirage "C" des décisions 5-8)
      4. Calculer le profit selon le type de décision (1-2, 3-4, ou 5-8)
    """
    chosen_real_index = get_final_decision(player)
    player.real_chosen_decision = chosen_real_index
    player.chosen_decision = player.get_visible_index(chosen_real_index)

    invested = getattr(player, C.FIELD_MAP[chosen_real_index])

    # La boule bleue n'existe que pour le tirage "C" des décisions 5-8
    has_blue_ball = (invested == "C")
    ball_color = get_ball_color(has_blue_ball)

    if chosen_real_index in (1, 2):
        profit = profit_1_2(invested, ball_color)
    elif chosen_real_index in (3, 4):
        profit = profit_3_4(invested, ball_color)
    else:
        profit = profit_5_8(chosen_real_index, invested, ball_color)

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
    @staticmethod
    def is_displayed(player: Player):
        return player.current_decision == 1

    def vars_for_template(player: Player):
        return {"ball_number_per_color": C.BALL_NUMBER // 2} | getTemplate(player)


class InvestmentDecision1_4(Page):
    form_model = "player"

    def get_form_fields(player: Player):
        i = getattr(player, f"real_index_{player.current_decision}")
        return [C.FIELD_MAP[i]]

    def vars_for_template(player: Player):
        i = getattr(player, f"real_index_{player.current_decision}")
        return getTemplate(player) | {"field_name": C.FIELD_MAP[i]}

    @staticmethod
    def error_message(player: Player, values):
        """Bloque la soumission si la valeur est la sentinelle -1 (champ non rempli)."""
        field = C.FIELD_MAP[getattr(player, f"real_index_{player.current_decision}")]
        val = values.get(field)
        if val is None or val == -1:
            return {field: "Veuillez s\u00e9lectionner un montant avant de valider."}


class InvestmentDecision5_8(Page):
    form_model = "player"

    def get_form_fields(player: Player):
        i = player.get_real_index()
        return [C.FIELD_MAP[i]]

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
            "field_name": C.FIELD_MAP[player.get_real_index()],
        }


class TirageFinal(Page):

    def vars_for_template(player: Player):

        return getTemplate(player) | {"profit": player.profit}

    def before_next_page(player: Player, timeout_happened):
        player.profit = final_profit(player)
        player.payoff += player.profit


class Fin(Page):
    """Page finale récapitulant les gains de l'application risk_aversion."""
    def vars_for_template(player: Player):
        return getTemplate(player) | {
            "initial_amount": C.ENDOWMENT,
            "invested": getattr(player, C.FIELD_MAP[player.real_chosen_decision]),
            "ball_color": player.ball_color,
            "profit_risk_aversion": player.profit,
            "total_risk_aversion": player.payoff,
            "participant_payoff": player.participant.payoff_plus_participation_fee(),
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
