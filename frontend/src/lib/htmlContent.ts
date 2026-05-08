const ESCAPED_HTML_PATTERN =
  /&lt;\/?(p|div|span|strong|em|b|i|u|h[1-6]|ul|ol|li|br|table|thead|tbody|tr|th|td)(\s|&gt;|\/)/i;

const TABLE_TAG_PATTERN = /<table\b([^>]*)>/gi;

export function decodeEscapedProposalHtml(value: string): string {
  if (!value || !ESCAPED_HTML_PATTERN.test(value)) {
    return value || '';
  }

  const textarea = document.createElement('textarea');
  textarea.innerHTML = value;
  return textarea.value;
}

export function normalizeProposalHtml(value: string): string {
  const decoded = decodeEscapedProposalHtml(value);
  return decoded.replace(TABLE_TAG_PATTERN, (match, attrs: string) => {
    if (/class\s*=/i.test(match)) {
      return match;
    }
    return `<table class="proposal-ai-table"${attrs}>`;
  });
}
