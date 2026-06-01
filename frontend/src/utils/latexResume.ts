import type { TailoredBullet, TailoredSkill } from "../types/tailor";

export type LatexResumeItem = {
  itemEnd?: number;
  itemStart?: number;
  text: string;
};

export type LatexResumeEntry = {
  id: string;
  kind: "experience" | "project";
  section: string;
  title: string;
  organization?: string;
  detail?: string;
  date?: string;
  location?: string;
  technologies?: string;
  itemListEnd?: number;
  items: LatexResumeItem[];
};

export type LatexResumeSection = {
  title: string;
  entries: LatexResumeEntry[];
  skills?: LatexSkillGroup[];
};

export type LatexResumeHeading = {
  name?: string;
  contacts: string[];
};

export type LatexSkillGroup = {
  label: string;
  skills: LatexSkillValue[];
  value: string;
  valueEnd?: number;
  valueStart?: number;
};

export type LatexSkillValue = {
  end: number;
  start: number;
  text: string;
};

export type ParsedLatexResume = {
  sections: LatexResumeSection[];
  entries: LatexResumeEntry[];
  heading: LatexResumeHeading;
  hasResumeMacros: boolean;
};

type BracedGroup = {
  content: string;
  end: number;
};

export function parseLatexResume(latex: string): ParsedLatexResume {
  const sectionMatches = [...latex.matchAll(/\\section\{([^}]*)\}/g)];
  const heading = parseHeading(latex);
  const sections: LatexResumeSection[] = [];
  const entries: LatexResumeEntry[] = [];

  sectionMatches.forEach((match, index) => {
    const sectionStart = match.index ?? 0;
    const contentStart = sectionStart + match[0].length;
    const sectionEnd = sectionMatches[index + 1]?.index ?? latex.length;
    const title = cleanLatexText(match[1]);
    const sectionEntries = parseEntriesInRange(latex, title, contentStart, sectionEnd);
    const skills = normalizeText(title) === "technical skills" ? parseTechnicalSkills(latex.slice(contentStart, sectionEnd), contentStart) : undefined;
    sections.push({ title, entries: sectionEntries, skills });
    entries.push(...sectionEntries);
  });

  return {
    sections,
    entries,
    heading,
    hasResumeMacros: /\\resume(Subheading|ProjectHeading|Item)\b/.test(latex),
  };
}

export function findBestLatexEntry(parsed: ParsedLatexResume, bullet: TailoredBullet): LatexResumeEntry | undefined {
  const sectionHint = normalizeText(bullet.placement.section);
  const entryHint = normalizeText(bullet.placement.entry);

  let best: { entry: LatexResumeEntry; score: number } | undefined;

  for (const entry of parsed.entries) {
    let score = 0;
    const section = normalizeText(entry.section);
    const title = normalizeText(entry.title);
    const organization = normalizeText(entry.organization ?? "");
    const detail = normalizeText(entry.detail ?? entry.technologies ?? "");
    const combined = `${title} ${organization} ${detail}`;

    if (sectionHint && section.includes(sectionHint)) {
      score += 4;
    }
    if (sectionHint.includes("experience") && entry.kind === "experience") {
      score += 3;
    }
    if (sectionHint.includes("project") && entry.kind === "project") {
      score += 3;
    }
    if (entryHint && (combined.includes(entryHint) || entryHint.includes(title))) {
      score += 7;
    }
    if (entryHint.includes("olei") && combined.includes("olei")) {
      score += 8;
    }
    if (entryHint.includes("sentimentscope") && title.includes("sentimentscope")) {
      score += 8;
    }
    if (entryHint.includes("resumerag") && title.includes("resumerag")) {
      score += 8;
    }
    if (entryHint.includes("fairshare") && title.includes("fairshare")) {
      score += 8;
    }

    const overlap = tokenOverlap(entryHint, combined);
    score += overlap;

    if (!best || score > best.score) {
      best = { entry, score };
    }
  }

  return best && best.score >= 4 ? best.entry : undefined;
}

