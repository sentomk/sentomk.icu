#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT_DIR / "posts"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "posts"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)(.*)$", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
UL_RE = re.compile(r"^[-*+]\s+(.+)$")
OL_RE = re.compile(r"^\d+\.\s+(.+)$")
CODE_FENCE_RE = re.compile(r"^```([\w-]+)?\s*$")
HR_RE = re.compile(r"^[-*_]{3,}\s*$")


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    text = raw.replace("\r\n", "\n")
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text

    front_matter = match.group(1)
    body = match.group(2)
    metadata: dict[str, str] = {}

    for line in front_matter.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"').strip("'")

    return metadata, body


def sanitize_slug(value: str, fallback: str) -> str:
    slug = value.strip()
    if not slug:
        slug = fallback
    slug = slug.replace("\\", "-").replace("/", "-")
    slug = slug.strip()
    return slug or "untitled-post"


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_excerpt(text: str, limit: int = 72) -> str:
    collapsed = normalize_spaces(text)
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def first_paragraph_text(markdown_body: str) -> str:
    lines = markdown_body.splitlines()
    acc: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if acc:
                break
            continue
        if (
            stripped.startswith("#")
            or stripped.startswith(">")
            or UL_RE.match(stripped)
            or OL_RE.match(stripped)
            or CODE_FENCE_RE.match(stripped)
            or HR_RE.match(stripped)
        ):
            if acc:
                break
            continue
        acc.append(stripped)

    text = normalize_spaces(" ".join(acc))
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", text)
    text = text.replace("**", "").replace("*", "")
    return text


def extract_title(markdown_body: str, metadata: dict[str, str], fallback: str) -> tuple[str, str]:
    title = metadata.get("title", "").strip()
    if title:
        return title, markdown_body

    lines = markdown_body.splitlines()
    for idx, line in enumerate(lines):
        match = re.match(r"^#\s+(.+?)\s*$", line.strip())
        if not match:
            continue
        extracted_title = match.group(1).strip()
        del lines[idx]
        if idx < len(lines) and not lines[idx].strip():
            del lines[idx]
        return extracted_title, "\n".join(lines)

    fallback_title = fallback.replace("-", " ").strip() or "Untitled Post"
    return fallback_title, markdown_body


def render_inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    code_spans: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        content = match.group(1)
        token = f"@@CODE_SPAN_{len(code_spans)}@@"
        code_spans.append(f"<code>{content}</code>")
        return token

    escaped = re.sub(r"`([^`]+)`", stash_code, escaped)

    def render_link(match: re.Match[str]) -> str:
        label = match.group(1)
        target = html.escape(match.group(2), quote=True)
        return f'<a href="{target}">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", render_link, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)

    for idx, code_html in enumerate(code_spans):
        escaped = escaped.replace(f"@@CODE_SPAN_{idx}@@", code_html)

    return escaped


def starts_new_block(stripped: str) -> bool:
    return bool(
        stripped.startswith(">")
        or HEADING_RE.match(stripped)
        or UL_RE.match(stripped)
        or OL_RE.match(stripped)
        or CODE_FENCE_RE.match(stripped)
        or HR_RE.match(stripped)
    )


def markdown_to_html(markdown_body: str) -> str:
    lines = markdown_body.splitlines()
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        fence_match = CODE_FENCE_RE.match(stripped)
        if fence_match:
            language = (fence_match.group(1) or "").strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not CODE_FENCE_RE.match(lines[i].strip()):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            class_attr = f' class="language-{language}"' if language else ""
            escaped_code = html.escape("\n".join(code_lines))
            out.append(f"<pre><code{class_attr}>{escaped_code}</code></pre>")
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            level = len(heading_match.group(1))
            content = render_inline(heading_match.group(2).strip())
            out.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        if HR_RE.match(stripped):
            out.append("<hr />")
            i += 1
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_line = re.sub(r"^>\s?", "", lines[i].strip())
                quote_lines.append(quote_line)
                i += 1
            nested_html = markdown_to_html("\n".join(quote_lines))
            out.append("<blockquote>")
            out.append(nested_html)
            out.append("</blockquote>")
            continue

        ul_match = UL_RE.match(stripped)
        if ul_match:
            items: list[str] = []
            while i < len(lines):
                candidate = lines[i].strip()
                item_match = UL_RE.match(candidate)
                if not item_match:
                    break
                items.append(f"<li>{render_inline(item_match.group(1).strip())}</li>")
                i += 1
            out.append("<ul>")
            out.extend(items)
            out.append("</ul>")
            continue

        ol_match = OL_RE.match(stripped)
        if ol_match:
            items = []
            while i < len(lines):
                candidate = lines[i].strip()
                item_match = OL_RE.match(candidate)
                if not item_match:
                    break
                items.append(f"<li>{render_inline(item_match.group(1).strip())}</li>")
                i += 1
            out.append("<ol>")
            out.extend(items)
            out.append("</ol>")
            continue

        paragraph_parts = [stripped]
        i += 1
        while i < len(lines):
            candidate = lines[i].strip()
            if not candidate or starts_new_block(candidate):
                break
            paragraph_parts.append(candidate)
            i += 1

        paragraph_text = normalize_spaces(" ".join(paragraph_parts))
        out.append(f"<p>{render_inline(paragraph_text)}</p>")

    return "\n".join(out)


