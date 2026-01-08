// Initialize Mermaid diagrams
document$.subscribe(() => {
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default'
  });

  // Handle theme switching
  const observer = new MutationObserver(() => {
    const isDark = document.body.getAttribute('data-md-color-scheme') === 'slate';
    mermaid.initialize({
      startOnLoad: true,
      theme: isDark ? 'dark' : 'default'
    });
    // Re-render all mermaid diagrams
    if (typeof mermaid !== 'undefined') {
      mermaid.contentLoaded();
    }
  });

  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['data-md-color-scheme']
  });
});
