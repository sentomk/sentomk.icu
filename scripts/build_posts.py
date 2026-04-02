#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT_DIR / "posts" / "markdown"
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


def build_post_html(title: str, metadata: dict[str, str], body_html: str) -> str:
    date_text = metadata.get("date", "").strip()
    kicker = metadata.get("kicker", "Essay").strip() or "Essay"
    category = metadata.get("category", "").strip()
    lede = metadata.get("lede", "").strip()
    description = metadata.get("description", "").strip()
    site_brand = metadata.get("site_brand", "Hide and Seek").strip() or "Hide and Seek"

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
        next_nav = '<a href="../index.html#essays">更多文章</a>'

    indented_body = "\n".join(
        f"            {line}" if line else "" for line in body_html.splitlines()
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description, quote=True)}" />
    <link rel="stylesheet" href="../styles.css?v=2" />
  </head>
  <body class="post-page">
    <div class="page-shell">
      <header class="site-header site-header--compact">
        <div class="site-header__inner">
          <a class="site-brand" href="../index.html">{html.escape(site_brand)}</a>
          <nav class="site-nav" aria-label="Primary">
            <a href="../index.html">首页</a>
            <a href="../index.html#essays">文章</a>
            <a href="../index.html#archive">归档</a>
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
  </body>
</html>
"""


def build_one(markdown_path: Path, output_dir: Path) -> Path:
    raw = markdown_path.read_text(encoding="utf-8")
    metadata, markdown_body = parse_front_matter(raw)

    title, markdown_body = extract_title(markdown_body, metadata, markdown_path.stem)
    if "lede" not in metadata or not metadata["lede"].strip():
        metadata["lede"] = first_paragraph_text(markdown_body)

    body_html = markdown_to_html(markdown_body.strip())
    slug = sanitize_slug(metadata.get("slug", ""), markdown_path.stem)
    output_path = output_dir / f"{slug}.html"

    output_html = build_post_html(title, metadata, body_html)
    output_path.write_text(output_html, encoding="utf-8", newline="\n")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build blog post HTML files from Markdown.")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Markdown source directory (default: posts/markdown).",
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
        help="Build a single markdown file.",
    )
    return parser.parse_args()


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
        generated = build_one(target, output_dir)
        print(f"[ok] {generated.relative_to(ROOT_DIR)}")
        return 0

    if not source_dir.exists():
        print(f"[error] Source directory not found: {source_dir}")
        return 1

    markdown_files = sorted(
        path
        for path in source_dir.glob("*.md")
        if path.is_file() and not path.name.startswith("_")
    )

    if not markdown_files:
        print(f"[warn] No markdown files found in {source_dir}")
        return 0

    for md_path in markdown_files:
        generated = build_one(md_path, output_dir)
        print(f"[ok] {generated.relative_to(ROOT_DIR)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
