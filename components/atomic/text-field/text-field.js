document.querySelectorAll('.text-field').forEach(field => {
  const input = field.querySelector('.text-field__native');
  const clear = field.querySelector('.text-field__clear');
  if (!input || !clear) return;

  const sync = () => { clear.hidden = !input.value; };

  input.addEventListener('input', sync);
  clear.addEventListener('click', () => {
    input.value = '';
    input.focus();
    sync();
  });

  sync();
});
