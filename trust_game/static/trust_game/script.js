/**
 * Gère la logique client pour le Trust Game.
 * Gère le minuteur, le chat (P2P et ChatGPT), et les transactions de jetons.
 */

/* ── Gestion du minuteur ── */

/**
 * Met à jour l'affichage visuel du minuteur de discussion.
 * Gère les classes de couleur selon l'urgence (warning, urgent, done).
 */
function updateChatTimer() {
    updateTimeRemaining();
    const el = document.getElementById("time");
    const remaining = document.getElementById("time_remaining");
    const label = document.getElementById("timer_label");
    if (!el || !remaining) return;

    remaining.textContent = timeRemaining;

    el.classList.remove('chat-timer--warning', 'chat-timer--urgent', 'chat-timer--done');

    if (timeRemaining <= 0) {
        clearInterval(chatTimer);
        el.classList.add('chat-timer--done');
        if (label) label.textContent = '— Discussion terminée';
        disableChat(true);
    } else if (timeRemaining < 60) {
        el.classList.add('chat-timer--urgent');
        if (label) label.textContent = '— Dernière minute';
    } else if (timeRemaining <= 120) {
        el.classList.add('chat-timer--warning');
        if (label) label.textContent = '— Bientôt terminé';
    } else {
        if (label) label.textContent = '';
    }
}

/**
 * Calcule le temps restant en secondes à partir du timestamp d'expiration.
 */
function updateTimeRemaining() {
    const now = Date.now() / 1000;
    timeRemaining = Math.max(parseInt(expireTime - now), 0);
}

/* ── Contrôle de l'interface de chat ── */

/**
 * Désactive les interfaces de chat (P2P et GPT) à la fin du temps ou après une décision.
 * @param {boolean} is_expired - Indique si la désactivation est due à l'expiration du temps.
 */
function disableChat(is_expired) {
    const placeholder = is_expired ? "Temps écoulé" : "Joueur A a pris sa décision";
    if (has_cheap_talk) setDisabled(inputCheapTalk, buttonCheapTalk, placeholder);
    if (has_chat_gpt) setDisabled(inputGPT, buttonGPT, placeholder);
}

/**
 * Désactive un couple input/bouton spécifique.
 * @param {HTMLElement} input - Le champ de saisie.
 * @param {HTMLElement} button - Le bouton d'envoi.
 * @param {string} placeholder - Le nouveau texte du placeholder.
 */
function setDisabled(input, button, placeholder) {
    if (!input || !button) return;
    input.disabled = true;
    button.disabled = true;
    input.placeholder = placeholder;
}

/* ── Gestion de l'affichage (Bulles de chat) ── */

/**
 * Ajoute une bulle de message dans le conteneur spécifié.
 * @param {string} containerId - ID du conteneur HTML.
 * @param {string} text - Contenu du message.
 * @param {string} bubbleClass - Classe CSS pour le style de la bulle (ex: chat-bubble--self).
 */
