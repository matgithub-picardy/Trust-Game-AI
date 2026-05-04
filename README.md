# Trust-Game-AI

Trust-Game-AI est une plateforme d'économie expérimentale basée sur oTree permettant d'étudier le fonctionnement de la confiance et de la réciprocité économiques (basé sur le **Trust Game** de Berg, Dickhaut et McCabe), augmenté de l'intervention d'un assistant d'Intelligence Artificielle (ChatGPT). 

Le projet a été développé pour évaluer comment les conseils donnés par une IA, lorsqu’elle adopte différents biais comportementaux ("stratège", "altruiste", "neutre"), parviennent (ou non) à influencer la prise de décision conjointe et modifient les issues sociales au sein du Trust Game.

## Fonctionnalités Clés

- **Jeu de la Confiance Classique (Trust Game)** : Intégration complète de la mécanique (donation, triplement, puis renvoi) avec calculs automatiques des gains.
- **Intervention de Modèle de Langage (LLM)** : ChatGPT (via l'API OpenAI `gpt-3.5-turbo`) analyse les chats entre joueurs et dispense des conseils contextuels aux participants.
- **Module "Cheap Talk"** : Messagerie instantanée intégrée qui permet aux deux joueurs de discuter avec indicateur de frappe en temps réel avant leur prise de décision.
- **Répartition Dynamique** : Module **Dispatcher** centralisé facilitant l'assignation automatique et fluide des cohortes de participants pour réaliser des traitements expérimentaux comparés (sessions de groupes modulables).
- **Mesures d'Aversion au Risque & Questionnaire** : Modules pré-inclus pour récupérer des indicateurs clés utiles à la recherche par l'expérimentateur.

---

## Tech Stack

- **Langage** : Python 3.12+ (recommandé)
- **Framework** : oTree 5.11+ (basé sur Django/Starlette)
- **Modèle IA** : GPT-3.5-Turbo de OpenAI  
- **Base de données** : PostgreSQL (prod) / SQLite (développement)
- **Communication Temps Réel** : `channels_redis` et WebSockets natifs d'oTree
- **Déploiement** : Configure pour Heroku via base Procfile.

---

## Architecture du Projet

Le canevas est divisé en plusieurs « applications oTree » s’exécutant de façon séquentielle.

```text
Trust-Game-AI/
 ├── dispatcher/         # Route d'aiguillage des cohortes vers leurs traitements
 ├── intro/              # Accueil, consentement éclairé et présentation du jeu
 ├── questionnaire/      # Collecte de données socio-démographiques finales
 ├── risk_aversion/      # Mésure individuelle d'aversion au risque
 ├── trust_game/         # Application cœur : Trust Game + Chat + IA 
 ├── chatgpt/            # Module d'architecture pour le test de ChatGPT seul
 ├── tests/              # Tests unitaires Pytest pour assurer la conformité
 ├── _rooms/             # Fichiers .txt de gestions de "Waiting rooms" oTree
 ├── requirements.txt    # Liste intégrale des dépendances Python
 ├── settings.py         # Configuration générale d'oTree (Variables, Séquences, Définitions des groupes)
 └── Procfile            # Paramètres de build Heroku (gunicorn/uvicorn)
```

### Le Déroulement ("Request Lifecycle" oTree)
1. **Dispatcher** : Tous les joueurs accèdent via un lien global. Ils sont dispatchés en groupe 1, 2 ou 3.
2. **Ordres Alternés** : Selon leur affiliation, la chaine d'expérimentation diffère (ceci évitant un biais d'apprentissage). Pour le GC1, il traverse "Risk Aversion" puis "Trust Game". Pour le GC2, il rencontre "Trust Game" en premier.
3. **Le GamePlay** : 
   - A l'intérieur de `trust_game`, les binômes interagissent.
   - Les appels asynchrones à l'API OpenAI sont lancés continuellement sur les messages échangés.
   - Les décisions d'investissement sont capturées, les paiements calculés (`set_payoffs`).
4. **Conclusion** : Présentation du solde monétaire final (`results`).

---

## Instructions de Démarrage (Local)

Ces instructions vous permettront de lancer le laboratoire localement pour la phase de test ou le développement.

