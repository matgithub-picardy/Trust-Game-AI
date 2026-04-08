# Trust Game  Spec de Refonte Complète
**Date** : 2026-04-08
**Auteur** : Stephane
**Approche retenue** : Refonte complète (back + front + UI/UX)
**Contexte** : Expérimentation économique comportementale en labo, participants rémunérés, expérimentateur sur place. **Interface optimisée en priorité pour smartphone** (mobile-first).

---

## 1. Objectifs

1. Corriger tous les bugs qui peuvent **fausser les données expérimentales**
2. Renforcer la **sécurité et la configuration** de l'application
3. Remettre en état la **logique backend** (questionnaire, randomisation GPT, risk_aversion)
4. Reconstruire l'**expérience participant** avec un design system moderne, professionnel et rassurant


---

## 2. Périmètre

| Domaine | Fichiers principaux |
|---|---|
| Corrections syntaxe templates | Tous les `.html` contenant `{{ if }}` / `{{ extends }}` |
| Sécurité & configuration | `.env`, `settings.py`, `dispatcher/__init__.py` |
| Logique backend | `risk_aversion/__init__.py`, `questionnaire/__init__.py`, `trust_game/__init__.py`, `results/__init__.py`, `intro/__init__.py` |
| Design system | `_static/style.css` + tous les templates participant |
| Hors périmètre | Tests (non requis), architecture oTree, WebSocket logic, modèle de données |

**Stack confirmée** : oTree 5.11.3 / Python / Jinja2 / JS vanilla / CSS custom variables. 

---

## 3. Corrections Bloquantes (Niveau 1)

### 3.1 Syntaxe templates invalide

**Problème** : Utilisation de `{{ if ... }}`, `{{ extends ... }}`, `{{ block ... }}` dans plusieurs templates. En Jinja2/oTree, seul `{% ... %}` est valide pour les balises logiques. Ces erreurs provoquent un rendu silencieusement incorrect (conditions ignorées).

**Fichiers à corriger** :
- `_templates/global/Page.html` — `{{ extends }}`, `{{ block }}`, `{{ endblock }}`
- `trust_game/templates/trust_game/GamePlay.html` — multiples `{{ if }}`
- `risk_aversion/templates/risk_aversion/InvestmentDecision1_4.html` — `{{ if }}`
- Tout autre template contenant ce pattern (scan systématique requis)

**Action** : Remplacer toutes les occurrences `{{ if }}` → `{% if %}`, `{{ extends }}` → `{% extends %}`, `{{ block }}` → `{% block %}`, `{{ endblock }}` → `{% endblock %}`.

### 3.2 Incohérence du show-up fee

**Problème** :
- `intro/__init__.py` : show-up fee = **€5**
- `results/__init__.py` : show-up fee défini comme **€10**

Un participant voit une somme à l'intro et une autre à la fin — biais expérimental + problème éthique.

**Action** : Extraire `SHOW_UP_FEE = 5` dans `settings.py` comme constante globale. L'importer dans `intro/__init__.py` et `results/__init__.py`.

### 3.3 Questionnaire désactivé

**Problème** : Les pages Q1–Q5 (mesure de perception de l'IA) sont commentées dans `page_sequence`. Seules 4 pages `TestInput` bidon s'exécutent.

**Action** : Décommenter Q1–Q5 et les réintégrer dans `page_sequence`. Supprimer les `TestInput` à leur tour.

### 3.4 Gestion d'erreur OpenAI absente

**Problème** : Si l'API OpenAI est indisponible, `chat_with_gpt()` plante silencieusement — bloque toute la session en labo.

**Action** : Entourer l'appel API d'un `try/except openai.OpenAIError` qui renvoie un message d'erreur lisible au participant via le mécanisme live :
```python
try:
    response = client.chat.completions.create(...)
except openai.OpenAIError:
    return {player.id_in_group: {"type": "gpt_error", "message": "Le service IA est temporairement indisponible."}}
```

**Comportement côté participant après `gpt_error`** : le JS reçoit `type === "gpt_error"` dans `liveRecv` et affiche le message d'erreur directement dans la colonne GPT du chat, à la place d'une bulle de réponse (style `.chat-bubble--error`). Le participant peut continuer : saisir des tokens, envoyer des messages P2P, et avancer. L'interface GPT ne se bloque pas — elle se fige visuellement (input désactivé, message d'info) mais le reste du jeu reste accessible.