export function findFallbackLatexEntry(parsed: ParsedLatexResume, bullet?: TailoredBullet): LatexResumeEntry | undefined {
  const experienceEntries = parsed.entries.filter((entry) => entry.kind === "experience" || normalizeText(entry.section).includes("experience"));
  const candidates = experienceEntries.length > 0 ? experienceEntries : parsed.entries;
  if (candidates.length === 0) {
    return undefined;
  }

  if (!bullet) {
    return candidates[0];
  }

  const bulletText = normalizeText(bullet.bullet);
  let best: { entry: LatexResumeEntry; score: number } | undefined;
  for (const entry of candidates) {
    const entryText = normalizeText(
      [
        entry.section,
        entry.title,
        entry.organization,
        entry.detail,
        entry.technologies,
        ...entry.items.map((item) => item.text),
      ]
        .filter(Boolean)
        .join(" "),
    );
    const score = tokenOverlap(bulletText, entryText);
    if (!best || score > best.score) {
      best = { entry, score };
    }
  }

  return best && best.score >= 2 ? best.entry : candidates[0];
}

export function insertResumeItem(latex: string, entry: LatexResumeEntry, bulletText: string): string {
  if (entry.itemListEnd === undefined) {
    return latex;
  }

  const lineStart = latex.lastIndexOf("\n", entry.itemListEnd) + 1;
  const existingIndent = latex.slice(lineStart, entry.itemListEnd).match(/^\s*/)?.[0] ?? "      ";
  const itemIndent = existingIndent.length >= 2 ? `${existingIndent}  ` : "        ";
  const insertion = `${itemIndent}\\resumeItem{${escapeLatex(bulletText)}}\n`;

  return `${latex.slice(0, entry.itemListEnd)}${insertion}${latex.slice(entry.itemListEnd)}`;
}

export function findClosestLatexItem(entry: LatexResumeEntry, bulletText: string): LatexResumeItem | undefined {
  const bullet = normalizeText(bulletText);
  let best: { item: LatexResumeItem; score: number } | undefined;

  for (const item of entry.items) {
    if (item.itemStart === undefined || item.itemEnd === undefined) {
      continue;
    }

    const itemText = normalizeText(item.text);
    let score = tokenOverlap(bullet, itemText);

    if (bullet.includes(itemText) || itemText.includes(bullet)) {
      score += 8;
    }

    if (!best || score > best.score) {
      best = { item, score };
    }
  }

  return best && best.score >= 2 ? best.item : undefined;
}

export function replaceResumeItem(latex: string, item: LatexResumeItem, bulletText: string): string {
  if (item.itemStart === undefined || item.itemEnd === undefined) {
    return latex;
  }

  const replacement = `\\resumeItem{${escapeLatex(bulletText)}}`;
  return `${latex.slice(0, item.itemStart)}${replacement}${latex.slice(item.itemEnd)}`;
}

export function findBestLatexSkillGroup(parsed: ParsedLatexResume, skill: TailoredSkill): LatexSkillGroup | undefined {
  const targetCategory = normalizeText(skill.category);
  const technicalSkills = parsed.sections.find((section) => normalizeText(section.title) === "technical skills")?.skills ?? [];

  return technicalSkills.find((group) => normalizeText(group.label) === targetCategory);
}

export function skillExistsInGroup(group: LatexSkillGroup, skillName: string): boolean {
  const normalizedSkill = normalizeText(skillName);
  return group.skills.some((skill) => normalizeText(skill.text) === normalizedSkill);
}

export function addLatexSkill(latex: string, group: LatexSkillGroup, skillName: string): string {
  if (group.valueEnd === undefined || skillExistsInGroup(group, skillName)) {
    return latex;
  }

  const separator = group.value.trim() ? ", " : "";
  const insertion = `${separator}${escapeLatex(skillName)}`;
  return `${latex.slice(0, group.valueEnd)}${insertion}${latex.slice(group.valueEnd)}`;
}

export function findLeastRelevantLatexSkill(group: LatexSkillGroup, protectedSkillNames: string[]): LatexSkillValue | undefined {
  const protectedSkills = new Set(protectedSkillNames.map(normalizeText));
  const replaceable = group.skills.filter((skill) => !protectedSkills.has(normalizeText(skill.text)));
  return replaceable[replaceable.length - 1] ?? group.skills[group.skills.length - 1];
}

export function replaceLatexSkill(latex: string, target: LatexSkillValue, skillName: string): string {
  return `${latex.slice(0, target.start)}${escapeLatex(skillName)}${latex.slice(target.end)}`;
}

