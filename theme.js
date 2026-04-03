(() => {
  const storageKey = "theme";
  const root = document.documentElement;
  const buttons = document.querySelectorAll(".theme-toggle");
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const sunIcon = `
    <circle cx="12" cy="12" r="4.25"></circle>
    <path d="M12 2.5v2.25"></path>
    <path d="M12 19.25v2.25"></path>
    <path d="M4.93 4.93l1.59 1.59"></path>
    <path d="M17.48 17.48l1.59 1.59"></path>
    <path d="M2.5 12h2.25"></path>
    <path d="M19.25 12h2.25"></path>
    <path d="M4.93 19.07l1.59-1.59"></path>
    <path d="M17.48 6.52l1.59-1.59"></path>
  `;
  const moonIcon = `
    <path d="M20.1 14.2A8.8 8.8 0 0 1 9.8 3.9a9.4 9.4 0 1 0 10.3 10.3z"></path>
  `;

  const getSystemTheme = () => (mediaQuery.matches ? "dark" : "light");

  const getStoredTheme = () => {
    try {
      const stored = localStorage.getItem(storageKey);
      return stored === "light" || stored === "dark" ? stored : null;
    } catch (error) {
      console.warn("Theme preference could not be read.", error);
      return null;
    }
  };

  const getActiveTheme = () => root.dataset.theme || getSystemTheme();

  const syncButtons = (theme) => {
    const nextLabel = theme === "dark" ? "light" : "dark";
    const iconMarkup = theme === "dark" ? moonIcon : sunIcon;

    for (const button of buttons) {
      const icon = button.querySelector("svg");
      if (icon) {
        icon.innerHTML = iconMarkup;
      }
      button.setAttribute("aria-label", `Switch to ${nextLabel} theme`);
      button.setAttribute("aria-pressed", String(theme === "dark"));
      button.setAttribute("title", `Switch to ${nextLabel} theme`);
    }
  };

  const applyTheme = (theme, persist) => {
    root.dataset.theme = theme;
    syncButtons(theme);

    if (!persist) {
      return;
    }

    try {
      localStorage.setItem(storageKey, theme);
    } catch (error) {
      console.warn("Theme preference could not be stored.", error);
    }
  };

  const initialTheme = getStoredTheme() || getSystemTheme();
  applyTheme(initialTheme, false);

  for (const button of buttons) {
    button.addEventListener("click", () => {
      const nextTheme = getActiveTheme() === "dark" ? "light" : "dark";
      applyTheme(nextTheme, true);
    });
  }

  mediaQuery.addEventListener("change", () => {
    if (!getStoredTheme()) {
      applyTheme(getSystemTheme(), false);
    }
  });
})();