### 1. Pré-requis 
- [Python](https://www.python.org/downloads/) 3.9 à 3.12 
- Un accès API chez [OpenAI](https://platform.openai.com/api-keys) configuré.

### 2. Cloner le Projet & Environnement virtuel
```bash
git clone https://github.com/votre-user/Trust-Game-AI.git
cd Trust-Game-AI

# MacOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows Powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Variables d'Environnement
Il faut créer un fichier `.env` à la racine du projet avec les informations ci-dessous.

Copiez un template en faisant :
```bash
cp .env.example .env # (ou créez le fichier manuellement)
```

**Structure requise du fichier `.env`** :
```env
# Authentification oTree
OTREE_ADMIN_PASSWORD=monmotdepassesecret
OTREE_AUTH_LEVEL=STUDY

# Connexion API OpenAI
OPENAI_API_KEY=sk-xxxxxxvotreclefxxxxxxx

# Configuration de l'Expérience (Variables Trust Game)
GPT_BEHAVIOR="Neutre"   # Valeurs possibles : Neutre / Stratège / Altruiste / Non
HAS_CHEAP_TALK=True     # Activer/Désactiver le chat inter-joueurs
DEBUG=True              # Mettre à False en production

# Dispatcher - Codes URL pour les groupes
IS_HEROKU=False
CODE_GROUPE_1=groupe1_link_access
CODE_GROUPE_2=groupe2_link_access
CODE_GROUPE_3=groupe3_link_access
```

### 5. Configurer la Base de Données
Initialisez l'architecture de la base de données oTree via cette commande:
```bash
otree resetdb
```
*(Confirmez avec `y` quand l'invite vous le demande)*

### 6. Lancement du Serveur de Développement
```bash
otree devserver
```

Une fois le serveur ouvert, accédez à [http://localhost:8000](http://localhost:8000). Connectez-vous avec l'identifiant `admin` et le mot de passe que vous avez configuré dans `OTREE_ADMIN_PASSWORD`. Vous y trouverez les interfaces des différentes "Sessions".

---

## Déploiement en Production (Heroku)

Si vous désirez administrer des sessions depuis un serveur web public pour envoyer l'expérience à distance, l'approche la plus courante pour oTree reste Heroku.

**1. S'inscrire sur Heroku et télécharger le CLI**
Générez compte via `heroku.com`. Connectez-vous depuis votre terminal local :
```bash
heroku login
```

**2. Créer l'application et les Add-ons nécessaires**
```bash
heroku create trust-game-ai
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
```

**3. Initialiser les configurations variables (Vars)**
Assignez manuellement chaque variable de votre `.env` à l'instance Heroku :
```bash
heroku config:set OPENAI_API_KEY=sk-xxxxxxvotreclefxxxxxxx
heroku config:set OTREE_PRODUCTION=1
heroku config:set OTREE_ADMIN_PASSWORD=supermotdepasse
heroku config:set OTREE_AUTH_LEVEL=STUDY
heroku config:set IS_HEROKU=True
heroku config:set GPT_BEHAVIOR="Votre_Comportement"
heroku config:set CODE_GROUPE_1=g1_code
heroku config:set CODE_GROUPE_2=g2_code
heroku config:set CODE_GROUPE_3=g3_code
```

**4. Pousser et Déployer le Code**
```bash
git push heroku main
```

**5. Initialiser la BD en ligne**
```bash
heroku run otree resetdb
```

Votre expérimentation est maintenant hébergée. Vous pouvez naviguer vers `<votre-app>.herokuapp.com`.

---

## Tests Automatisés

Le projet intègre une suite de tests unitaires utilisant **Pytest** pour garantir la fiabilité des calculs économiques et du comportement de l'IA.

### Utilité des tests
- **Fiabilité des gains** : Vérification mathématique des calculs de profits (payoffs) pour les modules de confiance et d'aversion au risque.
- **Validation du Chat IA** : S'assure que les messages sont correctement transmis et que les instructions de comportement GPT sont bien appliquées.
- **Non-régression** : Permet de vérifier instantanément qu'une modification du code n'a pas cassé de fonctionnalité existante.

### Exécuter les tests
Pour lancer la suite de tests (35 tests actuellement), utilisez la commande suivante à la racine du projet :

**Sur Windows (PowerShell) :**
```powershell
$env:PYTHONPATH="."; pytest tests/
```

**Sur macOS / Linux :**
```bash
PYTHONPATH=. pytest tests/
```

> [!TIP]
> Il est recommandé de lancer les tests après chaque modification majeure pour s'assurer de l'intégrité de la logique métier.

---

## Licence / Mention
Ce projet comporte une licence disponible dans `LICENSE`, et nécessite la citation du code open-source via la fiche `notice.txt` incluse à la racine. Produit par le programme Trust-Game-AI. 
