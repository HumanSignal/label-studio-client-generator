document.addEventListener('DOMContentLoaded', function() {
  const links = document.querySelectorAll('a[href^="https://humansignal.com/goenterprise"]');
  if (links.length === 0) {
    return;
  }
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