def build_post_html(title: str, metadata: dict[str, str], body_html: str, kind: str) -> str:
    date_text = metadata.get("date", "").strip()
    default_kicker = "Essay" if kind == "essay" else "Note"
    kicker = metadata.get("kicker", default_kicker).strip() or default_kicker
    category = metadata.get("category", "").strip()
    lede = metadata.get("lede", "").strip()
    description = metadata.get("description", "").strip()

    if not lede:
        lede = f"Article: {title}"
    if not description:
        description = lede or f"Article: {title}"

    kicker_parts = [kicker]
    if date_text:
        kicker_parts.append(date_text)
    if category:
        kicker_parts.append(category)
    kicker_line = " / ".join(kicker_parts)

    next_href = metadata.get("next_href", "").strip()
    next_title = metadata.get("next_title", "").strip()
    if next_href and next_title:
        next_nav = (
            f'<a href="{html.escape(next_href, quote=True)}">'
            f"下一篇：{html.escape(next_title)}</a>"
        )
    else:
        default_next_href = "../essay.html" if kind == "essay" else "../note.html"
        next_nav = f'<a href="{default_next_href}">更多</a>'

    indented_body = "\n".join(
        f"            {line}" if line else "" for line in body_html.splitlines()
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="color-scheme" content="light dark" />
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description, quote=True)}" />
    <link rel="icon" type="image/svg+xml" href="../favicon.svg" />
    <script>
      try {{
        const storedTheme = localStorage.getItem("theme");
        const storedLanguage = localStorage.getItem("language");
        if (storedTheme === "light" || storedTheme === "dark") {{
          document.documentElement.dataset.theme = storedTheme;
        }}
        if (storedLanguage === "zh" || storedLanguage === "en") {{
          document.documentElement.dataset.language = storedLanguage;
          document.documentElement.lang = storedLanguage === "zh" ? "zh-CN" : "en";
        }}
      }} catch (error) {{
        console.warn("Preferences could not be restored.", error);
      }}
    </script>
    <link rel="stylesheet" href="../styles.css?v=8" />
  </head>
  <body class="post-page">
    <div class="page-shell">
      <header class="site-header site-header--compact">
        <div class="site-header__inner">
          <div class="site-links" aria-label="Social links">
            <a class="site-links__item" href="https://github.com/sentomk" aria-label="GitHub" title="GitHub">
              <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                <path d="M12 2.25a10 10 0 0 0-3.16 19.49c.5.09.68-.21.68-.48v-1.7c-2.78.6-3.37-1.18-3.37-1.18a2.66 2.66 0 0 0-1.12-1.47c-.92-.63.07-.62.07-.62a2.11 2.11 0 0 1 1.54 1.03a2.15 2.15 0 0 0 2.94.84a2.17 2.17 0 0 1 .64-1.35c-2.22-.25-4.56-1.11-4.56-4.95a3.87 3.87 0 0 1 1.03-2.68a3.58 3.58 0 0 1 .1-2.65s.84-.27 2.75 1.02a9.44 9.44 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02a3.58 3.58 0 0 1 .1 2.65a3.87 3.87 0 0 1 1.03 2.68c0 3.85-2.34 4.69-4.57 4.94a2.43 2.43 0 0 1 .69 1.89v2.8c0 .27.18.58.69.48A10 10 0 0 0 12 2.25Z"></path>
              </svg>
            </a>
            <a class="site-links__item" href="mailto:sentomk@pm.me" aria-label="Email" title="Email">
              <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                <path d="M4.5 6.75h15a1.5 1.5 0 0 1 1.5 1.5v7.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 15.75v-7.5a1.5 1.5 0 0 1 1.5-1.5Z"></path>
                <path d="m4 8l8 6l8-6"></path>
              </svg>
            </a>
            <a class="site-links__item" href="https://www.linkedin.com/in/sentomk" aria-label="LinkedIn" title="LinkedIn">
              <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                <rect x="4.25" y="4.25" width="15.5" height="15.5" rx="2.2"></rect>
                <path d="M8.2 10.1v5.85"></path>
                <path d="M8.2 8.2h.01"></path>
                <path d="M12 15.95V12.8c0-1.15.62-1.9 1.72-1.9c1 0 1.48.68 1.48 1.9v3.15"></path>
                <path d="M12 10.1v.92"></path>
              </svg>
            </a>
            <a class="site-links__item site-links__item--hn" href="https://news.ycombinator.com/user?id=sentomk" aria-label="Hacker News" title="Hacker News">
              <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                <rect x="4" y="4" width="16" height="16" rx="1.6"></rect>
                <path d="M9 8l3 4l3-4"></path>
                <path d="M12 12v4"></path>
              </svg>
            </a>
          </div>
          <nav class="site-nav" aria-label="Primary">
            <a href="../index.html">首页</a>
            <a href="../essay.html">文章</a>
            <a href="../note.html">短札</a>
            <a href="../index.html#archive">归档</a>
            <span class="site-nav__sep" aria-hidden="true">|</span>
            <button class="theme-toggle" type="button" aria-label="切换主题">
              <span class="theme-toggle__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false"></svg>
              </span>
            </button>
          </nav>
        </div>
      </header>

      <main class="post-layout">
        <article class="post-article">
          <header class="post-article__header">
            <p class="post-article__kicker">{html.escape(kicker_line)}</p>
            <h1>{html.escape(title)}</h1>
            <p class="post-article__lede">{html.escape(lede)}</p>
          </header>

          <div class="post-article__body">
{indented_body}
          </div>
        </article>

        <nav class="post-footer-nav" aria-label="Post navigation">
          <a href="../index.html">返回首页</a>
          {next_nav}
        </nav>
      </main>
    </div>
    <script src="../ui.js?v=5"></script>
  </body>
