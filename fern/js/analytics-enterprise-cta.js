console.log('[enterprise-cta] custom JS loaded', window.location.href);
window.__ENTERPRISE_CTA_LOADED__ = true;


(function() {
  
  // help fern load GA library
  
  const MEASUREMENT_ID = 'G-326708547';

  function loadGaScriptOnce() {
    if (document.querySelector('script[data-ga4-loaded]')) return;

    const s = document.createElement('script');
    s.async = true;
    s.src = `https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`;
    s.setAttribute('data-ga4-loaded', 'true');
    document.head.appendChild(s);
  }

  loadGaScriptOnce();

  // add tracking for enterprise CTA

  document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll(
      'a[href^="https://humansignal.com/goenterprise"]'
    );
    if (!links.length) return;

    links.forEach((link, index) => {
      link.addEventListener('click', function() {
        if (typeof gtag === 'function') {
          gtag('event', 'enterprise_cta_click', {
            button_index: index + 1,
            button_text: link.innerText || '',
            target_url: link.href,
            page_path: window.location.pathname
          });
        }
      });
    });
  });
})();