function appendBubble(containerId, text, bubbleClass) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${bubbleClass}`;
    bubble.innerHTML = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

/* ── Logique d'envoi des messages ── */

/**
 * Prépare les données pour un message 'Cheap Talk' (P2P).
 * @param {string} message - Le contenu du message.
 * @returns {Object} - Données formatées pour liveSend.
 */
function sendChatMessageCheapTalk(message) {
    const playerPrefix = roleIsPlayerA ? "Joueur A" : "Joueur B";
    if (isTyping) doneTyping();
    return { message: message, player_type: playerPrefix };
}

/**
 * Prépare les données pour un message envoyé à l'IA (GPT).
 * @param {string} message - Le contenu du message.
 * @param {string} playerPrefix - Préfixe du joueur (ex: "Vous: ").
 * @returns {Object} - Données formatées pour liveSend.
 */
function sendChatMessageGPT(message, playerPrefix) {
    appendBubble('chatbox-gpt', playerPrefix + message, 'chat-bubble--self');
    const thinking = document.getElementById('gpt-thinking');
    if (thinking) thinking.style.display = '';
    return { message: message, is_chat_gpt: true };
}

/**
 * Fonction maîtresse d'envoi de message (déclenchée par l'UI).
 * @param {HTMLElement} input - Le champ input source.
 * @param {string|null} playerPrefix - Préfixe si c'est un chat GPT.
 */
function sendChatMessage(input, playerPrefix = null) {
    const message = input.value.trim();
    if (!message) return;
    let dataToSend;
    if (playerPrefix == null) dataToSend = sendChatMessageCheapTalk(message);
    else dataToSend = sendChatMessageGPT(message, playerPrefix);
    input.value = "";
    input.focus();
    liveSend(dataToSend);
}

/**
 * Signale au partenaire que l'utilisateur a fini d'écrire.
 */
function doneTyping() {
    isTyping = false;
    liveSend({ typing_status: false });
    clearTimeout(typingTimer);
}

/* ── Synchronisation et État du jeu ── */

/**
 * Restaure l'état de l'interface à partir des données sauvegardées (rechargement de page).
 */
function refreshFromSavedData() {
    const amount_sent = js_vars.amount_sent;
    const amount_sent_back = js_vars.amount_sent_back;

    if (amount_sent != null) {
        disableChat(false);
        liveRecv({ status: "sent", amount_sent: amount_sent });
        liveRecv({ status: "received", amount_sent: amount_sent, tripled_amount: amount_sent * js_vars.multiplier });
    }
    if (amount_sent_back != null) {
        liveRecv({
            status: "complete", can_proceed: true,
            amount_sent: amount_sent, amount_sent_back: amount_sent_back,
            tripled_amount: amount_sent * js_vars.multiplier
        });
    }
}

/* ── Gestion des Transactions ── */

/**
 * Envoie le montant de jetons choisi par le Joueur A.
 * Valide la saisie et met à jour l'UI locale avant l'envoi.
 */
function sendTokens() {
    const amountInput = document.getElementById("amount_input");
    const errorEl = document.getElementById("amount_error");
    const amount = parseInt(amountInput.value);

    if (isNaN(amount) || amount < 0 || amount > js_vars.endowment) {
        amountInput.classList.add("shake");
        if (errorEl) errorEl.style.display = 'block';
        setTimeout(() => amountInput.classList.remove("shake"), 300);
        return;
    }
    if (errorEl) errorEl.style.display = 'none';
    liveSend({ amount_sent: amount, time_remaining: timeRemaining });
    document.getElementById("send_button").disabled = true;
    document.getElementById("sent_amount").textContent = amount;
    document.getElementById("waiting_message").classList.remove("d-none");
}

/**
 * Envoie le montant de jetons renvoyé par le Joueur B.
 * Valide la saisie par rapport au montant triplé reçu.
 */
function sendTokensBack() {
    const amountBackInput = document.getElementById("amount_back_input");
    const errorEl = document.getElementById("amount_back_error");
    const maxAmount = parseInt(document.getElementById("tripled_amount_1").textContent);
    const amountBack = parseInt(amountBackInput.value);

    if (isNaN(amountBack) || amountBack < 0 || amountBack > maxAmount) {
        amountBackInput.classList.add("shake");
        if (errorEl) errorEl.style.display = 'block';
        setTimeout(() => amountBackInput.classList.remove("shake"), 300);
        return;
    }
    if (errorEl) errorEl.style.display = 'none';
    liveSend({ amount_sent_back: amountBack });
    document.getElementById("send_back_button").disabled = true;
}

/* ── Affichage des Résultats ── */

/**
 * Affiche le bilan financier pour le Joueur A.
 * @param {Object} data - Résultats de la transaction.
 */
function resultsPlayerA(data) {
    const resultsDiv = document.getElementById("final_results_content");
    const { amount_sent: sent, amount_sent_back: back } = data;
    const final = js_vars.endowment - sent + back;
    resultsDiv.innerHTML = `
    <p>Vous avez envoyé <strong>${sent} jeton(s)</strong> au Joueur B.</p>
    <p>Le Joueur B vous a renvoyé <strong>${back} jeton(s)</strong>.</p>
    <p><strong>Votre solde final : ${final} jetons</strong></p>`;
}

/**
 * Affiche le bilan financier pour le Joueur B.
 * @param {Object} data - Résultats de la transaction.
 */
function resultsPlayerB(data) {
    const resultsDiv = document.getElementById("final_results_content");
    const { amount_sent: received, tripled_amount: tripled, amount_sent_back: back } = data;
    const final = tripled - back;
    resultsDiv.innerHTML = `
    <p>Vous avez reçu <strong>${tripled} jeton(s)</strong> (${received} × ${js_vars.multiplier}).</p>
    <p>Vous avez renvoyé <strong>${back} jeton(s)</strong> au Joueur A.</p>
    <p><strong>Votre solde final : ${final} jetons</strong></p>`;
}

/**
 * Met à jour le bloc de résultats selon le rôle du joueur.
 */
function updateFinalResults(data) {
    if (roleIsPlayerA) resultsPlayerA(data);
    else resultsPlayerB(data);
}

/* ── Handlers de Réception (liveRecv) ── */

/**
 * Affiche la réponse générée par l'IA (GPT).
 */
function handleChatGPTReply(data) {
    const thinking = document.getElementById('gpt-thinking');
    if (thinking) thinking.style.display = 'none';
    appendBubble('chatbox-gpt', data.bot_prefix + data.reply, 'chat-bubble--gpt');
}

/**
 * Gère les erreurs techniques lors de la communication avec l'API GPT.
 */
function handleGPTError(data) {
    const thinking = document.getElementById('gpt-thinking');
    if (thinking) thinking.style.display = 'none';
    appendBubble('chatbox-gpt', data.message, 'chat-bubble--error');
    setDisabled(inputGPT, buttonGPT, "Service IA indisponible");
}

/**
 * Ajoute un nouveau message texte dans l'historique de chat.
 * Classe self si l'expéditeur est le joueur courant, other sinon.
 */
function handleNewMessage(data) {
    const chatHistory = document.getElementById("chat_history");
    if (!chatHistory) return;
    const isSelf = data.sender_id === js_vars.id_in_group;
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble ' + (isSelf ? 'chat-bubble--self' : 'chat-bubble--other');
    bubble.dataset.senderId = data.sender_id;
    bubble.innerHTML = data.new_message;
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    // si c'est un message reçu, envoyer un accusé de lecture
    if (!isSelf) {
        liveSend({ read_receipt: true });
    }
}

/**
 * Affiche l'accusé de lecture "Lu ✓" sur le dernier message envoyé.
 */
function handleReadReceipt(data) {
    const chatHistory = document.getElementById("chat_history");
    if (!chatHistory) return;
    // trouver le dernier message envoyé par le joueur courant
    const selfBubbles = chatHistory.querySelectorAll('.chat-bubble--self');
    if (!selfBubbles.length) return;
    const last = selfBubbles[selfBubbles.length - 1];
    // supprimer les anciens accusés
    chatHistory.querySelectorAll('.read-receipt').forEach(el => el.remove());
    const receipt = document.createElement('span');
    receipt.className = 'read-receipt';
    receipt.textContent = 'Lu ✓';
    last.appendChild(receipt);
}

/**
 * Affiche ou masque l'indicateur "Le partenaire écrit...".
 */
function handleTypingIndicator(data) {
    const typingIndicator = document.getElementById("typing_indicator");
    if (!typingIndicator) return;
    if (data.other_player_typing) typingIndicator.classList.remove("d-none");
    else typingIndicator.classList.add("d-none");
}

/**
 * Confirme l'envoi réussi pour le Joueur A.
 */
function handleSentStatus(data) {
    disableChat(false);
    document.getElementById("send_button").disabled = true;
    document.getElementById("sent_amount").textContent = data.amount_sent;
    document.getElementById("waiting_message").classList.remove("d-none");
}

/**
 * Gère la réception de jetons pour le Joueur B et active l'interface de renvoi.
 */
function handleReceivedStatus(data) {
    disableChat(false);
    document.getElementById("waiting_for_A").classList.add("d-none");
    document.getElementById("received_amount_display").classList.remove("d-none");
    document.getElementById("received_amount").textContent = data.amount_sent;
    document.getElementById("tripled_amount_1").textContent = data.tripled_amount;
    document.getElementById("tripled_amount_2").textContent = data.tripled_amount;
    document.getElementById("amount_back_input").max = data.tripled_amount;
    if (typeof setupSliderB === 'function') setupSliderB(data.tripled_amount);
}

/**
 * Gère la fin du jeu et l'affichage des résultats finaux.
 */
function handleCompleteStatus(data) {
    canProceed = data.can_proceed;
    document.getElementById("game_results").classList.remove("d-none");
    updateFinalResults(data);
    if (canProceed) document.getElementById("proceed_button").disabled = false;
}

/**
 * Point d'entrée principal pour tous les messages reçus via liveSend (Canaux oTree).
 * Oriente les données vers les handlers spécifiques.
 */
function liveRecv(data) {
    if (data.type === "gpt_error") handleGPTError(data);
    if (data.is_chat_gpt) handleChatGPTReply(data);
    if (data.new_message) handleNewMessage(data);
    if (data.read_by) handleReadReceipt(data);
    if (data.hasOwnProperty("other_player_typing")) handleTypingIndicator(data);
    if (data.status === "sent" && roleIsPlayerA) handleSentStatus(data);
    if (data.status === "received" && !roleIsPlayerA) handleReceivedStatus(data);
    if (data.status === "sent" || data.status === "received") {
        const timeEl = document.getElementById("time");
        if (timeEl) timeEl.classList.add("d-none");
    }
    if (data.status === "complete") handleCompleteStatus(data);
}
