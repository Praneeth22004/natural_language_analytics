import React from 'react';
import { marked } from 'marked';

// Configure marked for clean GFM and line breaks
marked.setOptions({
  gfm: true,
  breaks: true,
});

export default function MarkdownRenderer({ content, className = '' }) {
  if (!content) return null;
  const rawHtml = marked.parse(typeof content === 'string' ? content : String(content));
  return (
    <div 
      className={`markdown-body ${className}`}
      dangerouslySetInnerHTML={{ __html: rawHtml }}
    />
  );
}
