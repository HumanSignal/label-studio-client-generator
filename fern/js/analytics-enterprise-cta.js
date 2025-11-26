console.log('[enterprise-cta] custom JS loaded', window.location.href);
window.__ENTERPRISE_CTA_LOADED__ = true;

(function () {
  const MEASUREMENT_ID = 'G-326708547';

  function loadGaScriptOnce() {
    try {
      const existing = document.querySelector('script[data-ga4-loaded]');
      if (existing) {
        console.log('[enterprise-cta] GA script already present', existing.src);
        return;
      }

      const head =
        document.head ||
        document.getElementsByTagName('head')[0] ||
        document.documentElement;

      if (!head) {
        console.warn('[enterprise-cta] no <head> element found, cannot load GA');
        return;
      }

      const s = document.createElement('script');
      s.async = true;
      s.src = `https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`;
      s.setAttribute('data-ga4-loaded', 'true');

      s.onload = () => {
        console.log('[enterprise-cta] GA4 script loaded OK', s.src);
      };

      s.onerror = (e) => {
        console.error('[enterprise-cta] GA4 script FAILED to load', e);
      };

      head.appendChild(s);
      console.log('[enterprise-cta] GA4 script tag appended', s.src);
    } catch (err) {
      console.error('[enterprise-cta] loadGaScriptOnce threw', err);
    }
  }

  // Make sure we only run after DOM is at least partially ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadGaScriptOnce);
  } else {
    loadGaScriptOnce();
  }

  // --- Enterprise CTA tracking ---

  document.addEventListener('DOMContentLoaded', function () {
    const links = document.querySelectorAll(
      'a[href^="https://humansignal.com/goenterprise"]'
    );
    console.log('[enterprise-cta] found enterprise links:', links.length);

    if (!links.length) return;

    links.forEach((link, index) => {
      link.addEventListener('click', function () {
        console.log('[enterprise-cta] click on enterprise link', {
          index,
          href: link.href,
          gtagType: typeof gtag
        });

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

