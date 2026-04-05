(() => {
  const root = document.documentElement;
  const currentScript = document.currentScript;

  try {
    const storedTheme = localStorage.getItem("theme");
    const storedLanguage = localStorage.getItem("language");

    if (storedTheme === "light" || storedTheme === "dark") {
      root.dataset.theme = storedTheme;
    }

    if (storedLanguage === "zh" || storedLanguage === "en") {
      root.dataset.language = storedLanguage;
      root.lang = storedLanguage === "zh" ? "zh-CN" : "en";
    }
  } catch (error) {
    console.warn("Preferences could not be restored.", error);
  }

  if (!currentScript) {
    return;
  }

  const faviconHref = new URL("favicon.svg", currentScript.src).href;
  let favicon = document.querySelector('link[rel~="icon"]');

  if (!favicon) {
    favicon = document.createElement("link");
    favicon.rel = "icon";
    document.head.appendChild(favicon);
  }

  favicon.type = "image/svg+xml";
  favicon.href = faviconHref;
})();
