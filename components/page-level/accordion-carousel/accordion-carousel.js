/* Accordion carousel — single-open accordion (desktop) / carousel (mobile).
   Activating an item expands it (collapsing the others), shows its matching
   media pane, and selects its pagination dot. Wire on DOMContentLoaded. */
(function () {
  function initAccordionCarousel(root) {
    var items  = [].slice.call(root.querySelectorAll('.accordion-carousel__item'));
    var medias = [].slice.call(root.querySelectorAll('.accordion-carousel__media-item'));
    var dots   = [].slice.call(root.querySelectorAll('.accordion-carousel__dot'));
    if (!items.length) return;

    function activate(i) {
      items.forEach(function (it, k) {
        it.setAttribute('data-state', k === i ? 'expanded' : 'default');
        it.setAttribute('aria-expanded', k === i ? 'true' : 'false');
      });
      medias.forEach(function (m, k) {
        if (k === i) m.setAttribute('data-active', ''); else m.removeAttribute('data-active');
      });
      dots.forEach(function (d, k) {
        if (k === i) d.setAttribute('data-state', 'selected'); else d.removeAttribute('data-state');
      });
    }

    items.forEach(function (it, i) { it.addEventListener('click', function () { activate(i); }); });
    dots.forEach(function (d, i) { d.addEventListener('click', function () { activate(i); }); });

    var init = items.findIndex(function (it) { return it.getAttribute('data-state') === 'expanded'; });
    activate(init < 0 ? 0 : init);
  }

  function initAll() {
    [].slice.call(document.querySelectorAll('.accordion-carousel')).forEach(initAccordionCarousel);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