</html>
"""


def build_markdown_file(markdown_path: Path, output_dir: Path) -> list[Path]:
    raw = markdown_path.read_text(encoding="utf-8")
    metadata, markdown_body = parse_front_matter(raw)

    title, markdown_body = extract_title(markdown_body, metadata, markdown_path.stem)
    if "lede" not in metadata or not metadata["lede"].strip():
        metadata["lede"] = first_paragraph_text(markdown_body)

    body_html = markdown_to_html(markdown_body.strip())
    slug = sanitize_slug(metadata.get("slug", ""), markdown_path.stem)
    output_path = output_dir / f"{slug}.html"

    output_html = build_post_html(title, metadata, body_html, kind="essay")
    output_path.write_text(output_html, encoding="utf-8")
    return [output_path]


def parse_jsonl_entries(jsonl_path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []

    for index, raw_line in enumerate(jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{jsonl_path}:{index}: invalid JSON: {error.msg}") from error

        if not isinstance(payload, dict):
            raise ValueError(f"{jsonl_path}:{index}: each JSONL line must be an object")

        entry = {str(key).strip().lower(): str(value).strip() for key, value in payload.items()}
        if not entry.get("body") and not entry.get("content"):
            raise ValueError(f"{jsonl_path}:{index}: note entry must include body or content")
        entries.append(entry)

    return entries


def build_jsonl_file(jsonl_path: Path, output_dir: Path) -> list[Path]:
    generated: list[Path] = []
    entries = parse_jsonl_entries(jsonl_path)

    for index, entry in enumerate(entries, start=1):
        body_markdown = entry.get("body", "").strip() or entry.get("content", "").strip()
        if "lede" not in entry or not entry["lede"].strip():
            entry["lede"] = first_paragraph_text(body_markdown)
        if "description" not in entry or not entry["description"].strip():
            entry["description"] = entry["lede"]

        title = entry.get("title", "").strip()
        if not title:
            fallback_title = entry["lede"] or f"Note {index}"
            title = make_excerpt(fallback_title, limit=48)

        slug_seed = entry.get("slug", "").strip() or f"{jsonl_path.stem}-{index:02d}"
        slug = sanitize_slug(slug_seed, f"{jsonl_path.stem}-{index:02d}")
        output_path = output_dir / f"{slug}.html"

        if "next_href" not in entry or not entry["next_href"].strip():
            entry["next_href"] = "../note.html"

        body_html = markdown_to_html(body_markdown)
        output_html = build_post_html(title, entry, body_html, kind="note")
        output_path.write_text(output_html, encoding="utf-8")
        generated.append(output_path)

    return generated


def build_file(source_path: Path, output_dir: Path) -> list[Path]:
    suffix = source_path.suffix.lower()
    if suffix == ".md":
        return build_markdown_file(source_path, output_dir)
    if suffix == ".jsonl":
        return build_jsonl_file(source_path, output_dir)
    raise ValueError(f"Unsupported source format: {source_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build blog post HTML files from Markdown and JSONL.")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Source directory (default: posts).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="HTML output directory (default: posts).",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Build a single .md or .jsonl file.",
    )
    return parser.parse_args()


def format_output_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def main() -> int:
    args = parse_args()
    source_dir: Path = args.source.resolve()
    output_dir: Path = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.file is not None:
        target = args.file.resolve()
        if not target.exists():
            print(f"[error] File not found: {target}")
            return 1
        try:
            generated_files = build_file(target, output_dir)
        except ValueError as error:
            print(f"[error] {error}")
            return 1
        for generated in generated_files:
            print(f"[ok] {format_output_path(generated)}")
        return 0

    if not source_dir.exists():
        print(f"[error] Source directory not found: {source_dir}")
        return 1

    source_files = sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".jsonl"}
        and not path.name.startswith("_")
    )

    if not source_files:
        print(f"[warn] No source files found in {source_dir}")
        return 0

    for source_path in source_files:
        try:
            generated_files = build_file(source_path, output_dir)
        except ValueError as error:
            print(f"[error] {error}")
            return 1
        for generated in generated_files:
            print(f"[ok] {format_output_path(generated)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