---

## 4. Sécurité & Configuration (Niveau 2)

### 4.1 Clé API OpenAI exposée dans l'historique git

**Action externe** (côté utilisateur, hors code) : Régénérer la clé sur dashboard.openai.com et mettre à jour le `.env` local. Le `.env` reste dans `.gitignore`.

### 4.2 Secrets faibles dans `settings.py`

**Actions** :
- `SECRET_KEY` : remplacer par une clé forte générée via `python -c "import secrets; print(secrets.token_hex(32))"`
- La nouvelle valeur est placée dans `.env` sous `DJANGO_SECRET_KEY=<valeur>`, lue dans `settings.py` via `os.getenv('DJANGO_SECRET_KEY')`
- `OTREE_ADMIN_PASSWORD` : déjà dans `.env` sous `OTREE_ADMIN_PASSWORD`. Vérifier que `settings.py` le lit bien via `os.environ.get('OTREE_ADMIN_PASSWORD')` — si la valeur est encore hardcodée dans `settings.py`, la remplacer par cette lecture. Changer la valeur dans `.env` pour une valeur forte (≥ 12 caractères, alphanumérique).

### 4.3 URLs hardcodées dans le dispatcher

**Problème** : `LOCAL_URL` et `HEROKU_URL` sont en dur dans `dispatcher/__init__.py`.

**Action** : Les déplacer dans `.env` :
```env
LOCAL_URL=http://localhost:8000
HEROKU_URL=https://trust-game-ai-f55aa68b15d2.herokuapp.com
```
Les lire via `os.getenv('LOCAL_URL')` / `os.getenv('HEROKU_URL')`.

---

## 5. Logique Backend (Niveau 3)

### 5.1 `risk_aversion/__init__.py` — Refactoring des rustines

**Problème** : Code auto-décrit comme "rustines de dernière minute". La logique `create_index_map()` est fonctionnelle mais illisible.

**Actions** :
- Extraire `CONVERSION_RATE = 0.5` en constante nommée en tête de fichier
- Ajouter validation explicite côté back pour rejeter les valeurs `-1` (sentinelle) avant traitement
- Réécrire `final_profit()` avec des noms de variables explicites
- Ajouter des commentaires de section pour expliquer la logique d'index mapping

### 5.2 `trust_game/__init__.py` — Réactivation de `set_chat_options()`

**Problème** : La fonction de randomisation du comportement GPT par paire est commentée. Tous les participants reçoivent le même `GPT_BEHAVIOR` global — pas de randomisation inter-groupes.

**Action** : Décommenter et adapter `set_chat_options()`. La logique de base :
```python
index = ((player.id_in_group - 1) // 2) % len(BEHAVIORS)
```
assure qu'une paire (A+B) reçoit le même comportement, et que les comportements tournent entre paires.

**Point d'accroche oTree** : la fonction est appelée dans `creating_session` (au niveau du groupe), qui est le moment oTree où les paires sont formées et où les paramètres de session sont disponibles. C'est le seul endroit où `id_in_group` est accessible avant le début du jeu.

### 5.3 `results/__init__.py` — Consolidation des gains

**Action** : S'assurer que `tg_gain`, `ra_gain` et `show_up_fee` sont tous lus depuis les mêmes constantes centralisées. Aucune valeur monétaire hardcodée dans ce fichier.

---

## 6. Design System Participant (Niveau 4)

### 6.1 Direction artistique

**Concept** : *Institutional Trust* — interface d'une institution scientifique sérieuse, précise et rassurante. Pas froide, pas clinique.

