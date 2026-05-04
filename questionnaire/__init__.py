from otree.api import *
from datetime import datetime
import settings

class C(BaseConstants):
    """Constantes et options de réponses pour le questionnaire."""
    NAME_IN_URL = "questionnaire"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    
    # Mapping des ordres d'étapes selon la configuration de session
    ORDRES_ETAPES = ["Ordre non défini", "Q/A/TG", "A/Q/TG", "Q/TG/A"]
    SHOW_UP_FEE = settings.SHOW_UP_FEE

    # Q1 choices
    Q1_CHOICES = [
        [1, "Jamais"],
        [2, "Rarement (quelques fois par an)"],
        [3, "Occasionnellement (quelques fois par mois)"],
        [4, "Régulièrement (plusieurs fois par semaine)"],
        [5, "Quotidiennement"],
    ]

    # Q3 choices
    Q3_CHOICES = [
        [1, "Je n'en utilise pas"],
        [2, "Moins de 6 mois"],
        [3, "Entre 6 mois et 1 an"],
        [4, "Entre 1 et 2 ans"],
        [5, "Plus de 2 ans"],
    ]

    # Q4 choices
    Q4_CHOICES = [
        [1, "Non, aucune"],
        [2, "Oui, de manière informelle (articles, vidéos, podcasts)"],
        [3, "Oui, dans le cadre de mes études ou de ma formation professionnelle"],
        [4, "Oui, j'ai suivi une formation dédiée (MOOC, certification, etc.)"],
    ]

    # Q6-Q12: Likert 1-7
    LIKERT_7_CHOICES = [
        [1, "1 - Pas du tout d'accord"],
        [2, "2"],
        [3, "3"],
        [4, "4 - Ni d'accord ni en désaccord"],
        [5, "5"],
        [6, "6"],
        [7, "7 - Tout à fait d'accord"],
    ]

    # Q13-Q31: Likert 1-7
    LIKERT_5_CHOICES = [
        [1, "1 - Pas du tout d'accord"],
        [2, "2"],
        [3, "3"],
        [4, "4 - Ni d'accord ni en désaccord"],
        [5, "5"],
        [6, "6"],
        [7, "7 - Tout à fait d'accord"],
    ]

    # Q33 choices
    Q33_CHOICES = [
        [1, "Femme"],
        [2, "Homme"],
        [3, "Je préfère ne pas répondre"],
    ]

    # Q34 choices
    Q34_CHOICES = [
        [1, "Brevet des collèges ou moins"],
        [2, "Baccalauréat (ou équivalent)"],
        [3, "Bac+2 / BTS / DUT"],
        [4, "Licence (Bac+3)"],
        [5, "Master (Bac+5)"],
        [6, "Doctorat"],
        [7, "Autre"],
    ]

    # Q35 choices
    Q35_CHOICES = [
        [1, "Sciences économiques, gestion, finance"],
        [2, "Sciences sociales, psychologie, sociologie"],
        [3, "Sciences exactes, ingénierie, informatique"],
        [4, "Droit, sciences politiques"],
        [5, "Lettres, arts, sciences humaines"],
        [6, "Santé, médecine"],
        [7, "Autre"],
    ]

    # Q36 choices
    Q36_CHOICES = [
        [1, "Moins de 1 000 €"],
        [2, "1 000 – 1 999 €"],
        [3, "2 000 – 2 999 €"],
        [4, "3 000 – 3 999 €"],
        [5, "4 000 € et plus"],
        [6, "Je préfère ne pas répondre"],
    ]

    # Q37 choices
    Q37_CHOICES = [
        [1, "Étudiant(e)"],
        [2, "Salarié(e) du secteur privé"],
        [3, "Salarié(e) du secteur public"],
        [4, "Travailleur(se) indépendant(e) / freelance"],
        [5, "Sans emploi"],
        [6, "Retraité(e)"],
        [7, "Autre"],
    ]

    # Q39 choices
    Q39_CHOICES = [
        [1, "Non, jamais"],
        [2, "Oui, une ou deux fois"],
        [3, "Oui, plusieurs fois (3–4 fois)"],
        [4, "Oui, régulièrement (5 fois ou plus)"],
    ]

    # Q40 choices
    Q40_CHOICES = [
        [1, "Non"],
        [2, "Oui, une ou deux fois"],
        [3, "Oui, plusieurs fois"],
    ]

    # SVO items : 9 options par item (Option 1 à Option 9)
    SVO_CHOICES = [[i, str(i)] for i in range(1, 10)]

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Metadonnées
    date = models.StringField(doc="Date de passation de l'expérience.")
    ordre_etapes = models.StringField(doc="Ordre des applications pour ce participant.")
    session_group = models.IntegerField(initial=0, doc="ID du groupe de session.")
    player_name = models.StringField(blank=True)
    go_back = models.BooleanField(initial=False, doc="Indicateur de navigation arrière.")

    # ==== PARTIE 1 ====
    q1 = models.IntegerField(label="Q1. À quelle fréquence utilisez-vous des outils basés sur l'intelligence artificielle (ChatGPT, Copilot, Gemini, Mistral, Claude, etc.) ?", choices=C.Q1_CHOICES, widget=widgets.RadioSelect)
    
    # Q2 Checkboxes
    q2_travail = models.BooleanField(label="Travail / vie professionnelle", blank=True, widget=widgets.CheckboxInput)
    q2_etudes = models.BooleanField(label="Études ou formation", blank=True, widget=widgets.CheckboxInput)
    q2_redaction = models.BooleanField(label="Rédaction et aide à l'écriture", blank=True, widget=widgets.CheckboxInput)
    q2_recherche = models.BooleanField(label="Recherche d'informations", blank=True, widget=widgets.CheckboxInput)
    q2_programmation = models.BooleanField(label="Programmation / développement informatique", blank=True, widget=widgets.CheckboxInput)
    q2_loisirs = models.BooleanField(label="Loisirs et créativité (image, musique, jeux…)", blank=True, widget=widgets.CheckboxInput)
    q2_decision = models.BooleanField(label="Prise de décision personnelle (achats, santé, voyage…)", blank=True, widget=widgets.CheckboxInput)
    q2_aucun = models.BooleanField(label="Je n'en utilise pas", blank=True, widget=widgets.CheckboxInput)

    q3 = models.IntegerField(label="Q3. Depuis combien de temps utilisez-vous ce type d'outil ?", choices=C.Q3_CHOICES, widget=widgets.RadioSelect)
    q4 = models.IntegerField(label="Q4. Avez-vous suivi une formation ou lu des ressources spécifiques sur le fonctionnement de l'IA ?", choices=C.Q4_CHOICES, widget=widgets.RadioSelect)

    # Q5 Checkboxes
    q5_chatgpt = models.BooleanField(label="ChatGPT (OpenAI)", blank=True, widget=widgets.CheckboxInput)
    q5_copilot = models.BooleanField(label="Copilot (Microsoft)", blank=True, widget=widgets.CheckboxInput)
    q5_gemini = models.BooleanField(label="Gemini (Google)", blank=True, widget=widgets.CheckboxInput)
    q5_claude = models.BooleanField(label="Claude (Anthropic)", blank=True, widget=widgets.CheckboxInput)
    q5_mistral = models.BooleanField(label="Mistral / Le Chat", blank=True, widget=widgets.CheckboxInput)
    q5_perplexity = models.BooleanField(label="Perplexity AI", blank=True, widget=widgets.CheckboxInput)
    q5_integre = models.BooleanField(label="Un outil IA intégré à un logiciel métier (ex. : suite Office, outil de design, CRM…)", blank=True, widget=widgets.CheckboxInput)
    q5_aucun = models.BooleanField(label="Aucun de ces outils", blank=True, widget=widgets.CheckboxInput)

    # ==== PARTIE 2 ====
    q6 = models.IntegerField(label="Q6. Je fais généralement confiance aux informations fournies par les outils d'IA.", choices=C.LIKERT_7_CHOICES, widget=widgets.RadioSelectHorizontal)
    q7 = models.IntegerField(label="Q7. Les outils d'IA me semblent fiables pour m'aider à prendre des décisions importantes.", choices=C.LIKERT_7_CHOICES, widget=widgets.RadioSelectHorizontal)
    q8 = models.IntegerField(label="Q8. Je pense que les outils d'IA peuvent facilement se tromper ou donner de mauvais conseils. (R)", choices=C.LIKERT_7_CHOICES, widget=widgets.RadioSelectHorizontal)
    q9 = models.IntegerField(label="Q9. Je me sens à l'aise à l'idée de laisser une IA influencer certaines de mes décisions.", choices=C.LIKERT_7_CHOICES, widget=widgets.RadioSelectHorizontal)
    q10 = models.IntegerField(label="Q10. Je vérifie systématiquement les réponses d'une IA avant d'agir en conséquence. (R)", choices=C.LIKERT_7_CHOICES, widget=widgets.RadioSelectHorizontal)
    q11 = models.IntegerField(label="Q11. Je considère que les outils d'IA actuels sont globalement compétents dans tâches pour lesquelles ils sont conçus.", choices=C.LIKERT_7_CHOICES, widget=widgets.RadioSelectHorizontal)
    q12 = models.IntegerField(label="Q12. Je pense que les systèmes d'IA sont suffisamment transparents sur leur fonctionnement et leurs limites.", choices=C.LIKERT_7_CHOICES, widget=widgets.RadioSelectHorizontal)

    # ==== PARTIE 3 ====
    q13 = models.IntegerField(label="Q13. L'essor de l'IA me préoccupe pour l'avenir de l'emploi.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q14 = models.IntegerField(label="Q14. Je crains que les outils d'IA ne soient utilisés pour manipuler les comportements humains.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q15 = models.IntegerField(label="Q15. Je pense que les IA reproduisent des biais qui les rendent injustes envers certains groupes de personnes.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q16 = models.IntegerField(label="Q16. L'utilisation généralisée de l'IA dans la société me rend globalement mal à l'aise.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q17 = models.IntegerField(label="Q17. Je m'inquiète de l'impact de l'IA sur la protection de ma vie privée et de mes données personnelles.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q18 = models.IntegerField(label="Q18. Je me sens capable de détecter quand une IA essaie d'orienter mes choix ou mes opinions.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q19 = models.IntegerField(label="Q19. Je crains que le recours croissant à l'IA ne réduise progressivement notre capacité à penser et décider par nous-mêmes.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)

    # ==== PARTIE 4 (SVO) ====
    svo_item_1 = models.IntegerField(choices=C.SVO_CHOICES, widget=widgets.RadioSelect)
    svo_item_2 = models.IntegerField(choices=C.SVO_CHOICES, widget=widgets.RadioSelect)
    svo_item_3 = models.IntegerField(choices=C.SVO_CHOICES, widget=widgets.RadioSelect)
    svo_item_4 = models.IntegerField(choices=C.SVO_CHOICES, widget=widgets.RadioSelect)
    svo_item_5 = models.IntegerField(choices=C.SVO_CHOICES, widget=widgets.RadioSelect)
    svo_item_6 = models.IntegerField(choices=C.SVO_CHOICES, widget=widgets.RadioSelect)

    # ==== PARTIE 5 ====
    q20 = models.IntegerField(label="Q20. Si quelqu'un me rend service, je fais tout mon possible pour lui rendre la pareille, même si cela me prend du temps ou me coûte quelque chose.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q21 = models.IntegerField(label="Q21. Je m'efforce d'aider les personnes qui m'ont aidé par le passé, même lorsque cela représente un effort de ma part.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q22 = models.IntegerField(label="Q22. Si quelqu'un me cause du tort intentionnellement, je cherche à rétablir l'équité, même si cela a un coût pour moi.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q23 = models.IntegerField(label="Q23. Lorsque quelqu'un m'a traité injustement, je cherche à lui faire comprendre que ce comportement a des conséquences.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q24 = models.IntegerField(label="Q24. Je fais volontiers confiance à un inconnu, même sans aucune garantie de sa part.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q25 = models.IntegerField(label="Q25. Je préfère renoncer à un gain personnel plutôt que de profiter d'une situation au détriment d'une autre personne.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)

    # ==== PARTIE 6 ====
    q26 = models.IntegerField(label="Q26. En général, on peut faire confiance aux gens.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q27 = models.IntegerField(label="Q27. La plupart des gens essaient d'être honnêtes dans leurs rapports aux autres.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q28 = models.IntegerField(label="Q28. On ne peut jamais être trop prudent dans ses relations avec les autres. (R)", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q29 = models.IntegerField(label="Q29. La plupart des gens profiteraient de vous si l'occasion se présentait. (R)", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q30 = models.IntegerField(label="Q30. La plupart des gens respectent les règles et les normes sociales même lorsque personne ne les surveille.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)
    q31 = models.IntegerField(label="Q31. Je pense que la majorité des gens ont de bonnes intentions envers autrui.", choices=C.LIKERT_5_CHOICES, widget=widgets.RadioSelectHorizontal)

    # ==== PARTIE 7 ====
    q32 = models.IntegerField(label="Q32. Quel est votre âge ? (en années)")
    q33 = models.IntegerField(label="Q33. Quel est votre genre ?", choices=C.Q33_CHOICES, widget=widgets.RadioSelect)
    q34 = models.IntegerField(label="Q34. Quel est votre niveau d'études le plus élevé obtenu ?", choices=C.Q34_CHOICES, widget=widgets.RadioSelect)
    q35 = models.IntegerField(label="Q35. Dans quel domaine avez-vous principalement étudié ou travaillez-vous ?", choices=C.Q35_CHOICES, widget=widgets.RadioSelect)
    q35_autre = models.StringField(blank=True, label="Autre domaine :")
    q36 = models.IntegerField(label="Q36. Dans quelle tranche se situe votre revenu mensuel net personnel (en euros) ?", choices=C.Q36_CHOICES, widget=widgets.RadioSelect)
    q37 = models.IntegerField(label="Q37. Quelle est votre situation professionnelle actuelle ?", choices=C.Q37_CHOICES, widget=widgets.RadioSelect)
    q38 = models.StringField(label="Q38. Dans quel pays résidez-vous actuellement ?")
    q39 = models.IntegerField(label="Q39. Avez-vous déjà participé à une expérience économique (jeu de confiance, dilemme du prisonnier, jeu de l'ultimatum…) ?", choices=C.Q39_CHOICES, widget=widgets.RadioSelect)
    q40 = models.IntegerField(label="Q40. Avez-vous déjà participé spécifiquement à un jeu de confiance (Trust Game) avant aujourd'hui ?", choices=C.Q40_CHOICES, widget=widgets.RadioSelect)


# ==== PAGES ====

class Welcome(Page):
    def before_next_page(player, timeout_happened):
        config_name = player.session.config.get("name", "")
        if config_name == "groupe_1":
            n = 1
        elif config_name == "groupe_2":
            n = 2
        elif config_name == "groupe_3":
            n = 3
        else:
            n = 0
        player.ordre_etapes = C.ORDRES_ETAPES[n]
        player.session_group = n
        player.date = datetime.now().strftime("%d-%b-%y")
        player.participant.vars["show_up_fee"] = C.SHOW_UP_FEE

class Part1(Page):
    form_model = "player"
    form_fields = [
        "q1", 
        "q2_travail", "q2_etudes", "q2_redaction", "q2_recherche", "q2_programmation", "q2_loisirs", "q2_decision", "q2_aucun",
        "q3", "q4",
        "q5_chatgpt", "q5_copilot", "q5_gemini", "q5_claude", "q5_mistral", "q5_perplexity", "q5_integre", "q5_aucun"
    ]
    def before_next_page(player, timeout_happened):
        if player.go_back:
            player._index_in_pages -= 2
            player.go_back = False

class Part2(Page):
    form_model = "player"
    form_fields = ["q6", "q7", "q8", "q9", "q10", "q11", "q12"]
    def before_next_page(player, timeout_happened):
        if player.go_back:
            player._index_in_pages -= 2
            player.go_back = False

class Part3(Page):
    form_model = "player"
    form_fields = ["q13", "q14", "q15", "q16", "q17", "q18", "q19"]
    def before_next_page(player, timeout_happened):
        if player.go_back:
            player._index_in_pages -= 2
            player.go_back = False

class Part4(Page):
    form_model = "player"
    form_fields = ["svo_item_1", "svo_item_2", "svo_item_3", "svo_item_4", "svo_item_5", "svo_item_6"]
    def before_next_page(player, timeout_happened):
        if player.go_back:
            player._index_in_pages -= 2
            player.go_back = False

class Part5(Page):
    form_model = "player"
    form_fields = ["q20", "q21", "q22", "q23", "q24", "q25"]
    def before_next_page(player, timeout_happened):
        if player.go_back:
            player._index_in_pages -= 2
            player.go_back = False

class Part6(Page):
    form_model = "player"
    form_fields = ["q26", "q27", "q28", "q29", "q30", "q31"]
    def before_next_page(player, timeout_happened):
        if player.go_back:
            player._index_in_pages -= 2
            player.go_back = False

class Part7(Page):
    form_model = "player"
    form_fields = ["q32", "q33", "q34", "q35", "q35_autre", "q36", "q37", "q38", "q39", "q40"]
    def before_next_page(player, timeout_happened):
        if player.go_back:
            player._index_in_pages -= 2
            player.go_back = False

class Login(Page):
    form_model = "player"
    form_fields = ["player_name"]

class Conclusion(Page):
    pass

page_sequence = [
    Welcome,
    Part1,
    Part2,
    Part3,
    Part4,
    Part5,
    Part6,
    Part7,
    Conclusion,
]