export function escapeLatex(text: string): string {
  const replacements: Record<string, string> = {
    "\\": "\\textbackslash{}",
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircum{}",
    "&": "\\&",
    "%": "\\%",
    "$": "\\$",
    "#": "\\#",
    "_": "\\_",
    "{": "\\{",
    "}": "\\}",
  };

  return text.replace(/[\\~^&%$#_{}]/g, (match) => replacements[match]);
}

function parseEntriesInRange(latex: string, section: string, start: number, end: number): LatexResumeEntry[] {
  const entries: LatexResumeEntry[] = [];
  const sectionText = latex.slice(start, end);
  const macroRegex = /\\(resumeSubheading|resumeProjectHeading)\b/g;
  let match: RegExpExecArray | null;

  while ((match = macroRegex.exec(sectionText)) !== null) {
    const macroStart = start + match.index;
    const macroName = match[1];
    const parsed = macroName === "resumeSubheading"
      ? parseSubheading(latex, section, macroStart, end)
      : parseProjectHeading(latex, section, macroStart, end);

    if (parsed) {
      entries.push(parsed);
    }
  }

  return entries;
}

function parseHeading(latex: string): LatexResumeHeading {
  const centerMatch = latex.match(/\\begin\{center\}([\s\S]*?)\\end\{center\}/);
  if (!centerMatch) {
    return { contacts: [] };
  }

  const lines = centerMatch[1]
    .split(/\\\\/)
    .map(cleanLatexText)
    .map((line) => line.replace(/^small\s+/, "").trim())
    .filter(Boolean);

  const [name, ...contactLines] = lines;
  const contacts = contactLines
    .join(" | ")
    .split("|")
    .map((part) => part.trim())
    .filter(Boolean);

  return { name, contacts };
}

function parseTechnicalSkills(sectionText: string, baseOffset: number): LatexSkillGroup[] {
  return [...sectionText.matchAll(/\\textbf\{([^{}]+)\}\{:\s*([^{}]*)\}/g)]
    .map((match) => {
      const rawValue = match[2];
      const valueStartInMatch = match[0].lastIndexOf(rawValue);
      const valueStart = baseOffset + (match.index ?? 0) + valueStartInMatch;
      const valueEnd = valueStart + rawValue.length;
      return {
        label: cleanLatexText(match[1]),
        skills: parseSkillValues(rawValue, valueStart),
        value: cleanLatexText(rawValue),
        valueEnd,
        valueStart,
      };
    })
    .filter((skill) => skill.label && skill.value);
}

function parseSkillValues(rawValue: string, valueStart: number): LatexSkillValue[] {
  const skills: LatexSkillValue[] = [];
  const regex = /[^,]+/g;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(rawValue)) !== null) {
    const rawSkill = match[0];
    const leadingWhitespace = rawSkill.match(/^\s*/)?.[0].length ?? 0;
    const trailingWhitespace = rawSkill.match(/\s*$/)?.[0].length ?? 0;
    const start = valueStart + match.index + leadingWhitespace;
    const end = valueStart + match.index + rawSkill.length - trailingWhitespace;
    const text = cleanLatexText(rawSkill);
    if (text) {
      skills.push({ end, start, text });
    }
  }

  return skills;
}

function parseSubheading(latex: string, section: string, macroStart: number, sectionEnd: number): LatexResumeEntry | undefined {
  const parsed = parseMacroArgs(latex, macroStart + "\\resumeSubheading".length, 4);
  if (!parsed) {
    return undefined;
  }

  const [title, date, organization, location] = parsed.args.map(cleanLatexText);
  const list = parseItemList(latex, parsed.end, sectionEnd);
  return {
    id: `${section}:${title}:${organization}`,
    kind: "experience",
    section,
    title,
    organization,
    date,
    location,
    itemListEnd: list.itemListEnd,
    items: list.items,
  };
}

function parseProjectHeading(latex: string, section: string, macroStart: number, sectionEnd: number): LatexResumeEntry | undefined {
  const parsed = parseMacroArgs(latex, macroStart + "\\resumeProjectHeading".length, 2);
  if (!parsed) {
    return undefined;
  }

  const heading = cleanLatexText(parsed.args[0]);
  const [title, ...detailParts] = heading.split("|").map((part) => part.trim()).filter(Boolean);
  const list = parseItemList(latex, parsed.end, sectionEnd);

  return {
    id: `${section}:${title}:${detailParts.join(" ")}`,
    kind: "project",
    section,
    title: title || "Untitled project",
    detail: detailParts.join(" | "),
    technologies: detailParts.join(" | "),
    date: cleanLatexText(parsed.args[1]),
    itemListEnd: list.itemListEnd,
    items: list.items,
  };
}

