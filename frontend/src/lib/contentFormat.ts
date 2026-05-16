const escapeHtml = (value: string) =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const inlineMarkdownToHtml = (value: string) =>
  escapeHtml(value)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');

const isSeparatorRow = (line: string) =>
  /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);

const isTableRow = (line: string) => {
  const trimmed = line.trim();
  return trimmed.includes('|') && trimmed.split('|').filter((cell) => cell.trim()).length >= 2;
};

const tableRowCells = (line: string) =>
  line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => inlineMarkdownToHtml(cell.trim()));

const tableToHtml = (rows: string[]) => {
  const dataRows = rows.filter((row) => !isSeparatorRow(row));
  if (!dataRows.length) return '';
  const [head, ...body] = dataRows;
  const headerCells = tableRowCells(head);
  const bodyRows = body.map((row) => tableRowCells(row));

  return [
    '<table><thead><tr>',
    headerCells.map((cell) => `<th>${cell}</th>`).join(''),
    '</tr></thead><tbody>',
    bodyRows
      .map((cells) => `<tr>${cells.map((cell) => `<td>${cell}</td>`).join('')}</tr>`)
      .join(''),
    '</tbody></table>',
  ].join('');
};

export function markdownToEditorHtml(markdown: string) {
  const source = (markdown || '').trim();
  if (!source) return '';
  if (/<(p|h[1-6]|ul|ol|li|table|div|strong|em|br)\b/i.test(source)) return source;

  const lines = source.replace(/\r\n/g, '\n').split('\n');
  const blocks: string[] = [];
  let paragraph: string[] = [];
  let list: string[] = [];
  let table: string[] = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push(`<p>${inlineMarkdownToHtml(paragraph.join(' '))}</p>`);
      paragraph = [];
    }
  };
  const flushList = () => {
    if (list.length) {
      blocks.push(`<ul>${list.map((item) => `<li>${inlineMarkdownToHtml(item)}</li>`).join('')}</ul>`);
      list = [];
    }
  };
  const flushTable = () => {
    if (table.length) {
      blocks.push(tableToHtml(table));
      table = [];
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      flushList();
      flushTable();
      continue;
    }
    if (isTableRow(trimmed) || (table.length && isSeparatorRow(trimmed))) {
      flushParagraph();
      flushList();
      table.push(trimmed);
      continue;
    }
    flushTable();

    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = Math.min(heading[1].length, 3);
      blocks.push(`<h${level}>${inlineMarkdownToHtml(heading[2])}</h${level}>`);
      continue;
    }

    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      flushParagraph();
      list.push(bullet[1]);
      continue;
    }

    flushList();
    paragraph.push(trimmed);
  }

  flushParagraph();
  flushList();
  flushTable();
  return blocks.filter(Boolean).join('');
}

export function shouldNormalizeMarkdown(content: string) {
  const value = (content || '').trim();
  if (!value || /<[^>]+>/.test(value)) return false;
  return /\*\*[^*]+\*\*/.test(value) || /^\s*\|.+\|\s*$/m.test(value) || /^[-*]\s+\S+/m.test(value);
}
