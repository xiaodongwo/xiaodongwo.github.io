"""Validate generated internal links and assets before publishing."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent / 'dist'

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links, self.ids = [], set()
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ('href', 'src', 'poster'):
            if attrs.get(name):
                self.links.append(attrs[name])

pages = {path.resolve(): Page(path) for path in ROOT.rglob('*.html')}
assert pages, 'Build the site before checking it.'
errors, checked = [], 0
for path, page in pages.items():
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = ((ROOT / unquote(url.path).lstrip('/')) if url.path.startswith('/')
                  else (path.parent / unquote(url.path)) if url.path else path)
        if target.is_dir():
            target /= 'index.html'
        target = target.resolve()
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
            errors.append(f'{path.relative_to(ROOT)}: missing {link}')
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f'{path.relative_to(ROOT)}: missing anchor {link}')
        checked += 1
for error in errors:
    print(error)
print(f'Checked {len(pages)} pages and {checked} internal links/assets; {len(errors)} errors.')
raise SystemExit(bool(errors))
