'use client';
import React from 'react';

export function MultiLineCodeBlock({
  language,
  text,
}: {
  language?: string;
  text: string;
}) {
  const preStyle: React.CSSProperties = {
    borderRadius: 8,
    backgroundColor: '#0f172a',
    color: '#e6eef8',
    padding: '12px',
    fontSize: '0.875rem',
    lineHeight: 1.5,
    overflow: 'auto',
    whiteSpace: 'pre',
    fontFamily:
      "ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', 'Courier New', monospace",
  };

  return (
    <pre style={preStyle}>
      <code data-lang={language}>{text}</code>
    </pre>
  );
}
