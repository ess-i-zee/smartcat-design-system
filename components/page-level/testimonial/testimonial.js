/* Testimonial carousel.
   For each multi-mode testimonial, show one slide at a time and wire the
   prev/next chevrons and the dots. Index wraps around. Single-mode
   testimonials have no pagination and are left untouched. */

document.querySelectorAll('.testimonial[data-mode="multi"]').forEach(testimonial => {
  const slides = [...testimonial.querySelectorAll('.testimonial__slide')];
  const dots   = [...testimonial.querySelectorAll('.testimonial__dot')];
  const prev   = testimonial.querySelector('.testimonial__nav--prev');
  const next   = testimonial.querySelector('.testimonial__nav--next');

  if (slides.length <= 1) return;

  let index = slides.findIndex(s => s.hasAttribute('data-active'));
  if (index < 0) index = 0;

  function show(n) {
    index = (n + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      if (i === index) slide.setAttribute('data-active', '');
      else             slide.removeAttribute('data-active');
    });
    dots.forEach((dot, i) => {
      if (i === index) dot.setAttribute('data-state', 'selected');
      else             dot.removeAttribute('data-state');
    });
  }

  if (prev) prev.addEventListener('click', () => show(index - 1));
  if (next) next.addEventListener('click', () => show(index + 1));
  dots.forEach((dot, i) => dot.addEventListener('click', () => show(i)));

  show(index);
});
