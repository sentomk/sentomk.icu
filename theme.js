(() => {
  const themeStorageKey = "theme";
  const languageStorageKey = "language";
  const root = document.documentElement;
  const body = document.body;
  const themeButtons = document.querySelectorAll(".theme-toggle");
  const languageButtons = document.querySelectorAll(".language-toggle");
  const page = document.body.dataset.page;
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
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
  const translations = {
    home: {
      documentTitle: {
        zh: "a·common·place",
        en: "a·common·place",
      },
      navHome: { zh: "首页", en: "Home" },
      navEssays: { zh: "文章", en: "Essays" },
      navNotes: { zh: "短札", en: "Notes" },
      navArchive: { zh: "归档", en: "Archive" },
      heroEyebrow: { zh: "随笔与代码", en: "NOTES AND CODE" },
      heroTitle: { zh: "一个适合认真写字的博客。", en: "A blog built for deliberate writing." },
      heroLede: {
        zh: "参考传统技术博客的气质，但不做陈旧复刻。这里更像一本持续增补的工作日志：写程序、读系统、记问题，也保留一点缓慢和留白。",
        en: "It borrows the restraint of older technical blogs without turning into a replica. The site works more like a living notebook: code, systems, debugging notes, and enough whitespace to let the writing breathe.",
      },
      featuredLabel: { zh: "精选长文", en: "Featured Essay" },
      featuredDate: { zh: "2026年4月2日", en: "April 2, 2026" },
      featuredTitle: {
        zh: "为什么我更喜欢“小而明确”的个人网站",
        en: "Why I Prefer Small, Definite Personal Websites",
      },
      featuredExcerpt: {
        zh: "一个博客不需要先长成产品。先有稳定的排版、清晰的索引、可以长期追加的文章结构，往往比功能堆叠更重要。",
        en: "A blog does not need to become a product first. Stable typography, clear indexing, and a structure you can extend for years usually matter more than piling on features.",
      },
      essaysHeading: { zh: "长文章", en: "Longform" },
      post1Meta: { zh: "设计 / 写作", en: "Design / Writing" },
      post1Title: {
        zh: "为什么我更喜欢“小而明确”的个人网站",
        en: "Why I Prefer Small, Definite Personal Websites",
      },
      post1Excerpt: {
        zh: "从信息密度、排版节奏和长期维护成本出发，重新理解内容型博客的价值。",
        en: "A reconsideration of content-first blogs through information density, typography, and long-term maintenance cost.",
      },
      post2Meta: { zh: "工程 / 工具", en: "Engineering / Tools" },
      post2Title: {
        zh: "把开发日志写成能复用的文章",
        en: "Turning a Dev Log into a Reusable Essay",
      },
      post2Excerpt: {
        zh: "一次问题排查，如果能留下背景、判断和结论，它就不只是备忘录，而是知识资产。",
        en: "A debugging session becomes more than a memo once it preserves context, judgment, and conclusions.",
      },
      post3Meta: { zh: "系统 / 观察", en: "Systems / Observation" },
      post3Title: {
        zh: "读完一段源码之后，应该记录什么",
        en: "What to Record After Reading a Piece of Source Code",
      },
      post3Excerpt: {
        zh: "不只是 API 和结论，更要记下那些让你改变理解模型的边界条件。",
        en: "Record not only APIs and conclusions, but the edge conditions that changed your mental model.",
      },
      notesHeading: { zh: "短札", en: "Notes" },
      note1: {
        zh: "博客首页不该像产品落地页，目录感比 CTA 更重要。",
        en: "A blog homepage should read like an index, not a product landing page. Directory sense matters more than CTA buttons.",
      },
      note2: {
        zh: "正文宽度宁可偏窄，也不要让技术文章变成横向扫描任务。",
        en: "A slightly narrow measure is preferable to turning a technical article into a horizontal scanning task.",
      },
      note3: {
        zh: "好的归档页不是“旧文章列表”，而是你的长期思考地图。",
        en: "A good archive is not just a list of old posts. It is a map of long-term thinking.",
      },
      aboutHeading: { zh: "关于这里", en: "About" },
      aboutBody: {
        zh: "这是一个静态博客雏形。没有引入框架，也没有复杂交互，重点放在排版、层次和可持续写作的氛围上。",
        en: "This is a static blog prototype. No framework, no dense interaction layer, just typography, structure, and a setup that supports sustained writing.",
      },
      archiveHeading: { zh: "归档", en: "Archive" },
    },
    "post-small-things": {
      documentTitle: {
        zh: "为什么我更喜欢“小而明确”的个人网站",
        en: "Why I Prefer Small, Definite Personal Websites",
      },
      navHome: { zh: "首页", en: "Home" },
      navEssays: { zh: "文章", en: "Essays" },
      navArchive: { zh: "归档", en: "Archive" },
      postKicker: { zh: "长文 / 2026年4月2日", en: "Essay / April 2, 2026" },
      postTitle: {
        zh: "为什么我更喜欢“小而明确”的个人网站",
        en: "Why I Prefer Small, Definite Personal Websites",
      },
      postLede: {
        zh: "一些网站努力证明自己什么都能做，于是首页像控制台、侧栏像导航树、每一个模块都在抢注意力。我越来越偏向反方向：只保留真正重要的东西，让内容自己站出来。",
        en: "Some sites work hard to prove they can do everything, so the homepage turns into a dashboard, the sidebar into a navigation tree, and every module competes for attention. I prefer the opposite direction: keep only what matters and let the writing stand on its own.",
      },
      paragraph1: {
        zh: "写作型网站首先是一个阅读界面。页面最重要的工作，不是展示作者会多少技术，而是让读者以尽可能低的摩擦进入文章。宽度、字距、层次、留白，这些看似保守的选择，决定了一个网站能否被长期阅读。",
        en: "A writing site is first a reading interface. Its most important job is not to demonstrate how much technology the author knows, but to bring the reader into the article with as little friction as possible. Measure, spacing, hierarchy, and whitespace may sound conservative, but they decide whether a site can be read for years.",
      },
      paragraph2: {
        zh: "我喜欢那些老派技术博客，并不是因为它们“旧”，而是因为它们在很多地方做得克制：首页说明这是谁的站点、最近写了什么、历史上写过什么，仅此而已。它们不试图把每一篇文章包装成营销资产，也不会要求每一次访问都转化成订阅或点击。",
        en: "I like old-school technical blogs not because they are old, but because they are restrained in the right places. The homepage explains whose site this is, what was written recently, and what exists in the archive. That is enough. They do not try to package every article as a marketing asset, and they do not expect every visit to convert into a subscription or a click.",
      },
      blockquote1: {
        zh: "一个博客最好的界面，往往是让人忘记界面的界面。",
        en: "The best interface for a blog is often the one that lets you forget the interface exists.",
      },
      paragraph3: {
        zh: "“简单”并不等于“随便”。真正的小网站仍然需要明确的视觉方向。例如纸面感的底色、略带报刊气质的标题、压低饱和度的强调色，以及有节制的分隔线。它们共同传达的信息是：这里适合安静地读，而不是快速地滑过去。",
        en: "Simple does not mean careless. A genuinely small site still needs a clear visual direction: a paper-like background, headlines with a faint editorial feel, low-saturation accents, and restrained dividers. Together they tell the reader that this is a place for calm reading, not fast scrolling.",
      },
      sectionTitle: { zh: "我希望保留的几个特征", en: "A Few Traits I Want to Keep" },
      paragraph4: {
        zh: "第一，首页应该像目录页，而不是产品首页。第二，文章页应该把主要空间留给正文。第三，归档必须清晰，因为博客的价值常常来自它的时间纵深，而不是最新一篇文章。",
        en: "First, the homepage should behave like an index rather than a product front page. Second, the article page should give most of its space to the body text. Third, the archive has to be clear, because much of a blog's value comes from its time depth rather than its latest post.",
      },
      paragraph5: {
        zh: "如果将来再往这个网站上加功能，我也会优先考虑那些支持写作的东西：标签、全文检索、RSS、代码块样式，而不是社交计数器、复杂推荐流或过度动画。",
        en: "If I add more features later, I will prioritize the ones that support writing: tags, full-text search, RSS, and code block styling, not social counters, elaborate recommendation flows, or overdone animation.",
      },
      backHome: { zh: "返回首页", en: "Back Home" },
      nextPost: {
        zh: "下一篇：把开发日志写成能复用的文章",
        en: "Next: Turning a Dev Log into a Reusable Essay",
      },
    },
  };

  const getSystemTheme = () => (mediaQuery.matches ? "dark" : "light");

  const getStoredTheme = () => {
    try {
      const stored = localStorage.getItem(themeStorageKey);
      return stored === "light" || stored === "dark" ? stored : null;
    } catch (error) {
      console.warn("Theme preference could not be read.", error);
      return null;
    }
  };

  const getStoredLanguage = () => {
    try {
      const stored = localStorage.getItem(languageStorageKey);
      return stored === "zh" || stored === "en" ? stored : null;
    } catch (error) {
      console.warn("Language preference could not be read.", error);
      return null;
    }
  };

  const getActiveTheme = () => root.dataset.theme || getSystemTheme();
  const getActiveLanguage = () => root.dataset.language || "zh";

  const syncButtons = (theme) => {
    const nextLabel = theme === "dark" ? "light" : "dark";
    const iconMarkup = theme === "dark" ? moonIcon : sunIcon;

    for (const button of themeButtons) {
      const icon = button.querySelector("svg");
      if (icon) {
        icon.innerHTML = iconMarkup;
      }
      button.dataset.icon = theme;
      button.setAttribute("aria-label", `Switch to ${nextLabel} theme`);
      button.setAttribute("aria-pressed", String(theme === "dark"));
      button.setAttribute("title", `Switch to ${nextLabel} theme`);
    }
  };

  const applyLanguageContent = (language, persist) => {
    const pageTranslations = translations[page];
    root.dataset.language = language;
    root.lang = language === "zh" ? "zh-CN" : "en";

    if (pageTranslations) {
      document.title = pageTranslations.documentTitle[language];

      for (const element of document.querySelectorAll("[data-i18n]")) {
        const key = element.dataset.i18n;
        if (pageTranslations[key]) {
          element.textContent = pageTranslations[key][language];
        }
      }
    }

    for (const button of languageButtons) {
      const nextLanguage = language === "zh" ? "EN" : "中";
      button.textContent = nextLanguage;
      button.setAttribute(
        "aria-label",
        language === "zh" ? "Switch to English" : "切换到中文"
      );
      button.setAttribute(
        "title",
        language === "zh" ? "Switch to English" : "切换到中文"
      );
    }

    if (!persist) {
      return;
    }

    try {
      localStorage.setItem(languageStorageKey, language);
    } catch (error) {
      console.warn("Language preference could not be stored.", error);
    }
  };

  const applyLanguage = (language, persist, animate) => {
    if (!animate || reducedMotionQuery.matches) {
      applyLanguageContent(language, persist);
      return;
    }

    body.classList.remove("is-language-entering");
    body.classList.add("is-language-leaving");

    window.setTimeout(() => {
      applyLanguageContent(language, persist);
      body.classList.remove("is-language-leaving");
      body.classList.add("is-language-entering");

      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => {
          body.classList.remove("is-language-entering");
        });
      });
    }, 120);
  };

  const applyTheme = (theme, persist) => {
    root.dataset.theme = theme;
    syncButtons(theme);

    if (!persist) {
      return;
    }

    try {
      localStorage.setItem(themeStorageKey, theme);
    } catch (error) {
      console.warn("Theme preference could not be stored.", error);
    }
  };

  const initialTheme = getStoredTheme() || getSystemTheme();
  const initialLanguage = getStoredLanguage() || "zh";
  applyTheme(initialTheme, false);
  applyLanguage(initialLanguage, false, false);

  for (const button of themeButtons) {
    button.addEventListener("click", () => {
      const nextTheme = getActiveTheme() === "dark" ? "light" : "dark";
      applyTheme(nextTheme, true);
    });
  }

  for (const button of languageButtons) {
    button.addEventListener("click", () => {
      const nextLanguage = getActiveLanguage() === "zh" ? "en" : "zh";
      applyLanguage(nextLanguage, true, true);
    });
  }

  mediaQuery.addEventListener("change", () => {
    if (!getStoredTheme()) {
      applyTheme(getSystemTheme(), false);
    }
  });
})();