function parseMacroArgs(latex: string, start: number, count: number): { args: string[]; end: number } | undefined {
  const args: string[] = [];
  let cursor = start;

  for (let index = 0; index < count; index += 1) {
    cursor = skipWhitespace(latex, cursor);
    const group = parseBracedGroup(latex, cursor);
    if (!group) {
      return undefined;
    }
    args.push(group.content);
    cursor = group.end;
  }

  return { args, end: cursor };
}

function parseItemList(latex: string, start: number, sectionEnd: number): { items: LatexResumeItem[]; itemListEnd?: number } {
  const listStartMarker = "\\resumeItemListStart";
  const listEndMarker = "\\resumeItemListEnd";
  const listStart = latex.indexOf(listStartMarker, start);

  if (listStart < 0 || listStart >= sectionEnd) {
    return { items: [] };
  }

  const contentStart = listStart + listStartMarker.length;
  const itemListEnd = latex.indexOf(listEndMarker, contentStart);
  if (itemListEnd < 0 || itemListEnd >= sectionEnd) {
    return { items: [] };
  }

  const items: LatexResumeItem[] = [];
  let cursor = contentStart;

  while (cursor < itemListEnd) {
    const itemStart = latex.indexOf("\\resumeItem", cursor);
    if (itemStart < 0 || itemStart >= itemListEnd) {
      break;
    }

    const group = parseBracedGroup(latex, itemStart + "\\resumeItem".length);
    if (!group) {
      cursor = itemStart + "\\resumeItem".length;
      continue;
    }

    items.push({
      itemEnd: group.end,
      itemStart,
      text: cleanLatexText(group.content),
    });
    cursor = group.end;
  }

  return { items, itemListEnd };
}

function parseBracedGroup(text: string, start: number): BracedGroup | undefined {
  const open = skipWhitespace(text, start);
  if (text[open] !== "{") {
    return undefined;
  }

  let depth = 0;
  for (let index = open; index < text.length; index += 1) {
    const char = text[index];
    const previous = text[index - 1];
    if (char === "{" && previous !== "\\") {
      depth += 1;
    } else if (char === "}" && previous !== "\\") {
      depth -= 1;
      if (depth === 0) {
        return {
          content: text.slice(open + 1, index),
          end: index + 1,
        };
      }
    }
  }

  return undefined;
}

function skipWhitespace(text: string, start: number): number {
  let cursor = start;
  while (cursor < text.length && /\s/.test(text[cursor])) {
    cursor += 1;
  }
  return cursor;
}

function cleanLatexText(value: string): string {
  let text = value
    .replace(/\\(?:vspace|hspace)\*?(?:\[[^\]]*\])?\{[^{}]*\}/g, " ")
    .replace(/\\\(|\\\)/g, "")
    .replace(/\$\\?\|\$/g, " | ");
  let previous = "";

  while (previous !== text) {
    previous = text;
    text = text
      .replace(/\\href\{[^{}]*\}\{([^{}]*)\}/g, "$1")
      .replace(/\\(?:textbf|emph|underline|textit|small|scshape)\{([^{}]*)\}/g, "$1");
  }

  return text
    .replace(/\\textasciitilde\{\}/g, "~")
    .replace(/\\textasciicircum\{\}/g, "^")
    .replace(/\\textbackslash\{\}\s*[()]?/g, "")
    .replace(/\\&/g, "&")
    .replace(/\\%/g, "%")
    .replace(/\\_/g, "_")
    .replace(/\\#/g, "#")
    .replace(/\\\$/g, "$")
    .replace(/\\\{/g, "{")
    .replace(/\\\}/g, "}")
    .replace(/\s*\|\s*/g, " | ")
    .replace(/\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?/g, " ")
    .replace(/[{}]/g, "")
    .replace(/\s+/g, " ")
    .replace(/\s+([,.;:%])/g, "$1")
    .trim();
}

function normalizeText(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9+#]+/g, " ").replace(/\s+/g, " ").trim();
}

function tokenOverlap(left: string, right: string): number {
  const leftTokens = new Set(left.split(" ").filter((token) => token.length >= 3));
  const rightTokens = new Set(right.split(" ").filter((token) => token.length >= 3));
  let overlap = 0;

  leftTokens.forEach((token) => {
    if (rightTokens.has(token)) {
      overlap += 1;
    }
  });

  return overlap;
}
