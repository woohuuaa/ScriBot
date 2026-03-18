'use client';
import React, { useState } from 'react';

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch (e) {
      // fall back to older approach
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'absolute';
      textarea.style.left = '-9999px';
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand('copy');
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1500);
      } catch (err) {
        // ignore
      }
      document.body.removeChild(textarea);
    }
  };

  const baseStyle: React.CSSProperties = {
    borderRadius: 6,
    padding: '6px 10px',
    fontSize: '0.875rem',
    transition: 'background-color 150ms ease',
    border: 'none',
    cursor: 'pointer',
  };

  const copiedStyle: React.CSSProperties = {
    backgroundColor: '#2563eb',
    color: 'white',
  };

  const defaultStyle: React.CSSProperties = {
    backgroundColor: 'rgba(0,0,0,0.05)',
    color: 'inherit',
  };

  return (
    <button
      onClick={handleCopy}
      style={{ ...baseStyle, ...(copied ? copiedStyle : defaultStyle) }}
      title={copied ? 'Gekopieerd' : 'Kopiëren'}
      aria-label={copied ? 'Gekopieerd' : 'Kopiëren'}
    >
      {copied ? '✓' : 'Kopieer'}
    </button>
  );
}