| Élément | Valeur |
|---|---|
| Ton | Institutionnel raffiné |
| Police display | `DM Serif Display` (Google Fonts CDN + fallback local) |
| Police corps | `DM Sans` (Google Fonts CDN + fallback local) |
| Couleur primaire | `#0f2447` (bleu nuit) |
| Couleur accent | `#3b82f6` (bleu vif) |
| Fond | `#fafaf9` (blanc chaud) |
| Surface | `#ffffff` |
| Texte | `#1e293b` |
| Muted | `#64748b` |
| Succès | `#198754` |
| Warning | `#f59e0b` |
| Danger | `#ef4444` |

### 6.2 Architecture CSS — `_static/style.css`

Réécriture complète avec variables CSS :

```css
:root {
  --color-primary:  #0f2447;
  --color-accent:   #3b82f6;
  --color-success:  #198754;
  --color-warning:  #f59e0b;
  --color-danger:   #ef4444;
  --color-bg:       #fafaf9;
  --color-surface:  #ffffff;
  --color-border:   #e2e8f0;
  --color-text:     #1e293b;
  --color-muted:    #64748b;

  --font-display:   'DM Serif Display', Georgia, serif;
  --font-body:      'DM Sans', system-ui, sans-serif;

  /* Espacements — généreux sur mobile pour les touch targets */
  --space-xs: 4px;   --space-sm: 8px;
  --space-md: 16px;  --space-lg: 24px;
  --space-xl: 40px;

  /* Touch target minimum : 44px (Apple HIG / WCAG 2.5.5) */
  --touch-target: 44px;

  --radius-sm: 6px;  --radius-md: 12px;  --radius-lg: 20px;

  /* Breakpoints */
  --bp-tablet:  768px;
  --bp-desktop: 1024px;

  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 16px rgba(15,36,71,0.10);
  --shadow-lg: 0 8px 32px rgba(15,36,71,0.15);

  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
  --transition-slow: 400ms ease;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Approche mobile-first** : le CSS est écrit pour mobile en base, les media queries ajoutent des styles pour tablet (≥768px) puis desktop (≥1024px). Aucun style desktop-first.

**Composants CSS nommés** : `.experiment-card`, `.chat-bubble`, `.token-input`, `.progress-stepper`, `.skeleton`, `.dots-loader`, `.toast`.

**Note réseau en labo** : les machines de labo peuvent ne pas avoir accès à Internet. Les fichiers de police `DM Serif Display` et `DM Sans` doivent être téléchargés en `.woff2` et servis localement depuis `_static/fonts/`. Le `@font-face` dans `style.css` pointe vers ces fichiers locaux en priorité ; le lien Google Fonts CDN est conservé en secours uniquement.

### 6.3 Skeleton Loaders

oTree renvoie du HTML complet côté serveur (SSR) — il n'y a pas de phase de chargement async par défaut sur les pages statiques. Les skeletons s'appliquent donc uniquement aux **états d'attente réels** :

1. **WaitPage oTree** : pendant l'attente d'un autre participant (état async réel)
2. **Réponse GPT** : entre l'envoi du message et la réception via `liveRecv` (état async réel)
3. **Soumission de formulaire** : entre le clic "Suivant" et le chargement de la page suivante — le skeleton remplace le contenu de la page courante via JS au moment du `submit`

**Mécanisme JS** :
```javascript
// Au submit du formulaire : afficher le skeleton sur le conteneur principal
document.querySelector('form').addEventListener('submit', () => {
  document.querySelector('.page-content').classList.add('skeleton-active');
});
// Au DOMContentLoaded de la nouvelle page : le skeleton disparaît naturellement
// (le HTML serveur remplace tout le body)
```

Effet shimmer CSS pur :
```css
@keyframes shimmer {
  0%   { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}
.skeleton {
  background: linear-gradient(90deg, #e8edf2 25%, #f5f7fa 50%, #e8edf2 75%);
  background-size: 1000px 100%;
  animation: shimmer 1.8s infinite ease-in-out;
  border-radius: var(--radius-sm);
}
```

Déclinaisons :
- **WaitPage** → skeleton centré avec 3 blocs de hauteurs variées
- **Réponse GPT en attente** → bulle skeleton dans la colonne GPT (remplacée par la vraie réponse à l'arrivée)
- **Transition de page** → skeleton sur `.page-content` pendant ~300ms entre submit et chargement

### 6.4 Indicateurs de chargement — Trois points animés

Remplacent tous les spinners :

```css
.dots-loader span {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: bounce 1.2s infinite;
  animation-delay: calc(var(--i) * 0.2s);
}
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40%           { transform: translateY(-6px); opacity: 1; }
}
```

**Utilisations** :
- Bulle "GPT thinking" dans le chat (style iMessage)
- État de chargement des boutons au clic (texte → `● ● ●`, bouton désactivé)
- WaitPage oTree

### 6.5 Timer narratif

| Temps restant | Couleur | Message | Animation |
|---|---|---|---|
| > 120s | `#3b82f6` bleu | "Temps de discussion" | Aucune |
| 60–120s | `#f59e0b` ambre | "Bientôt terminé" | Pulsation lente |
| < 60s | `#ef4444` rouge | "Dernière minute" | Pulsation rapide |
| 0s | `#64748b` gris | "Discussion terminée" | Aucune |

Transition fluide : `transition: color 1s, border-color 1s`.

### 6.6 Chat Interface — Refonte

**Approche mobile-first** : le layout de base (< 768px) est en **onglets** — un onglet "Discussion" et un onglet "Assistant IA". Sur écrans ≥ 1024px, bascule en deux colonnes côte à côte.

**Mobile (défaut, < 1024px) — Onglets :**
```
┌─────────────────────────────────┐
│ [Joueur A]      [Timer 4:32 ●] │
├────────────┬────────────────────┤
│ Discussion │  Assistant IA      │  ← onglets actifs
├────────────┴────────────────────┤
│                                 │
│  [Bulles du chat actif]         │
│  [● ● ● thinking]               │
│                                 │
├─────────────────────────────────┤
│ [Input ──────────── Envoyer]   │
└─────────────────────────────────┘
```

**Desktop (≥ 1024px) — Deux colonnes :**
```
┌──────────────────────────────────────────────┐
│  [Joueur A]              [Timer: 4:32 ●●]   │
├───────────────────┬──────────────────────────┤
│  Discussion       │  Assistant IA             │
│  [Bulles]         │  [Bulles]                 │
│                   │  [● ● ● thinking]         │
├───────────────────┤                           │
│ [Input  Envoyer]  │ [Input  Envoyer]          │
└───────────────────┴──────────────────────────┘
```

- **Badge rôle** : `Joueur A` / `Joueur B` toujours visible en haut
- **Timer** : affiché en permanence, compact sur mobile (icône + chiffre), étendu sur desktop
- **Bulles** : slide-in depuis le bas (`translateY(12px)→0` + `opacity: 0→1`, 200ms)
- **Indicateur typing** : 3 points animés, visible seulement en chat P2P
- **Erreur GPT** : message inline dans la zone GPT active, non bloquant
- **Input dédié par zone** : chaque zone (P2P et GPT) a son propre champ de saisie et son propre bouton "Envoyer". L'input P2P appelle `sendChatMessageCheapTalk()`, l'input GPT appelle `sendChatMessageGPT()`.
- **Touch targets** : bouton "Envoyer" ≥ 44px de hauteur, champ de saisie ≥ 44px
- **Exception max-width** : GamePlay utilise `width: 100%` avec `padding: 0 var(--space-md)` sur mobile, et `max-width: 960px` sur desktop — aucune contrainte 720px ici.

### 6.7 Formulaire Token — Validation temps réel

- Slider horizontal synchronisé avec champ numérique
- Slider ≥ 44px de hauteur de zone tactile sur mobile (padding autour de la piste)
- Aperçu dynamique : *"Vous envoyez 6 → l'autre joueur recevra 18 jetons"*
- Animation aperçu au changement : `scale(1.05)→1` en 150ms
- Validation : animation `shake` si valeur hors plage, message inline (pas d'alerte modale)
- Bouton "Envoyer" : pleine largeur sur mobile (`width: 100%`), auto sur desktop

```css
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25%       { transform: translateX(-6px); }
  75%       { transform: translateX(6px); }
}
```

### 6.8 Toasts — Feedback non-bloquant

Remplacent toutes les alertes statiques. Slide-in depuis le haut, disparaissent après 4s :

```
┌─────────────────────────────┐
│ ✓  Décision enregistrée    │
└─────────────────────────────┘
```

Types : succès (vert), info (bleu), erreur (rouge), neutre (gris).

### 6.9 Barre de progression narrative

**Mobile** : version compacte — barre de progression linéaire + label texte. Les noms des étapes sont masqués (trop larges sur petit écran) et remplacés par un texte centré sous la barre :

```
[━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━]
      Étape 3 sur 5 — Risque
```

**Desktop (≥ 768px)** : version complète avec points nommés :
```
● ──────── ● ──────── ● ──────── ○ ──────── ○
Accueil  Questionnaire  Risque  Jeu  Résultats
                          ↑ vous êtes ici
```

- Points passés : remplis couleur primaire
- Point actuel : pulsation légère (`@keyframes pulse`)
- Points futurs : `var(--color-border)` gris clair
- Sur mobile : la barre est une `<progress>` native stylisée ou un `<div>` avec `width: calc(X/Y * 100%)`

**Injection de la variable `current_step`** : chaque page de chaque module oTree expose `current_step` via `vars_for_template()`. Exemple dans `trust_game/__init__.py` :
```python
class GamePlay(Page):
    def vars_for_template(player):
        return {"current_step": 4, "total_steps": 5, "step_label": "Jeu de confiance"}
```
Le template `Page.html` global lit `{{ current_step }}`, `{{ total_steps }}`, `{{ step_label }}` pour construire la barre. Si une page ne définit pas `vars_for_template`, la barre n'est pas affichée (fallback : masquée via `{% if current_step %}`).

**Coordination avec `Page.html`** : ce fichier est modifié en Phase 1 (correction syntaxe) ET en Phase 4 (ajout barre de progression). Pour éviter les conflits, la Phase 1 corrige uniquement la syntaxe `{% %}` sans toucher la structure. La Phase 4 ajoute ensuite le bloc de barre de progression.

### 6.10 WaitPage redessinée

```
┌─────────────────────────────────────────────┐
│                                             │
│     En attente de l'autre participant       │
│                                             │
│              ● ● ●                          │
│                                             │
│   "L'expérimentateur est disponible        │
│    si vous avez besoin d'aide."             │
│                                             │
└─────────────────────────────────────────────┘
```

Fond avec motif géométrique subtil (`radial-gradient`) pour éviter le vide visuel.

### 6.11 Page Résultats — Reveal progressif

1. Skeleton → contenu (400ms)
2. Chaque ligne slide-in avec délai échelonné (`animation-delay: 0.1s, 0.2s...`)
3. Montant final en euros : pulse unique pour attirer l'attention

**Mécanisme JS d'activation** : la page Results est SSR (contenu disponible immédiatement). Le skeleton est simulé via une classe CSS ajoutée au body au chargement, retirée après un délai court :
```javascript
// results.js — DOMContentLoaded
document.body.classList.add('results-loading');
setTimeout(() => {
  document.body.classList.remove('results-loading');
  document.querySelectorAll('.result-row').forEach((row, i) => {
    row.style.animationDelay = `${i * 0.1}s`;
    row.classList.add('slide-in');
  });
}, 400);
```
La classe `.results-loading` masque les `.result-row` via CSS et affiche des blocs `.skeleton` à leur place.

### 6.12 Layout universel — Mobile-first

Toutes les pages participant partagent le même conteneur. **Base mobile** :

```
┌─────────────────────────┐
│ [Titre]     [Étape X/Y] │  ← header fixe, compact
│ [━━━●━━━━━━━━━━━━━○━━━] │  ← barre de progression
├─────────────────────────┤
│                         │
│   [Contenu full-width]  │  ← padding 16px h., scroll
│   [avec padding 16px]   │
│                         │
├─────────────────────────┤
│  [ Suivant →          ] │  ← bouton full-width, 52px
└─────────────────────────┘
```

**Sur desktop (≥ 768px)** :
```
┌──────────────────────────────────────────┐
│  [Titre expérience]       [Étape X/Y]   │
│  [━━━━━●━━━━━━━━━━━━━━━━━━━━━━━○━━━━━]  │
├──────────────────────────────────────────┤
│                                          │
│     [Contenu centré, max-width: 640px]   │
│                                          │
├──────────────────────────────────────────┤
│              [ Suivant → ]               │
└──────────────────────────────────────────┘
```

**Règles mobiles** :
- Bouton "Suivant" : `width: 100%`, `min-height: 52px`, texte `1rem`
- Tous les boutons et inputs : `min-height: var(--touch-target)` (44px)
- Padding horizontal : `var(--space-md)` (16px) sur mobile
- Font-size corps : `1rem` minimum (jamais en dessous de 16px → pas de zoom forcé iOS)
- Pas de `:hover` seul sans fallback tactile — toujours un `:active` ou `:focus` aussi

---

## 7. Décisions Techniques Confirmées

| Question | Décision | Raison |
|---|---|---|
| React ? | Non | Incompatible oTree (SSR + liveSend) |
| Tailwind ? | Non | Conflit Bootstrap, build step inutile |
| Bootstrap 4 ? | Réduit | Garder la grille, écraser le reste |
| JS vanilla ? | Oui, amélioré | Natif oTree live system |
| CSS variables ? | Oui | Design system léger et maintenable |
| Google Fonts ? | Oui (DM Serif Display + DM Sans) | Servi localement en `.woff2` (`_static/fonts/`), CDN en fallback uniquement |
| Responsive ? | Mobile-first | Smartphone = cible principale, desktop en media query |
| Touch targets ? | 44px minimum | Apple HIG + WCAG 2.5.5, évite les erreurs de tap |

---

## 8. Ordre d'Implémentation

```
Phase 1 — Corrections bloquantes
  1.1  Scan et correction syntaxe templates ({{ → {%)
  1.2  Centralisation SHOW_UP_FEE dans settings.py
  1.3  Réactivation questionnaire Q1–Q5
  1.4  Try/except sur appels OpenAI

Phase 2 — Sécurité & configuration
  2.1  Déplacement SECRET_KEY dans .env
  2.2  Déplacement URLs dispatcher dans .env
  2.3  Vérification OTREE_ADMIN_PASSWORD dans .env

Phase 3 — Logique backend
  3.1  Refactoring risk_aversion (constantes, validation -1, lisibilité)
  3.2  Réactivation set_chat_options() dans trust_game
  3.3  Consolidation gains dans results

Phase 4 — Design system
  4.1  Layout universel dans Page.html (structure de base, max-width 720px sauf GamePlay, header/footer)
  4.2  Réécriture _static/style.css (variables CSS, composants, police locale woff2)
  4.3  Ajout fonts locales dans _static/fonts/ + @font-face dans style.css
  4.4  Barre de progression dans Page.html (vars_for_template dans chaque module)
  4.5  Skeleton loaders (WaitPage, GPT thinking, transition de page)
  4.6  Dots loader (remplacement spinners)
  4.7  Toast système
  4.8  Timer narratif (GamePlay)
  4.9  Chat interface refonte (GamePlay — exception max-width : pleine largeur disponible)
  4.10 Token form (slider + preview + shake)
  4.11 WaitPage redessinée
  4.12 Results reveal progressif
  4.13 Application du layout universel à tous les templates restants (questionnaire, risk_aversion, intro, results)
```

---

## 9. Ce qui reste inchangé

- Architecture oTree (modules, sessions, page_sequence globale)
- Logique WebSocket `liveSend` / `liveRecv` (fonctionnelle)
- Routing dispatcher (logique modulo 3)
- Modèle de données Player/Group (aucun field ajouté)
- Procfile Heroku
- Tout code commenté (conservé tel quel, sauf décision explicite)
