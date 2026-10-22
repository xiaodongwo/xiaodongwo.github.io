"""Build a portable, static website from editable JSON and Markdown content."""
import html
import filecmp
import json
import re
import shutil
import stat
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import markdown
import yaml

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
OUT.mkdir(exist_ok=True)

def copy_static(source, destination):
    target = Path(destination)
    if target.is_file():
        # Media copied from user folders may retain the read-only attribute.
        if filecmp.cmp(source, destination, shallow=False):
            return destination
        if not target.resolve().is_relative_to(OUT.resolve()):
            raise ValueError('Static asset destination must stay inside dist.')
        target.chmod(target.stat().st_mode | stat.S_IWRITE)
    return shutil.copy2(source, destination)

shutil.copytree(ROOT / 'static', OUT, dirs_exist_ok=True, copy_function=copy_static)
load = lambda name: json.loads((ROOT / 'content' / name).read_text(encoding='utf-8'))
PROFILE, PAPERS, NEWS, TALKS = [load(n) for n in ['profile.json','papers.json','news.json','talks.json']]
SELECTED = [next(p for p in PAPERS if p['id'] == key) for key in load('home-selection.json')]
esc = lambda s: html.escape(str(s), quote=True)
url = lambda s: quote(s, safe='/:?=&%#@+~')

def md(text):
    return markdown.markdown(text, extensions=['extra', 'sane_lists'])

def icon(name):
    paths = {
        'cv':'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
        'scholar':'<path d="m2 9 10-5 10 5-10 5-10-5zM6 11v6c4 3 8 3 12 0v-6M22 9v8"/>',
        'researchgate':'<text x="2" y="20" fill="currentColor" stroke="none" font-family="Georgia,serif" font-size="21">R</text><text x="15" y="10" fill="currentColor" stroke="none" font-family="Georgia,serif" font-size="10">G</text>',
        'github':'<path d="M9 19c-4 1-4-2-6-2m12 5v-4a3.5 3.5 0 0 0-1-2.7c3.3-.4 6.8-1.6 6.8-7.3a5.7 5.7 0 0 0-1.5-4 5.3 5.3 0 0 0-.1-4s-1.3-.4-4.2 1.5a14.3 14.3 0 0 0-7.6 0C4.5-.4 3.2 0 3.2 0a5.3 5.3 0 0 0-.1 4 5.7 5.7 0 0 0-1.5 4c0 5.7 3.5 6.9 6.8 7.3A3.5 3.5 0 0 0 7.5 18v4" transform="translate(2 1) scale(.85)"/>',
        'email':'<rect x="3" y="5" width="18" height="14" rx="1"/><path d="m3 6 9 7 9-7"/>',
        'arrow':'<path d="M5 12h14m-5-5 5 5-5 5"/>',
        'chevron':'<path d="m6 9 6 6 6-6"/>',
        'download':'<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/>'
    }
    return f'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'

def nav(active):
    links = ''.join(f'<a href="{href}" class="nav-link{" current" if active == text else ""}"'+(' aria-current="page"' if active == text else '')+f'>{text}</a>' for text,href in [('Home','/'),('CV',PROFILE['cv']),('Papers','/papers/')])
    return f'''<header class="site-header"><nav class="main-nav" aria-label="Main navigation">{links}
    <details class="nav-dropdown"><summary class="nav-link{' current' if active == 'Blogs' else ''}">Blogs {icon('chevron')}</summary>
    <div class="dropdown-content"><a href="/blogs/">All blogs</a><a href="/blogs/magic/">Magic</a><a href="/blogs/movie/">Movie</a><a href="/blogs/thoughts/">Thoughts</a></div></details>
    </nav></header>'''

def page(title, content, active='Home', cls='', description=None, extra_head=''):
    description = description or 'Xiaodong Wang — computational photography, computer vision, and physics-based imaging.'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Xiaodong Wang</title><meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="light"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/fonts/fonts.css"><link rel="stylesheet" href="/styles.css">
