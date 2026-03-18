import { useState, useEffect } from 'react';

export function useTheme(): 'light' | 'dark' {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof document === 'undefined') {
      return 'dark'; // Default to dark in SSR
    }

    return document.documentElement.getAttribute('data-theme') === 'light'
      ? 'light'
      : 'dark';
  });

  useEffect(() => {
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (
          mutation.type === 'attributes' &&
          mutation.attributeName === 'data-theme'
        ) {
          const newTheme =
            document.documentElement.getAttribute('data-theme') === 'light'
              ? 'light'
              : 'dark';
          setTheme(newTheme);
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });

    return () => observer.disconnect();
  }, []);

  return theme;
}
