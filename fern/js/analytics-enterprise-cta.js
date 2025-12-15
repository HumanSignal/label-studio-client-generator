// Event delegation so this works with client-side navigation / dynamically rendered content.
document.addEventListener(
  'click',
  function (event) {
    const target = event.target;
    if (!(target instanceof Element)) {
      return;
    }

    const link = target.closest('a[href^="https://humansignal.com/goenterprise"]');
    if (!link) {
    return;
  }

    // Compute an index at click-time (stable enough for analytics, and works for dynamically added links).
    const links = Array.from(
      document.querySelectorAll('a[href^="https://humansignal.com/goenterprise"]'),
    );
    const index = links.indexOf(link);

      if (typeof gtag === 'function') {
        gtag('event', 'enterprise_cta_click', {
        button_index: index >= 0 ? index : undefined,
          button_text: link.innerText || '', 
          target_url: link.href,
        page_path: window.location.pathname,
        });
      }
  },
  true,
);