<script src="/app.js" defer></script>{extra_head}</head>
<body class="{cls}"><a class="skip-link" href="#main">Skip to content</a>{nav(active)}
<main id="main" class="site-main">{content}</main>
<footer class="site-footer"><span>Xiaodong Wang</span><div><a href="mailto:{PROFILE['email']}">Email</a><a href="{PROFILE['scholar']}">Scholar</a><a href="{PROFILE['github']}">GitHub</a></div></footer>
</body></html>'''

def write(route, data):
    dest = OUT / route.strip('/') / 'index.html' if route != '404.html' else OUT / route
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(data, encoding='utf-8')

def resources(links):
    return ' '.join(f'<a class="resource" href="{esc(url(href))}">{esc(label[:1].upper() + label[1:])}</a>' for label,href in links.items())

def paper_title(p, full=False):
    target = p['links'].get('pdf')
    if target:
        return f'<a class="paper-title" href="{esc(url(target))}">{esc(p["title"])}</a>'
    if not full:
        return f'<a class="paper-title" href="/papers/#{p["id"]}">{esc(p["title"])}</a>'
    return f'<span class="paper-title unlinked">{esc(p["title"])}</span>'

def compact_paper(p):
    note = p['note']
    if 'under review' in note.lower() or 'accepted' in note.lower():
        status = note
    else:
        status = 'Preprint' if p['type'] == 'Preprint' else ''
        if note and not note.startswith('*'): status = ' · '.join(filter(None, [status, note]))
    venue = p['venue'] if p['type'] == 'Journal' else p['abbr']
    meta = f'<span title="{esc(p["venue"])}">{esc(venue)}</span>'
    if status: meta += f' · {esc(status)}'
    return f'<li class="timeline-row"><span class="date">{p["year"]}</span><div><div class="compact-title">{paper_title(p)}</div><p class="compact-meta">{meta}</p></div></li>'

def talk_rows():
    rows = []
    for talk in TALKS:
        title = esc(talk['title'])
        if talk['links']:
            target = next(iter(talk['links'].values()))
            title = f'<a class="talk-title" href="{esc(url(target))}">{title}</a>'
        else:
            title = f'<span class="talk-title">{title}</span>'
        date = datetime.strptime(talk['date'], '%Y-%m').strftime('%Y %b')
        rows.append(f'<li class="timeline-row"><time class="date" datetime="{talk["date"]}">{date}</time><div>{title} <span class="talk-resources">{resources(talk["links"])}</span><p class="row-description">{esc(talk["event"])} · {esc(talk["kind"])}</p></div></li>')
    return ''.join(rows)

socials = [('ResearchGate','researchgate',PROFILE['researchgate']),('Scholar','scholar',PROFILE['scholar']),('GitHub','github',PROFILE['github']),('Email','email','mailto:'+PROFILE['email'])]
social_html = ''.join(f'<a href="{esc(href)}">{icon(i)}<span>{name}</span></a>' for name,i,href in socials)
home = f'''<section class="profile" aria-labelledby="intro-title">
<img class="portrait" src="{PROFILE['photo']}" alt="Xiaodong Wang" width="224" height="224" fetchpriority="high">
<div class="profile-text"><h1 id="intro-title">Hello, I'm Xiaodong Wang</h1>
{md(PROFILE['intro'])}{md(PROFILE['background'])}
<p class="opportunities">{esc(PROFILE['opportunities'])}</p>
<div class="social-links" aria-label="Contact and academic profiles">{social_html}</div></div></section>
<div class="editorial">
<section class="home-section" aria-labelledby="papers-heading"><div class="section-heading"><h2 id="papers-heading">Papers</h2><a class="quiet-link" href="/papers/">All papers {icon('arrow')}</a></div>
<ul class="timeline paper-list">{''.join(compact_paper(p) for p in SELECTED)}</ul></section>
<section class="home-section" aria-labelledby="talks-heading"><h2 id="talks-heading">Talks &amp; Media</h2><ul class="timeline talks-list">{talk_rows()}</ul></section>
</div>'''
write('/', page('Home', home, cls='home-page'))

def authors_html(authors):
    return ', '.join(f'<strong>{esc(a)}</strong>' if 'Xiaodong Wang' in a else esc(a) for a in authors)

def full_paper(p):
    notes = f' · <span class="paper-note">{esc(p["note"])}</span>' if p['note'] else ''
    links = {('paper' if k == 'pdf' else k):v for k,v in p['links'].items()}
    if p['id'] == 'wang2025plug': links['blog']='/blogs/thoughts/diffusion-models/'
    return f'''<li class="publication" id="{p['id']}" data-type="{p['type']}"><h3>{paper_title(p, True)}</h3>
    <p class="authors">{authors_html(p['authors'])}</p><p class="venue">{esc(p['venue'])}, {p['year']}{notes}</p><p class="publication-links">{resources(links)}</p></li>'''

years = sorted({p['year'] for p in PAPERS}, reverse=True)
filters = [('All','All'),('Conference','Conference'),('Journal','Journal'),('Preprint','Preprints & manuscripts'),('Thesis','Thesis')]
filter_html = ''.join(f'<button type="button" class="filter-button{" selected" if key == "All" else ""}" data-filter="{key}" aria-pressed="{"true" if key == "All" else "false"}">{label}</button>' for key,label in filters)
groups = ''.join(f'<section class="year-group" data-year="{y}"><h2>{y}</h2><ul class="publications">'+''.join(full_paper(p) for p in PAPERS if p['year']==y)+'</ul></section>' for y in years)
papers_page = f'''<div class="page-content"><header class="page-title"><h1>Papers</h1><p>Publications, manuscripts, and thesis.</p><a class="quiet-link" href="{PROFILE['scholar']}">Google Scholar {icon('arrow')}</a></header>
<div class="paper-filters" aria-label="Filter publications">{filter_html}</div><p class="filter-status" role="status" aria-live="polite">{len(PAPERS)} entries</p>{groups}</div>'''
write('/papers/', page('Papers', papers_page, active='Papers'))

CATEGORIES = {'Magic': 'Practice, performance, and the pleasure of surprise.', 'Movie': 'Films, images, editing, and sound.', 'Thoughts': 'Research notes, reflections, and life along the way.'}
MAGIC_VIDEOS = load('magic-videos.json')
posts = []
for path in sorted((ROOT/'content/posts').glob('*.md')):
    _, raw_meta, body = path.read_text(encoding='utf-8').split('---',2)
    meta = yaml.safe_load(raw_meta)
    if meta.get('draft'): continue
    assert meta['category'] in CATEGORIES, f'Unknown blog category in {path.name}'
    meta['route'] = f'/blogs/{meta["category"].lower()}/{meta["slug"]}/'
    posts.append((meta,body))
posts.sort(key=lambda p:str(p[0].get('date') or p[0].get('added') or ''), reverse=True)

def post_date(meta, long=False, include_time=False):
    if meta.get('date_label'):
        return f'<span>{esc(meta["date_label"])}</span>'
    if not meta.get('date'):
        return ''
    value = str(meta['date'])
    parsed = datetime.strptime(value, '%Y-%m-%d')
    label = f'{parsed:%B} {parsed.day}, {parsed:%Y}' if long else value
    if include_time and meta.get('published_time'):
        clock = str(meta['published_time'])
        datetime.strptime(clock, '%H:%M')
        label = f'{parsed:%B} {parsed.day}, {parsed:%Y} · {clock}'
        value += f'T{clock}:00+08:00'
    rendered = f'<time datetime="{esc(value)}">{esc(label)}</time>'
    return f'<em>{rendered}</em>' if include_time and meta.get('date_italic') else rendered

def category_tabs(active):
    return '<nav class="category-tabs" aria-label="Blog categories">'+''.join(f'<a href="{href}"'+(' aria-current="page" class="selected"' if name==active else '')+f'>{name}</a>' for name,href in [('All','/blogs/')]+[(c,f'/blogs/{c.lower()}/') for c in CATEGORIES])+'</nav>'

def post_list(items, heading='h2'):
    if not items:
        return '<div class="empty-state"><p>No posts yet.</p><p class="muted">Notes will appear here as they are published.</p></div>'
    return '<ul class="blog-list">'+''.join(f'<li><div class="post-meta">{post_date(p, long=True)}<span>{esc(p.get("topic",p["category"]))}</span></div><{heading}><a href="{p["route"]}">{esc(p["title"])}</a></{heading}><p>{esc(p.get("description",""))}</p></li>' for p,b in items)+'</ul>'

THOUGHT_TOPICS = {'Life Thoughts': '/blogs/thoughts/', 'Technical Thoughts': '/blogs/thoughts/technical/'}

def thoughts_view(items, active='Life Thoughts'):
    # Real links keep the selected category on refresh and work without JavaScript.
    tabs = '<nav class="thoughts-tabs" aria-label="Thoughts topics">' + ''.join(
        f'<a href="{route}"' + (' class="selected" aria-current="page"' if topic == active else '') +
        f'>{topic}</a>' for topic, route in THOUGHT_TOPICS.items()) + '</nav>'
    entries = [(p,b) for p,b in items if p.get('topic') == active]
    return tabs + post_list(entries)

def magic_gallery():
    entries = []
    for video in MAGIC_VIDEOS:
        seconds = int(video['duration_seconds'])
        duration = f'{seconds // 60}:{seconds % 60:02d}'
        silent = ' · Silent' if not video['has_audio'] else ''
        orientation = ' performance--portrait' if video['height'] > video['width'] else ''
        entries.append(f'''<li class="performance{orientation}" id="{video['id']}">
        <video class="magic-video" controls playsinline preload="none" poster="{esc(video['poster'])}" width="{video['width']}" height="{video['height']}" aria-label="{esc(video['title'])}"><source src="{esc(video['src'])}" type="video/mp4"><p><a href="{esc(video['src'])}">Open {esc(video['title'])}</a></p></video>
        <div class="performance-caption"><h2><a href="{esc(video['src'])}">{esc(video['title'])}</a></h2><span>{duration}{silent}</span></div></li>''')
    return f'<section class="magic-collection" aria-label="Magic performances"><p class="collection-meta">{len(MAGIC_VIDEOS)} performances</p><ol class="performance-grid">'+''.join(entries)+'</ol></section>'

def magic_collection_link():
    return f'<ul class="blog-list"><li><div class="post-meta"><span>Magic</span><span>{len(MAGIC_VIDEOS)} videos</span></div><h2><a href="/blogs/magic/">Magic performances</a></h2><p>A collection of close-up magic and performance clips.</p></li></ul>'

for name in ['All'] + list(CATEGORIES):
    items = posts if name=='All' else [(p,b) for p,b in posts if p['category']==name]
    title = 'Blogs' if name=='All' else name
    subtitle = 'Magic, movies, and thoughts — in and beyond research.' if name=='All' else CATEGORIES[name]
    if name == 'Magic' and MAGIC_VIDEOS:
        entries = magic_gallery() + (post_list(items) if items else '')
    elif name == 'All' and MAGIC_VIDEOS:
        entries = magic_collection_link() + post_list(items)
    elif name == 'Thoughts':
        entries = thoughts_view(items)
    else:
        entries = post_list(items)
    content = f'<div class="page-content blog-page"><header class="page-title"><h1>{title}</h1><p>{subtitle}</p></header>{category_tabs(name)}{entries}</div>'
    write('/blogs/' if name=='All' else f'/blogs/{name.lower()}/',page(title,content,active='Blogs'))

thought_items = [(p,b) for p,b in posts if p['category'] == 'Thoughts']
technical_content = f'<div class="page-content blog-page"><header class="page-title"><h1>Thoughts</h1><p>{CATEGORIES["Thoughts"]}</p></header>{category_tabs("Thoughts")}{thoughts_view(thought_items, "Technical Thoughts")}</div>'
write(THOUGHT_TOPICS['Technical Thoughts'], page('Technical Thoughts', technical_content, active='Blogs'))

for meta, body in posts:
    missing = re.findall(r'!\[\[([^\]]+)\]\]',body)
    body = re.sub(r'!\[\[[^\]]+\]\]', '', body)
    # Preserve TeX before Markdown interprets escapes and underscores.
    formulas = []
    def protect(match):
        value = match.group(0).replace('\\_', '_').replace('>\\\\', '\\\\')
        formulas.append(value)
        return f'MATHPLACEHOLDER{len(formulas)-1}END'
    if meta.get('math'):
        body = re.sub(r'\$\$[\s\S]*?\$\$|(?<!\\)\$(?!\$)[^\n$]+?(?<!\\)\$', protect, body)
    body = re.sub(r'^> \[!important\]\s*', '> **Note.** ', body, flags=re.M)
    body = re.sub(r'^(#{1,6}) ', lambda m:'#'*(min(len(m[1])+1,6))+' ',body,flags=re.M)
    parser = markdown.Markdown(extensions=['extra','sane_lists','toc'], extension_configs={'toc':{'permalink':False}})
    article = parser.convert(body)
    for i,tex in enumerate(formulas):
        article = article.replace(f'MATHPLACEHOLDER{i}END',html.escape(tex))
    note = '<p class="article-note">This tutorial is a work in progress. Some illustrations referenced in the original notes are not yet available.</p>' if missing else ''
    scripts = '''<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']},startup:{ready(){MathJax.startup.defaultReady();MathJax.startup.promise.then(()=>document.documentElement.dataset.mathReady='true')}}};</script><script defer src="/assets/vendor/mathjax/tex-chtml.js"></script>''' if meta.get('math') else ''
    source_link = f'<p class="article-source"><a href="{esc(meta["source_url"])}">Read the Chinese original on WeChat ↗</a></p>' if meta.get('source_url') else ''
    heading = f'<h1'+(' class="article-title--strong"' if meta.get('title_bold') else '')+f'>{esc(meta["title"])}</h1>'
    description = f'<p class="article-description">{esc(meta["description"])}</p>' if meta.get('show_description', True) else ''
    if meta.get('byline'):
        article_header = f'<p class="post-meta">{esc(meta.get("topic",meta["category"]))}</p>{heading}<p class="article-byline">{esc(meta["byline"])}</p><p class="post-meta">{post_date(meta, include_time=True)}</p>{description}{source_link}'
    else:
        article_header = f'<p class="post-meta"><span>{esc(meta.get("topic",meta["category"]))}</span>{post_date(meta, include_time=True)}</p>{heading}{description}{source_link}'
    back_label = meta.get('topic', meta['category'])
    back_route = THOUGHT_TOPICS.get(back_label, f'/blogs/{meta["category"].lower()}/')
    content = f'''<article class="page-content article-page"><a class="back-link" href="{back_route}">← {esc(back_label)}</a><header class="article-header">{article_header}</header>{note}<div class="article-body">{article}</div><a class="back-link article-end" href="{back_route}">← Back to {esc(back_label)}</a></article>'''
    write(meta['route'],page(meta['title'],content,active='Blogs',description=meta['description'],extra_head=scripts))

aliases = {'/cv/':PROFILE['cv'],'/publications/':'/papers/','/blog/':'/blogs/','/2025-03-26-plotly/':'/blogs/thoughts/diffusion-models/','/blog/2025/plotly/':'/blogs/thoughts/diffusion-models/','/news/':'/'}
for old,new in aliases.items():
    write(old,f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={new}"><title>Page moved</title></head><body><a href="{new}">Continue to the updated page</a></body></html>')
write('404.html',page('Page not found','<div class="page-content"><header class="page-title"><h1>Page not found</h1><p>The page may have moved.</p></header><p><a href="/">Return home →</a></p></div>'))
(OUT/'.nojekyll').write_text('',encoding='utf-8')
print(f'Built {len(list(OUT.rglob("*.html")))} pages in {OUT}')
