(function () {
  const STORAGE_KEY = "langExerciseBuilder";
  const page = document.querySelector("main[data-api-base-url]");
  const form = document.querySelector("#loginForm");
  const alertBox = document.querySelector("#loginAlert");
  const button = document.querySelector("#loginButton");

  const saved = readStorage();
  if (saved.accessToken) window.location.replace("/exercise-builder/");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    alertBox.classList.add("d-none");
    button.disabled = true;
    button.textContent = "Entrando...";
    try {
      const response = await fetch(`${page.dataset.apiBaseUrl}/auth/token/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          username: document.querySelector("#username").value.trim(),
          password: document.querySelector("#password").value,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Usuario ou senha invalidos.");
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        apiBaseUrl: page.dataset.apiBaseUrl,
        accessToken: data.access,
        usuario: data.usuario,
      }));
      window.location.replace("/exercise-builder/");
    } catch (error) {
      alertBox.textContent = error.message;
      alertBox.classList.remove("d-none");
      button.disabled = false;
      button.textContent = "Entrar";
    }
  });

  function readStorage() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
    catch { return {}; }
  }
})();
