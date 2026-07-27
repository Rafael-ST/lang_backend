(function () {
  const STORAGE_KEY = "langExerciseBuilder";
  const LOGIN_URL = "/exercise-builder/login/";

  const state = {
    cards: [],
    exerciseSets: [],
    exerciseTypes: [],
    filteredCards: [],
    filteredSets: [],
  };

  const elements = {
    page: document.querySelector("main[data-api-base-url]"),
    apiBaseUrl: document.querySelector("#apiBaseUrl"),
    currentUser: document.querySelector("#currentUser"),
    logoutButton: document.querySelector("#logoutButton"),
    saveConnectionButton: document.querySelector("#saveConnectionButton"),
    reloadDataButton: document.querySelector("#reloadDataButton"),
    connectionStatus: document.querySelector("#connectionStatus"),
    cardSearch: document.querySelector("#cardSearch"),
    setSearch: document.querySelector("#setSearch"),
    form: document.querySelector("#exerciseForm"),
    alertBox: document.querySelector("#alertBox"),
    exerciseSet: document.querySelector("#exerciseSet"),
    card: document.querySelector("#card"),
    exerciseType: document.querySelector("#exerciseType"),
    exerciseSkill: document.querySelector("#exerciseSkill"),
    order: document.querySelector("#order"),
    difficulty: document.querySelector("#difficulty"),
    isActive: document.querySelector("#isActive"),
    promptText: document.querySelector("#promptText"),
    audioFile: document.querySelector("#audioFile"),
    currentAudio: document.querySelector("#currentAudio"),
    imageFile: document.querySelector("#imageFile"),
    currentImage: document.querySelector("#currentImage"),
    translation: document.querySelector("#translation"),
    expectedTranscript: document.querySelector("#expectedTranscript"),
    acceptedAnswers: document.querySelector("#acceptedAnswers"),
    clozeTemplate: document.querySelector("#clozeTemplate"),
    clozeAnswer: document.querySelector("#clozeAnswer"),
    optionsSection: document.querySelector("#optionsSection"),
    optionsTitle: document.querySelector("#optionsTitle"),
    optionsList: document.querySelector("#optionsList"),
    addOptionButton: document.querySelector("#addOptionButton"),
    jsonPreview: document.querySelector("#jsonPreview"),
    copyJsonButton: document.querySelector("#copyJsonButton"),
    cardSummary: document.querySelector("#cardSummary"),
  };

  init();

  function init() {
    state.exerciseTypes = Array.from(elements.exerciseType.options).map(
      (option) => ({
        label: option.textContent,
        value: option.value,
      })
    );
    loadConnection();
    if (!readStorage().accessToken) {
      window.location.replace(LOGIN_URL);
      return;
    }
    bindEvents();
    filterExerciseTypesBySkill();
    addDefaultOptionRows();
    updateTypeFields();
    updatePreview();

    loadApiData();
  }

  function bindEvents() {
    elements.saveConnectionButton.addEventListener("click", saveConnectionAndLoad);
    elements.logoutButton.addEventListener("click", logout);
    elements.reloadDataButton.addEventListener("click", loadApiData);
    elements.cardSearch.addEventListener("input", renderCards);
    elements.setSearch.addEventListener("input", renderExerciseSets);
    elements.exerciseType.addEventListener("change", handleTypeChange);
    elements.exerciseSkill.addEventListener("change", handleSkillChange);
    elements.card.addEventListener("change", hydrateFromSelectedCard);
    elements.audioFile.addEventListener("change", renderSelectedAudioFile);
    elements.imageFile.addEventListener("change", renderSelectedImageFile);
    elements.addOptionButton.addEventListener("click", () => addOptionRow());
    elements.copyJsonButton.addEventListener("click", copyJson);
    elements.form.addEventListener("submit", submitExercise);

    elements.form.querySelectorAll("input, select, textarea").forEach((field) => {
      field.addEventListener("input", updatePreview);
      field.addEventListener("change", updatePreview);
    });
  }

  function loadConnection() {
    const saved = readStorage();
    elements.apiBaseUrl.value = saved.apiBaseUrl || elements.page.dataset.apiBaseUrl || "/api/v1";
    elements.currentUser.textContent = saved.usuario?.username || "";
  }

  function readStorage() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    } catch {
      return {};
    }
  }

  function saveConnectionAndLoad() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        apiBaseUrl: getApiBaseUrl(),
        accessToken: readStorage().accessToken,
        usuario: readStorage().usuario,
      })
    );
    loadApiData();
  }

  async function loadApiData() {
    setLoading(true);
    hideAlert();

    try {
      const [exerciseSets, cards] = await Promise.all([
        apiRequest("/exercise-sets/"),
        apiRequest("/cards/"),
      ]);

      state.exerciseSets = normalizeList(exerciseSets);
      state.cards = normalizeList(cards);
      renderExerciseSets();
      renderCards();
      refreshOptionCardSelects();
      setConnectionStatus("Conectado", "success");
    } catch (error) {
      setConnectionStatus("Erro", "danger");
      showAlert(error.message, "danger");
    } finally {
      setLoading(false);
    }
  }

  async function apiRequest(path, options = {}) {
    const baseUrl = getApiBaseUrl();
    const { authRetry = false, ...fetchOptions } = options;

    if (!baseUrl) {
      throw new Error("Informe a URL da API.");
    }

    const isFormData = fetchOptions.body instanceof FormData;
    const headers = {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(fetchOptions.headers || {}),
    };

    const token = readStorage().accessToken;

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${baseUrl}${path}`, {
      ...fetchOptions,
      headers,
      credentials: "include",
    });
    const data = await response.json().catch(() => null);

    if (response.status === 401) {
      if (authRetry) {
        logout();
        throw new Error("Sua sessao expirou. Entre novamente.");
      }
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return apiRequest(path, { ...fetchOptions, authRetry: true });
      }
      logout();
      throw new Error("Sua sessao expirou. Entre novamente.");
    }

    if (!response.ok) {
      throw new Error(getApiErrorMessage(data));
    }

    return data;
  }

  async function refreshAccessToken() {
    const response = await fetch(`${getApiBaseUrl()}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: "{}",
    });
    if (!response.ok) return false;
    const data = await response.json();
    const saved = readStorage();
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...saved, accessToken: data.access }));
    return true;
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    window.location.replace(LOGIN_URL);
  }

  function getApiBaseUrl() {
    return elements.apiBaseUrl.value.trim().replace(/\/+$/, "");
  }

  function normalizeList(data) {
    if (Array.isArray(data)) {
      return data;
    }

    if (Array.isArray(data?.results)) {
      return data.results;
    }

    return [];
  }

  function renderExerciseSets() {
    const selectedValue = elements.exerciseSet.value;
    const search = normalizeText(elements.setSearch.value);
    state.filteredSets = state.exerciseSets.filter((item) =>
      normalizeText(`${item.title || ""} ${item.description || ""} ${item.sublevel_detail?.nome || ""}`).includes(search)
    );

    elements.exerciseSet.innerHTML = [
      '<option value="">Selecione...</option>',
      ...state.filteredSets.map((item) => {
        const label = [item.title, item.sublevel_detail?.nome].filter(Boolean).join(" - ");
        return `<option value="${escapeHtml(item.id)}">${escapeHtml(label || item.id)}</option>`;
      }),
    ].join("");
    elements.exerciseSet.value = selectedValue;
    updatePreview();
  }

  function renderCards() {
    const selectedValue = elements.card.value;
    const search = normalizeText(elements.cardSearch.value);
    state.filteredCards = state.cards.filter((item) =>
      normalizeText(`${item.english_name || ""} ${item.international_name || ""}`).includes(search)
    );

    elements.card.innerHTML = [
      '<option value="">Selecione...</option>',
      ...state.filteredCards.map((item) => {
        const label = [item.english_name, item.international_name].filter(Boolean).join(" - ");
        return `<option value="${escapeHtml(item.id)}">${escapeHtml(label || item.id)}</option>`;
      }),
    ].join("");
    elements.card.value = selectedValue;

    elements.cardSummary.innerHTML = state.filteredCards
      .slice(0, 12)
      .map(
        (item) => `
          <div class="summary-item">
            <strong>${escapeHtml(item.english_name || item.id)}</strong>
            <span>${escapeHtml(item.international_name || "Sem traducao")}</span>
          </div>
        `
      )
      .join("");
    updatePreview();
  }

  function handleTypeChange() {
    elements.exerciseSkill.value = getDefaultSkill(
      elements.exerciseType.value
    );
    updateTypeFields();
    hydrateFromSelectedCard();
  }

  function handleSkillChange() {
    filterExerciseTypesBySkill();
    updateTypeFields();
    hydrateFromSelectedCard();
  }

  function filterExerciseTypesBySkill() {
    const selectedSkill = elements.exerciseSkill.value;
    const currentType = elements.exerciseType.value;
    const availableTypes = state.exerciseTypes.filter(
      (exerciseType) =>
        getDefaultSkill(exerciseType.value) === selectedSkill
    );

    elements.exerciseType.innerHTML = availableTypes
      .map(
        (exerciseType) =>
          `<option value="${escapeAttribute(exerciseType.value)}">${escapeHtml(exerciseType.label)}</option>`
      )
      .join("");

    if (availableTypes.some((exerciseType) => exerciseType.value === currentType)) {
      elements.exerciseType.value = currentType;
    }
  }

  function getDefaultSkill(type) {
    if (["speak_written_text", "speak_english_from_translation"].includes(type)) {
      return "speaking";
    }

    if ([
      "just_audio",
      "multiple_choice_audio_english",
      "write_translation_from_audio",
      "complete_audio_text",
      "image_presentation",
      "audio_multiple_choice_images",
    ].includes(type)) {
      return "listening";
    }

    return "reading";
  }

  function updateTypeFields() {
    const type = elements.exerciseType.value;
    const isMultipleChoice = ["multiple_choice_translation", "multiple_choice_audio_english", "image_multiple_choice_english", "audio_multiple_choice_images"].includes(type);
    const isMatchingPairs = type === "matching_pairs";
    const isCompleteAudioText = type === "complete_audio_text";
    toggle(".prompt-text-field", !["write_translation_from_audio", "multiple_choice_audio_english", "matching_pairs", "complete_audio_text", "image_presentation", "image_multiple_choice_english", "audio_multiple_choice_images", "speak_english_from_translation"].includes(type));
    toggle(".prompt-audio-field", ["just_audio", "multiple_choice_audio_english", "write_translation_from_text_audio", "write_translation_from_audio", "complete_audio_text", "image_presentation", "audio_multiple_choice_images"].includes(type));
    toggle(".prompt-image-field", ["image_presentation", "image_multiple_choice_english", "audio_multiple_choice_images"].includes(type));
    toggle(".translation-field", !["speak_written_text", "multiple_choice_audio_english", "matching_pairs", "complete_audio_text", "image_multiple_choice_english", "audio_multiple_choice_images"].includes(type));
    toggle(".expected-field", ["speak_written_text", "speak_english_from_translation"].includes(type));
    toggle(".accept-field", type.includes("write_translation"));
    toggle(".cloze-field", isCompleteAudioText);
    elements.optionsSection.classList.toggle("d-none", !isMultipleChoice && !isMatchingPairs);
    elements.optionsTitle.textContent = isMatchingPairs ? "Cards para associar" : "Alternativas";
    updatePreview();
  }

  function toggle(selector, visible) {
    document.querySelectorAll(selector).forEach((node) => {
      node.classList.toggle("d-none", !visible);
    });
  }

  function hydrateFromSelectedCard() {
    const card = getSelectedCard();

    if (!card) {
      updatePreview();
      return;
    }

    elements.promptText.value = card.english_name || "";
    elements.audioFile.value = "";
    renderCurrentAudio(card.audio_url || card.audio || "");
    elements.imageFile.value = "";
    renderCurrentImage(card.image_url || card.image || "");
    elements.translation.value = card.international_name || "";
    elements.expectedTranscript.value = card.english_name || "";
    elements.clozeTemplate.value = card.english_name || "";
    elements.clozeAnswer.value = "";

    if (["multiple_choice_translation", "multiple_choice_audio_english", "image_multiple_choice_english", "audio_multiple_choice_images", "matching_pairs"].includes(elements.exerciseType.value)) {
      hydrateOptions(card);
    }

    updatePreview();
  }

  function hydrateOptions(card) {
    elements.optionsList.innerHTML = "";
    addOptionRow(card.id);

    state.cards
      .filter((item) => item.id !== card.id)
      .slice(0, 3)
      .forEach((item) => addOptionRow(item.id));
  }

  function addDefaultOptionRows() {
    for (let index = 0; index < 4; index += 1) {
      addOptionRow();
    }
  }

  function addOptionRow(id = "") {
    const row = document.createElement("div");
    row.className = "option-row";
    row.innerHTML = `
      <select class="form-select option-card" aria-label="Card da alternativa">
        ${buildOptionCardChoices(id)}
      </select>
      <button class="btn btn-outline-danger" type="button" title="Remover alternativa">
        <i class="bi bi-trash"></i>
      </button>
    `;
    row.querySelector("button").addEventListener("click", () => {
      row.remove();
      updatePreview();
    });
    row.querySelector("select").addEventListener("change", updatePreview);
    elements.optionsList.appendChild(row);
    updatePreview();
  }

  function buildOptionCardChoices(selectedId = "") {
    return [
      '<option value="">Selecione um card...</option>',
      ...state.cards
        .filter((card) => card.is_active !== false)
        .map((card) => {
          const isSelected = String(card.id) === String(selectedId) ? " selected" : "";
          const label = [card.english_name, card.international_name]
            .filter(Boolean)
            .join(" - ");
          return `<option value="${escapeAttribute(card.id)}"${isSelected}>${escapeHtml(label || card.id)}</option>`;
        }),
    ].join("");
  }

  function refreshOptionCardSelects() {
    elements.optionsList.querySelectorAll(".option-card").forEach((select) => {
      const selectedId = select.value;
      select.innerHTML = buildOptionCardChoices(selectedId);
      select.value = selectedId;
    });
    updatePreview();
  }

  function buildPayload(audioUrlOverride = "") {
    const type = elements.exerciseType.value;
    const card = getSelectedCard();
    const prompt = {};
    const answerConfig = {};

    if (!["write_translation_from_audio", "multiple_choice_audio_english", "complete_audio_text", "image_multiple_choice_english", "audio_multiple_choice_images", "speak_english_from_translation"].includes(type) && elements.promptText.value.trim()) {
      prompt.text = elements.promptText.value.trim();
    }

    if (["just_audio", "multiple_choice_audio_english", "write_translation_from_text_audio", "write_translation_from_audio", "complete_audio_text", "image_presentation", "audio_multiple_choice_images"].includes(type)) {
      const audioUrl = audioUrlOverride || getCurrentAudioUrl();
      if (audioUrl) {
        prompt.audio_url = audioUrl;
      }
    }

    if (type === "just_audio") {
      answerConfig.translation = elements.translation.value.trim();
    }

    if (type === "multiple_choice_translation") {
      answerConfig.correct_card_id = elements.card.value;
      answerConfig.correct_text = elements.translation.value.trim();
    }

    if (type === "multiple_choice_audio_english") {
      answerConfig.correct_card_id = elements.card.value;
      answerConfig.correct_text = card?.english_name || "";
    }

    if (type === "image_multiple_choice_english") {
      answerConfig.correct_card_id = elements.card.value;
      answerConfig.correct_text = card?.english_name || "";
    }

    if (type === "audio_multiple_choice_images") {
      answerConfig.correct_card_id = elements.card.value;
      answerConfig.correct_text = card?.english_name || "";
    }

    if (type.includes("write_translation")) {
      answerConfig.correct_text =
        type === "write_translation_from_audio"
          ? elements.promptText.value.trim() || card?.english_name || ""
          : elements.translation.value.trim();
      answerConfig.case_sensitive = false;
      answerConfig.trim = true;

      const accepted = splitAcceptedAnswers(elements.acceptedAnswers.value);
      if (accepted.length) {
        answerConfig.accept = accepted;
      }
    }

    if (type === "speak_written_text") {
      answerConfig.expected_transcript = elements.expectedTranscript.value.trim();
      answerConfig.language = "en-US";
    }

    if (type === "speak_english_from_translation") {
      prompt.text = elements.translation.value.trim();
      answerConfig.expected_transcript = elements.expectedTranscript.value.trim();
      answerConfig.language = "en-US";
    }

    if (type === "complete_audio_text") {
      prompt.text = elements.clozeTemplate.value.trim();
      answerConfig.correct_text = elements.clozeAnswer.value.trim();
      answerConfig.case_sensitive = false;
      answerConfig.trim = true;
    }

    return {
      exercise_set: elements.exerciseSet.value,
      card: elements.card.value,
      type,
      skill: elements.exerciseSkill.value,
      prompt,
      options: ["multiple_choice_translation", "multiple_choice_audio_english", "image_multiple_choice_english", "audio_multiple_choice_images"].includes(type) ? getOptions() : [],
      pair_cards: type === "matching_pairs" ? getSelectedOptionCardIds() : [],
      answer_config: answerConfig,
      is_active: elements.isActive.checked,
      difficulty: Number(elements.difficulty.value || 1),
      order: Number(elements.order.value || 0),
    };
  }


  async function uploadCardMediaIfNeeded() {
    const audioFile = elements.audioFile.files?.[0];
    const imageFile = elements.imageFile.files?.[0];

    if (!audioFile && !imageFile) {
      return getCurrentAudioUrl();
    }

    if (!elements.card.value) {
      throw new Error("Selecione um card antes de enviar o audio.");
    }

    const formData = new FormData();
    if (audioFile) {
      formData.append("audio", audioFile);
    }
    if (imageFile) {
      formData.append("image", imageFile);
    }

    const updatedCard = await apiRequest(`/cards/${encodeURIComponent(elements.card.value)}/`, {
      method: "PATCH",
      body: formData,
    });

    state.cards = state.cards.map((card) =>
      String(card.id) === String(updatedCard.id) ? { ...card, ...updatedCard } : card
    );
    elements.audioFile.value = "";
    renderCurrentAudio(updatedCard.audio || updatedCard.audio_url || "");
    elements.imageFile.value = "";
    renderCurrentImage(updatedCard.image || updatedCard.image_url || "");

    return updatedCard.audio || updatedCard.audio_url || "";
  }

  function getCurrentAudioUrl() {
    const card = getSelectedCard();
    return card?.audio_url || card?.audio || "";
  }


  function renderSelectedAudioFile() {
    const file = elements.audioFile.files?.[0];

    if (!file) {
      renderCurrentAudio(getCurrentAudioUrl());
      return;
    }

    elements.currentAudio.textContent = `${file.name} sera enviado ao salvar.`;
    updatePreview();
  }

  function renderCurrentAudio(audioUrl) {
    if (!audioUrl) {
      elements.currentAudio.textContent = "Nenhum audio salvo para este card.";
      return;
    }

    elements.currentAudio.innerHTML = `<a href="${escapeAttribute(audioUrl)}" target="_blank" rel="noreferrer">Audio atual do card</a>`;
  }

  function renderSelectedImageFile() {
    const file = elements.imageFile.files?.[0];

    if (!file) {
      const card = getSelectedCard();
      renderCurrentImage(card?.image_url || card?.image || "");
      return;
    }

    elements.currentImage.textContent = `${file.name} sera enviada ao salvar.`;
    updatePreview();
  }

  function renderCurrentImage(imageUrl) {
    if (!imageUrl) {
      elements.currentImage.textContent = "Nenhuma imagem salva para este card.";
      return;
    }

    elements.currentImage.innerHTML = `<a href="${escapeAttribute(imageUrl)}" target="_blank" rel="noreferrer">Imagem atual do card</a>`;
  }

  function getOptions() {
    const useEnglish = [
      "multiple_choice_audio_english",
      "image_multiple_choice_english",
      "audio_multiple_choice_images",
    ].includes(elements.exerciseType.value);

    return Array.from(elements.optionsList.querySelectorAll(".option-row"))
      .map((row) => {
        const id = row.querySelector(".option-card").value;
        const card = state.cards.find((item) => String(item.id) === String(id));

        return {
          id,
          text: useEnglish
            ? card?.english_name || ""
            : card?.international_name || card?.english_name || "",
          audio_url: card?.audio_url || card?.audio || "",
          image_url: card?.image_url || card?.image || "",
        };
      })
      .filter((option) => option.id);
  }

  function getSelectedOptionCardIds() {
    return [
      ...new Set(
        Array.from(elements.optionsList.querySelectorAll(".option-card"))
          .map((select) => select.value)
          .filter(Boolean)
      ),
    ];
  }

  function getSelectedCard() {
    return state.cards.find((item) => String(item.id) === String(elements.card.value));
  }

  function splitAcceptedAnswers(value) {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function updatePreview() {
    elements.jsonPreview.textContent = JSON.stringify(buildPayload(), null, 2);
  }

  async function submitExercise(event) {
    event.preventDefault();
    elements.form.classList.add("was-validated");

    if (!elements.form.checkValidity()) {
      return;
    }

    hideAlert();
    try {
      const uploadedAudioUrl = await uploadCardMediaIfNeeded();
      const payload = buildPayload(uploadedAudioUrl);
      await apiRequest("/exercises/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("Exercicio criado com sucesso.", "success");
      elements.order.value = Number(elements.order.value || 0) + 1;
      updatePreview();
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function copyJson() {
    await navigator.clipboard.writeText(elements.jsonPreview.textContent);
    showAlert("JSON copiado.", "info");
  }

  function setLoading(isLoading) {
    elements.saveConnectionButton.disabled = isLoading;
    elements.reloadDataButton.disabled = isLoading;
  }

  function setConnectionStatus(label, variant) {
    elements.connectionStatus.className = `badge text-bg-${variant}`;
    elements.connectionStatus.textContent = label;
  }

  function showAlert(message, variant) {
    elements.alertBox.className = `alert alert-${variant}`;
    elements.alertBox.textContent = message;
  }

  function hideAlert() {
    elements.alertBox.className = "alert d-none";
    elements.alertBox.textContent = "";
  }

  function normalizeText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function getApiErrorMessage(data) {
    if (!data) {
      return "Erro ao acessar a API.";
    }

    if (typeof data === "string") {
      return data;
    }

    if (data.detail || data.message) {
      return data.detail || data.message;
    }

    return Object.entries(data)
      .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(" ") : value}`)
      .join("\n");
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replace(/`/g, "&#096;");
  }
})();
