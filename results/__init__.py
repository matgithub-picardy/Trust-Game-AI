"""
Application oTree pour la synthèse finale des gains.
Calcule et affiche le montant total accumulé par le participant à travers
toutes les applications de la session (Show Up Fee, Risk Aversion, Trust Game).
"""
from otree.api import *
import settings


class C(BaseConstants):
    """Paramètres financiers globaux pour le calcul des gains finaux."""
    NAME_IN_URL = "results"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    
    SHOW_UP_FEE = cu(settings.SHOW_UP_FEE)
    CONVERSION_RATE = settings.CONVERSION_RATE


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    """Stocke le bilan financier final du participant."""
    gain_total = models.CurrencyField(doc="Somme totale des gains en jetons (toutes applis confondues).")
    gain_euros = models.FloatField(doc="Conversion finale des jetons en euros réels.")


# PAGES



class Results(Page):
    """Page finale récapitulant l'ensemble des gains de la session expérimentale."""
    
    def vars_for_template(player: Player):
        """Agrège les résultats stockés dans participant.vars et calcule le gain final."""
        player.gain_total = C.SHOW_UP_FEE

        vars = player.participant.vars
        gain_risk_aversion = cu(vars["total_risk_aversion"])

        tg_role = vars.get("tg_role")
        vars_tg = {}

        # Intégration optionnelle des résultats du Trust Game (si joué)
        if tg_role:
            endowment = int(vars.get("tg_endowment"))
            mult = int(vars.get("tg_multiplier"))
            sent = int(vars.get("tg_sent"))
            sent_back = int(vars.get("tg_sent_back"))

            if tg_role == "A":
                tg_gain = cu(endowment - sent + sent_back)
            else:
                tg_gain = cu(mult * sent - sent_back)

            player.gain_total += tg_gain

            vars_tg = {
                "tg_endowment": endowment,
                "tg_sent": sent,
                "tg_multiplier": mult,
                "tg_sent_back": sent_back,
                "tg_gain": tg_gain,
            }

        player.gain_total += gain_risk_aversion
        player.gain_euros = round(float(player.gain_total * C.CONVERSION_RATE), 2)

        return {
            "show_up_fee": C.SHOW_UP_FEE,
            "chosen_decision": vars["chosen_decision"],
            "invested": vars["invested"],
            "ball_color": vars["ball_color"],
            "initial_amount": vars["initial_amount"],
            "profit_risk_aversion": vars["profit_risk_aversion"],
            "gain_risk_aversion": gain_risk_aversion,
            "gain_total": player.gain_total,
            "tg_role": tg_role,
            "tg_gain": cu(0),
            "converted_gain": player.gain_euros,
        } | vars_tg


page_sequence = [Results]
