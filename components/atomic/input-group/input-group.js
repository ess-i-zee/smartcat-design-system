/* Input group — live character counter.
   For each .input-group that has a .input-group__counter, find the wrapped
   control (Text field or Text area native element) and keep the counter in
   sync with its length. If the control has a `maxlength`, show "len/max";
   otherwise just "len". Select has no text length, so it is skipped. */

document.querySelectorAll('.input-group').forEach(group => {
  const counter = group.querySelector('.input-group__counter');
  if (!counter) return;

  const field = group.querySelector('.text-field__native, .text-area__native');
  if (!field) return;

  const max = field.getAttribute('maxlength');

  function update() {
    const len = field.value.length;
    counter.textContent = max ? `${len}/${max}` : `${len}`;
  }

  field.addEventListener('input', update);
  update();
});
