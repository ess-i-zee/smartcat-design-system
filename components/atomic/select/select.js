const CROSS_SVG = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.3127 3.9797C11.5079 3.78449 11.8245 3.7846 12.0197 3.9797C12.215 4.17496 12.215 4.49147 12.0197 4.68673L8.70626 7.99923L12.0197 11.3127C12.215 11.508 12.215 11.8245 12.0197 12.0197C11.8245 12.215 11.508 12.215 11.3127 12.0197L7.99923 8.70626L4.68673 12.0197C4.49147 12.215 4.17496 12.215 3.9797 12.0197C3.7846 11.8245 3.78449 11.5079 3.9797 11.3127L7.2922 7.99923L3.9797 4.68673C3.78444 4.49147 3.78444 4.17496 3.9797 3.9797C4.17496 3.78444 4.49147 3.78444 4.68673 3.9797L7.99923 7.2922L11.3127 3.9797Z" fill="currentColor" fill-opacity="0.94"/></svg>`;

document.querySelectorAll('.select').forEach(select => {
  const isMulti   = select.dataset.mode === 'multi';
  const dropdown  = select.querySelector('.select__dropdown');
  const clearBtn  = select.querySelector('.select__clear');
  const placeholder = select.querySelector('.select__placeholder');
  const valueEl   = isMulti ? null : select.querySelector('.select__value');
  const chipsEl   = isMulti ? select.querySelector('.select__chips') : null;
  const overflowEl = isMulti ? select.querySelector('.select__overflow-count') : null;

  if (!dropdown) return;

  // ── Open / close ──────────────────────────────────────────────

  function sortDropdownItems() {
    const items = [...dropdown.querySelectorAll('.dropdown-item')];
    const selected   = items.filter(i => i.dataset.state === 'selected');
    const unselected = items.filter(i => i.dataset.state !== 'selected');
    [...selected, ...unselected].forEach(item => dropdown.appendChild(item));
  }

  function open() {
    if (isMulti) sortDropdownItems();
    select.dataset.open = '';
    dropdown.hidden = false;
  }

  function close() {
    delete select.dataset.open;
    dropdown.hidden = true;
  }

  select.addEventListener('click', e => {
    if (e.target.closest('.select__clear') || e.target.closest('.input-chip__clear')) return;
    select.hasAttribute('data-open') ? close() : open();
  });

  document.addEventListener('click', e => {
    if (!select.contains(e.target)) close();
  });

  // ── Single-select: item click ─────────────────────────────────

  if (!isMulti) {
    dropdown.querySelectorAll('.dropdown-item').forEach(item => {
      item.addEventListener('click', () => {
        const label = item.querySelector('.dropdown-item__label')?.textContent ?? '';
        dropdown.querySelectorAll('.dropdown-item').forEach(i => delete i.dataset.state);
        item.dataset.state = 'selected';
        if (valueEl)    { valueEl.textContent = label; valueEl.hidden = false; }
        if (placeholder)  placeholder.hidden = true;
        if (clearBtn)     clearBtn.hidden = false;
        close();
      });
    });
  }

  // ── Multi-select: item click ──────────────────────────────────

  if (isMulti) {
    dropdown.querySelectorAll('.dropdown-item').forEach(item => {
      item.addEventListener('click', () => {
        const label = item.querySelector('.dropdown-item__label')?.textContent ?? '';
        if (item.dataset.state === 'selected') {
          delete item.dataset.state;
          removeChip(label);
        } else {
          item.dataset.state = 'selected';
          addChip(label);
        }
        syncPlaceholder();
        syncClearBtn();
        syncOverflow();
      });
    });
  }

  // ── Chip management ───────────────────────────────────────────

  function addChip(label) {
    const size = select.dataset.size || 'l';
    const chip = document.createElement('div');
    chip.className = 'input-chip';
    chip.dataset.size = size;
    chip.dataset.label = label;
    chip.innerHTML =
      `<span class="input-chip__label">${label}</span>` +
      `<button class="input-chip__clear" type="button" aria-label="Remove ${label}">${CROSS_SVG}</button>`;
    chip.querySelector('.input-chip__clear').addEventListener('click', () => {
      chip.remove();
      dropdown.querySelectorAll('.dropdown-item').forEach(i => {
        if (i.querySelector('.dropdown-item__label')?.textContent === label) delete i.dataset.state;
      });
      syncPlaceholder();
      syncClearBtn();
      syncOverflow();
    });
    chipsEl.insertBefore(chip, overflowEl);
  }

  function removeChip(label) {
    chipsEl.querySelectorAll('.input-chip').forEach(chip => {
      if (chip.dataset.label === label) chip.remove();
    });
  }

  function syncPlaceholder() {
    if (!placeholder) return;
    if (isMulti) {
      placeholder.hidden = chipsEl.querySelectorAll('.input-chip').length > 0;
    } else {
      placeholder.hidden = valueEl && !valueEl.hidden;
    }
  }

  function syncClearBtn() {
    if (!clearBtn) return;
    if (isMulti) {
      clearBtn.hidden = chipsEl.querySelectorAll('.input-chip').length === 0;
    } else {
      clearBtn.hidden = !valueEl || valueEl.hidden;
    }
  }

  // ── Overflow count ─────────────────────────────────────────────
  // Detects which chips are clipped by the chips container's overflow:hidden
  // and replaces them with a "+N" count badge. Two-pass: first pass without
  // the badge (it takes no space when hidden), second pass after badge appears
  // to catch any chip it displaces.

  function syncOverflow() {
    if (!chipsEl || !overflowEl) return;
    const chips = [...chipsEl.querySelectorAll('.input-chip')];
    chips.forEach(c => { c.hidden = false; });
    overflowEl.hidden = true;

    requestAnimationFrame(() => {
      const cRight = chipsEl.getBoundingClientRect().right;
      let hiddenCount = 0;

      for (let i = chips.length - 1; i >= 0; i--) {
        if (chips[i].getBoundingClientRect().right > cRight) {
          chips[i].hidden = true;
          hiddenCount++;
        }
      }

      if (hiddenCount === 0) return;

      overflowEl.textContent = `+${hiddenCount}`;
      overflowEl.hidden = false;

      // Badge now occupies space — check if it pushed any visible chip out
      requestAnimationFrame(() => {
        const oLeft = overflowEl.getBoundingClientRect().left;
        const visible = chips.filter(c => !c.hidden);
        for (let i = visible.length - 1; i >= 0; i--) {
          if (visible[i].getBoundingClientRect().right > oLeft) {
            visible[i].hidden = true;
            hiddenCount++;
            overflowEl.textContent = `+${hiddenCount}`;
          } else break;
        }
      });
    });
  }

  // ── Clear all ──────────────────────────────────────────────────

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (isMulti) {
        chipsEl.querySelectorAll('.input-chip').forEach(c => c.remove());
        if (overflowEl) overflowEl.hidden = true;
        dropdown.querySelectorAll('.dropdown-item').forEach(i => delete i.dataset.state);
      } else {
        if (valueEl)    { valueEl.hidden = true; valueEl.textContent = ''; }
        if (placeholder)  placeholder.hidden = false;
        dropdown.querySelectorAll('.dropdown-item').forEach(i => delete i.dataset.state);
      }
      clearBtn.hidden = true;
      if (isMulti && placeholder) placeholder.hidden = false;
    });
  }
});
