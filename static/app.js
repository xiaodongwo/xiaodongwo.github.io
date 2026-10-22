// Progressive enhancement: all pages and navigation work without JavaScript.
document.querySelectorAll('.nav-dropdown').forEach(dropdown => {
  document.addEventListener('click', event => {
    if (!dropdown.contains(event.target)) dropdown.open = false;
  });
  dropdown.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      dropdown.open = false;
      dropdown.querySelector('summary').focus();
    }
  });
});

const filters = [...document.querySelectorAll('[data-filter]')];
filters.forEach(button => button.addEventListener('click', () => {
  const selected = button.dataset.filter;
  filters.forEach(item => {
    item.classList.toggle('selected', item === button);
    item.setAttribute('aria-pressed', String(item === button));
  });
  let count = 0;
  document.querySelectorAll('.publication').forEach(paper => {
    paper.hidden = selected !== 'All' && paper.dataset.type !== selected;
    if (!paper.hidden) count += 1;
  });
  document.querySelectorAll('.year-group').forEach(group => {
    group.hidden = !group.querySelector('.publication:not([hidden])');
  });
  document.querySelector('.filter-status').textContent = `${count} ${count === 1 ? 'entry' : 'entries'}`;
}));

const performances = [...document.querySelectorAll('.magic-video')];
performances.forEach(video => video.addEventListener('play', () => {
  performances.forEach(other => {
    if (other !== video) other.pause();
  });
}));
