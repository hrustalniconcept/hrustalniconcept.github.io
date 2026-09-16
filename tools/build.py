#!/usr/bin/env python3
"""Генератор раздела «Услуги». Читает content/services.json, content/cases.json, content/config.json,
собирает uslugi/index.html, uslugi/<slug>/index.html, sitemap.xml, robots.txt и CONTENT-TODO.md.
Запуск: python3 tools/build.py"""
import json, os, re, html, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = lambda *p: os.path.join(ROOT, 'content', *p)
cfg = json.load(open(C('config.json')))
data = json.load(open(C('services.json')))
cases = json.load(open(C('cases.json')))['cases']
SITE = cfg['site']['url'].rstrip('/')
SERVICES = data['services']
BY = {s['slug']: s for s in SERVICES}
ORDER = data['ladder']['order']
TODOS = []            # (страница, блок, текст)
_ctx = {'page': '', 'block': ''}

LOGO = '<svg viewBox="0 0 69 69" aria-hidden="true"><path d="M52.1687 68.9595L34.5 55.6875L16.8313 68.9595H0.121479L34.5 43.1347L68.8785 68.9595H52.1687Z"/><path d="M43.1347 34.5L68.9595 0.121479V16.8313L55.6875 34.5L68.9595 52.1687V68.8785L43.1347 34.5Z"/><path d="M16.8313 0.0404053L34.5 13.3124L52.1687 0.0404053H68.8785L34.5 25.8652L0.121479 0.0404053H16.8313Z"/><path d="M25.8652 34.5L0.0404053 68.8785V52.1687L13.3124 34.5L0.0404053 16.8313V0.121479L25.8652 34.5Z"/></svg>'

def esc(s): return html.escape(str(s), quote=True)

def t(s, block=None):
    """Экранирует текст и превращает [[ЗАПОЛНИТЬ: ...]] в видимую заглушку, регистрируя её в CONTENT-TODO."""
    if block: _ctx['block'] = block
    s = esc(s)
    def rep(m):
        TODOS.append((_ctx['page'], _ctx['block'], m.group(1).strip()))
        return f'<span class="todo">{m.group(1).strip()}</span>'
    return re.sub(r'\[\[\s*(.*?)\s*\]\]', rep, s, flags=re.S)

def plain(s):
    """Текст для meta и JSON-LD: заглушки убираются."""
    return re.sub(r'\s*\[\[.*?\]\]', '', str(s), flags=re.S).strip()

def is_todo(s): return bool(re.search(r'\[\[', str(s) or ''))

def idx(slug): return ORDER.index(slug) + 1

def price_num(s):
    v = s['price']['value']; return f'{v:,}'.replace(',', ' ')

# ---------- общие части ----------
def head(title, desc, canonical, og_image=None, ld=None, preload=None):
    og = og_image or f'{SITE}/assets/img/uslugi/proverka_aero_og.jpg'
    pre = f'<link rel="preload" as="image" href="{preload["src"]}" imagesrcset="{preload["srcset"]}" imagesizes="100vw">' if preload else ''
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{og}"><meta property="og:url" content="{canonical}"><meta property="og:locale" content="ru_RU">
<meta name="theme-color" content="#072F50">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/BebasNeue-Bold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/Inter-var-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
{pre}
<link rel="stylesheet" href="/assets/css/site.css">
{('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>') if ld else ''}
<script type="application/json" id="cfg">{json.dumps({"bitrix": {k: v for k, v in cfg["bitrix"].items() if not k.startswith("_")}, "metrika": {"counter": cfg["metrika"]["counter"]}}, ensure_ascii=False)}</script>
</head>'''

def nav(cur_slug=None):
    tg = cfg['contacts']['manager']['telegram']
    items = ''.join(f'<a href="/uslugi/{s["slug"]}/"{" class=cur aria-current=page" if s["slug"] == cur_slug else ""}>{esc(s["title"] if not s.get("flagship") else "Продуктовая концепция")}<small>{esc(s["price"]["display"])}</small></a>' for s in SERVICES)
    return f'''<header class="nav" id="nav">
  <a class="logo" href="/">{LOGO}Хрустальный</a>
  <nav class="links" aria-label="Разделы"><a href="/uslugi/">Услуги</a><a href="{cfg["site"]["portfolio"]}">Портфолио</a><a href="{cfg["site"]["home"]}">hrustalni.com</a></nav>
  <div class="right"><a class="tg" href="{tg}" rel="noopener">Написать в Telegram</a><a href="#zayavka">Заявка</a><button class="burger" type="button" aria-label="Меню"><i></i><i></i><i></i></button></div>
</header>
<div class="menu" role="dialog" aria-label="Меню сайта">
  <div class="top"><a class="logo" href="/">{LOGO}Хрустальный</a><button class="close" type="button">закрыть <i></i></button></div>
  <div class="cols">
    <div><span class="lbl">Услуги для девелоперов и землевладельцев</span><div class="pl">{items}<a href="/uslugi/" style="font-size:clamp(20px,2vw,26px);color:var(--w70)">Как выбрать по стадии проекта →</a></div></div>
    <div><span class="lbl">Бюро</span><div class="pl"><a href="{cfg["site"]["portfolio"]}">Портфолио<small>дома и посёлки</small></a><a href="{cfg["site"]["home"]}">hrustalni.com<small>основной сайт</small></a><a href="{cfg["contacts"]["channel"]}" rel="noopener">Telegram-канал</a></div></div>
  </div>
  <div class="bottom"><a href="#zayavka">Заявка</a><a href="{tg}" rel="noopener">Анна, работа с проектами → Telegram</a><a href="{cfg["site"]["home"]}">hrustalni.com</a></div>
</div>'''

def footer():
    return f'''<footer class="footer">
  <a class="logo" href="/">{LOGO}Хрустальный</a>
  <span class="cap">Концепт-бюро «Хрустальный» · {esc(cfg["facts"]["years"])} · {esc(cfg["facts"]["settlements"])} · {esc(cfg["facts"]["residents"])}</span>
  <div class="fl"><a href="/uslugi/">Услуги</a><a href="{cfg["site"]["portfolio"]}">Портфолио</a><a href="{cfg["contacts"]["manager"]["telegram"]}" rel="noopener">Telegram</a><a href="{cfg["site"]["home"]}">hrustalni.com</a></div>
</footer>
<script src="/assets/js/site.js" defer></script>'''

def crumbs(items, dark=False):
    li = ''.join(f'<li><a href="{h}">{esc(n)}</a></li>' if h else f'<li aria-current="page">{esc(n)}</li>' for n, h in items)
    return f'<nav aria-label="Вы здесь"><ol class="crumbs">{li}</ol></nav>'

def ladder(cur=None, dark=False):
    """Лестница услуг с зачётами. Текущая подсвечена."""
    rows = []
    for i, slug in enumerate(ORDER):
        s = BY[slug]; n = f'{i+1:02d}'
        cls = ' '.join(filter(None, ['cur' if slug == cur else '', 'flag' if s.get('flagship') else '']))
        title = 'Продуктовая концепция' if s.get('flagship') else s['title']
        note = s['price'].get('note', '')
        href = f'/uslugi/{slug}/'
        inner = f'<span class="n">{n}</span><span class="t">{esc(title)}<small>{esc(s["duration"])}</small></span><span class="d">{esc(note)}</span><span class="p">{esc(s["price"]["display"])}</span><span class="a">{"Вы здесь" if slug == cur else "Подробнее <i>→</i>"}</span>'
        rows.append(f'<li class="{cls}">' + (f'<a href="{href}">{inner}</a>' if slug != cur else f'<a aria-current="page">{inner}</a>') + '</li>')
        if slug == 'finansovaya-model':
            rows.append('<li class="off"><span>↓ ' + t(data['ladder']['offset_rule'], 'Лестница услуг') + '</span></li>')
    entry = data['ladder'].get('entry')
    first = (f'<li class="entry"><a href="#zayavka"><span class="n">00</span><span class="t">{esc(entry["title"])}<small>{esc(entry["text"])}</small></span><span class="d"></span><span class="p">{esc(entry["price"])}</span><span class="a">Начать <i>↓</i></span></a></li>' if entry else '')
    return f'<ol class="ladder">{first}{"".join(rows)}</ol>'

def form_block(s):
    """Блок «Первый шаг»: одна форма, поля по ТЗ, без капчи. Подтверждение говорит, что будет дальше."""
    tg = cfg['contacts']['manager']['telegram']
    success = (f'<div class="success"><h2 class="h2">Заявка у Анны. <em>Ответ</em> в ближайший рабочий день</h2><div class="rule"></div>'
               f'<p class="txt">Первый разговор занимает 30 минут: по кадастровому номеру и схеме участка скажем, что там можно, а что нельзя, и нужен ли вам этот этап вообще. Если удобнее сразу: <a href="{tg}" rel="noopener" style="text-decoration:underline;text-underline-offset:3px">Анна в Telegram</a>.</p></div>')
    policy = cfg.get('policy_url') or ''
    pol = f'<a href="{policy}">политикой обработки данных</a>' if policy else t('политикой обработки данных [[ЗАПОЛНИТЬ: ссылка на политику обработки персональных данных]]', 'Первый шаг, форма')
    return f'''<section class="sec dark wrap" id="zayavka">
  <div class="grid">
    <div class="c5 rv"><span class="lbl">Первый шаг</span><h2 class="h2" style="margin-top:14px">{s["hero_cta_h2"]}</h2><div class="rule"></div>
      <p class="txt">{t(s["first_step_text"], "Первый шаг")}</p>
      <p class="txt" style="margin-top:18px">Пишет и звонит {esc(cfg["contacts"]["manager"]["name"])}, {esc(cfg["contacts"]["manager"]["role"])}. Если удобнее без формы: <a href="{tg}" rel="noopener" style="text-decoration:underline;text-underline-offset:3px">Telegram</a>.</p></div>
    <div class="c6 c6r rv">
      <form id="leadForm" class="form" novalidate data-service-title="{esc(s["title"])}" data-cta="{esc(s["cta"])}" data-success="{esc(success)}">
        <div class="f"><label for="f-name">Имя</label><input id="f-name" name="name" type="text" autocomplete="name" required placeholder="Как к вам обращаться"><span class="err">Напишите имя</span></div>
        <div class="f"><label for="f-contact">Телефон или Telegram</label><input id="f-contact" name="contact" type="text" inputmode="tel" autocomplete="tel" required placeholder="+7 ··· или @ник"><span class="err">Нужен телефон или ник в Telegram</span></div>
        <div class="f"><label for="f-object">Кадастровый номер или ссылка на проект</label><input id="f-object" name="object" type="text" placeholder="38:06:······:···· или ссылка"></div>
        <div class="f"><label for="f-about">Коротко о проекте, необязательно</label><textarea id="f-about" name="about" rows="2" placeholder="Площадь, стадия, что сейчас мешает"></textarea></div>
        <div class="f" style="position:absolute;left:-9999px" aria-hidden="true"><label for="f-company">Компания</label><input id="f-company" name="company" type="text" tabindex="-1" autocomplete="off"></div>
        <div class="foot"><button class="btn" type="submit"><span>{esc(s["cta"])}</span><i>→</i></button><p class="cap">Нажимая кнопку, вы соглашаетесь с {pol}. Без рассылок: один звонок или сообщение по делу.</p></div>
        <p class="msg" role="alert"></p>
      </form>
    </div>
  </div>
</section>'''

# ---------- страница услуги ----------
def service_page(s):
    slug = s['slug']; _ctx['page'] = f'/uslugi/{slug}/'
    n = idx(slug); url = f'{SITE}/uslugi/{slug}/'
    seo_title = plain(s['seo']['title']) or f'{s["title"]}. Концепт-бюро «Хрустальный»'
    seo_desc = plain(s['seo']['description']) or plain(s['promise'])
    img = s.get('image', {}); has_img = bool(img.get('src'))
    base = f'/assets/img/uslugi/{img["src"]}' if has_img else ''
    srcset = f'{base}_s.webp 800w, {base}_m.webp 1400w, {base}.webp 2400w' if has_img else ''
    og = f'{SITE}{base}_og.jpg' if has_img else None
    faq_ld = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q['q'], "acceptedAnswer": {"@type": "Answer", "text": plain(q['a'])}} for q in s['faq'] if not is_todo(q['a'])]}
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Service", "name": s['title'], "description": seo_desc, "url": url, "serviceType": "Консалтинг в загородном девелопменте", "areaServed": "RU",
         "provider": {"@type": "Organization", "name": cfg['site']['name'], "url": cfg['site']['home']},
         "offers": {"@type": "Offer", "price": s['price']['value'], "priceCurrency": "RUB", "description": s['price']['display'] + ', ' + s['duration']}},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "Услуги", "item": SITE + '/uslugi/'}, {"@type": "ListItem", "position": 3, "name": s['title'], "item": url}]},
        faq_ld]}

    # тексты блоков по умолчанию, если в JSON их нет
    s.setdefault('hero_cta_h2', 'Расскажите <em>о проекте</em>')
    s.setdefault('first_step_text', 'Ответим в ближайший рабочий день и скажем, с какой ступени имеет смысл начинать.')
    report = cfg['report_example']['url']
    report_link = (f'<a class="arrow" href="{report}" data-goal="report_example" target="_blank" rel="noopener">Посмотреть пример отчёта <i>↗</i></a>' if report
                   else f'<a class="arrow" href="#zayavka" data-goal="report_example">Прислать пример отчёта <i>↓</i></a>')
    if not report: TODOS.append((_ctx['page'], 'Обложка, кнопка «Посмотреть пример отчёта»', 'Обезличенный пример отчёта в PDF, 4-6 страниц. Пока файла нет, кнопка ведёт на форму'))

    # 1. обложка
    photo = (f'<figure class="photo rv"><img src="{base}_m.webp" srcset="{srcset}" sizes="100vw" width="2400" height="1409" alt="{esc(img["alt"])}" fetchpriority="high" decoding="async">'
             f'<figcaption class="cap">{esc(img.get("caption", ""))}</figcaption></figure>' if has_img else '<div class="photo empty rv" role="img" aria-label="Место для фотографии"></div>')
    if not has_img: TODOS.append((_ctx['page'], 'Обложка', f'Фотография на обложку услуги «{s["title"]}», собственная съёмка, привязанная к содержанию'))
    _ctx['block'] = 'Обложка'
    hero = f'''<section class="hero wrap">
  {crumbs([("Главная", "/"), ("Услуги", "/uslugi/"), (s["title"], None)])}
  <div class="meta"><span class="lbl">Услуга {n:02d} / {len(ORDER):02d}</span><span class="lbl">{esc(s["duration"])}</span><span class="lbl">{esc(s["price"]["display"])}</span></div>
  <h1 class="h1">{s.get("h1", esc(s["title"]))}</h1>
  <p class="lead">{t(s.get("result_line") or s["promise"])}</p>
  <div class="facts">
    <div><b>{esc(s["price"]["display"])}</b><span class="cap">{esc(s["duration"])}</span></div>
    <div><b>{esc(s.get("fact2", {}).get("b", s["duration"]))}</b><span class="cap">{t(s.get("fact2", {}).get("cap", s["price"]["note"]))}</span></div>
  </div>
  <div class="actions"><a class="btn" href="#zayavka" data-goal="cta_click">{esc(s["cta"])} <i>→</i></a>{report_link}</div>
  {photo}
</section>'''

    # 2. кому подходит / не подходит
    _ctx['block'] = 'Кому подходит'
    li = lambda items, mark: ''.join(f'<li><i>{mark}</i><p>{t(x)}</p></li>' for x in items)
    who = f'''<section class="sec wrap" id="komu">
  <div class="head"><h2 class="h2 rv">Кому подходит <em>и кому нет</em></h2><p class="txt rv">Правая колонка важнее левой. Если ваш случай там, сэкономим друг другу неделю.</p></div>
  <div class="two">
    <div class="rv"><div class="word">Подходит</div><ul class="list">{li(s["for_whom"], "+")}</ul></div>
    <div class="rv"><div class="word">Не подходит</div><ul class="list x">{li(s["not_for_whom"], "×")}</ul></div>
  </div>
</section>'''

    # 3. что получаете на выходе
    _ctx['block'] = 'Что получаете на выходе'
    dl = ''.join(f'<li><p>{t(x)}</p></li>' for x in s['deliverables'])
    frame_img = ''
    if s.get('artifact_image'):
        ai = s['artifact_image']; frame_img = f'<img src="/assets/img/uslugi/{ai["src"]}_m.webp" alt="{esc(ai["alt"])}" loading="lazy" decoding="async">'
    else:
        TODOS.append((_ctx['page'], 'Что получаете на выходе', 'Снимок разворота отчёта или экрана с документом для правой колонки. Пока контейнер пустой'))
    out = f'''<section class="sec dark wrap" id="na-vyhode">
  <div class="grid">
    <div class="c7 rv"><span class="lbl">Что получаете на выходе</span><h2 class="h2" style="margin-top:14px">Что окажется <em>у вас в руках</em></h2><div class="rule"></div>
      <ol class="deliv" style="margin-top:28px">{dl}</ol></div>
    <div class="c4 c4r rv" style="align-self:end"><div class="frame">{frame_img}<span class="cap">{"Разворот отчёта" if frame_img else ""}</span></div>
      <p class="cap" style="margin-top:14px">{report_link}</p></div>
  </div>
</section>'''

    # 4. результат
    _ctx['block'] = 'Результат'
    rl = ''.join(f'<li><b>{i+1:02d}</b><p>{t(x)}</p></li>' for i, x in enumerate(s['results']))
    res = f'''<section class="sec wrap" id="rezultat">
  <div class="head"><h2 class="h2 rv">Какие решения <em>вы примете</em></h2><p class="txt rv">Каждый пункт это решение, которое можно принять по итогам, или деньги, которые не будут потеряны.</p></div>
  <ol class="res n{len(s["results"])}">{rl}</ol>
</section>'''

    # 5. как устроена работа
    _ctx['block'] = 'Как устроена работа'
    if s['stages']:
        st = ''.join(f'<li class="rv"><span class="lbl">{esc(x["term"])}</span><h3 class="h3">{esc(x["name"])}</h3><p>{t(x["out"])}</p></li>' for x in s['stages'])
        stages_html = f'<ol class="steps" style="--n:{len(s["stages"])}">{st}</ol>'
    else:
        stages_html = f'<p class="txt">{t("[[ЗАПОЛНИТЬ: этапы работы по услуге «" + s["title"] + "» с неделями и выходом каждого этапа]]")}</p>'
    how = f'''<section class="sec stone wrap" id="kak">
  <div class="head"><h2 class="h2 rv">Как устроена <em>работа</em></h2><p class="txt rv">{esc(s["duration"][0].upper() + s["duration"][1:])}. У каждого этапа свой выход, и его мы защищаем в разговоре, а не отправляем письмом.</p></div>
  {stages_html}
</section>'''

    # 6. стоимость
    _ctx['block'] = 'Стоимость'
    moves = s['price'].get('what_moves_it')
    moves_html = ('<ul class="list" style="margin-top:12px">' + ''.join(f'<li><i>·</i><p>{t(x)}</p></li>' for x in moves) + '</ul>') if moves else f'<p>{t(s["price"].get("fixed_note", "Цена не зависит от площади участка и региона. Работаем по документам и открытым данным по всей России."))}</p>'
    scale = f'<p class="txt" style="margin-top:18px">{t(s["price"]["scale_argument"])}</p>' if s['price'].get('scale_argument') else ''
    nxt = BY['koncepciya']
    price = f'''<section class="sec dark wrap price" id="stoimost">
  <div class="grid">
    <div class="c5 rv"><span class="lbl" style="display:block">Стоимость</span><b class="big" style="margin-top:14px">{esc(s["price"]["display"])}</b><span class="cap" style="display:block;margin-top:8px">{esc(s["duration"])}</span>{scale}</div>
    <div class="c7 rv">
      <div class="row"><div><span class="lbl">Что двигает цену</span>{moves_html}</div>
        <div><span class="lbl">Следующая ступень</span><p>{t(s["price"]["note"])}. <b>{esc(s.get("next_step", "Если по итогам нужна концепция целиком: " + nxt["price"]["display"] + ", первый этап от 600 000 ₽ засчитывается в полную сумму."))}</b></p></div>
        <div><span class="lbl">Оплата</span><p>{t(s["payment"])}</p></div></div>
      <div class="row" style="border-bottom:1px solid var(--wline)"><div style="grid-column:1/-1"><p><b>Точная сумма называется после разговора и разбора материалов, а не до него.</b> Если мастер-план, концепция или исследование уже есть, полный объём не продаём. Проверяем и дорабатываем: экономика, темп, очерёдность, управление.</p></div></div>
      <div class="actions" style="margin-top:28px"><a class="btn" href="#zayavka" data-goal="cta_click">{esc(s["cta"])} <i>→</i></a></div>
    </div>
  </div>
</section>'''

    # 7. кейс и отзыв
    _ctx['block'] = 'Кейс'
    ref = s.get('case_ref', '')
    cs = [c for c in cases if c['id'] == ref] or ([] if is_todo(ref) else [c for c in cases if slug in c['services']])
    if cs:
        c = cs[0]
        if slug not in c.get('primary', c['services'][:1]): TODOS.append((_ctx['page'], 'Кейс', f'Кейс именно по услуге «{s["title"]}». Пока показан смежный кейс «{c["title"]}»'))
        row = lambda k, v: f'<div><dt>{k}</dt><dd>{t(v)}</dd></div>'
        case_html = f'''<div class="case rv"><div class="fig"><b>{esc(c["figure"])}</b><p class="cap">{esc(c["figure_caption"])}</p><p class="cap" style="margin-top:18px">{esc(c["meta"])}</p></div>
      <div><h3 class="h3" style="margin-bottom:18px">{esc(c["title"])}</h3><dl>{row("Ситуация", c["situation"])}{row("Что нашли", c["found"])}{row("Что поменяли", c["changed"])}{row("Что изменилось", c["result"])}</dl></div></div>'''
    else:
        ref = s.get('case_ref', '')
        case_html = f'<p class="txt rv">{t(ref if is_todo(ref) else "[[ЗАПОЛНИТЬ: кейс по услуге «" + s["title"] + "» в формате Ситуация → Что нашли → Что поменяли → Что изменилось в цифрах]]")}</p>'
    review = s.get('review')
    review_html = (f'<blockquote class="quote rv"><p>{esc(review["text"])}</p><footer class="cap">{esc(review["name"])}, {esc(review["role"])}, {esc(review["project"])}</footer></blockquote>' if review and not is_todo(review.get('text', '')) else '')
    if not review_html:
        TODOS.append((_ctx['page'], 'Кейс, отзыв', f'Отзыв клиента по услуге «{s["title"]}»: имя, должность, проект, 2-4 предложения о том, какое решение помог принять результат. Пока блок отзыва не выводится'))
    case = f'''<section class="sec wrap" id="keis">
  <div class="head"><h2 class="h2 rv">Как это выглядит <em>в цифрах</em></h2><p class="txt rv">Клиентские проекты не называем. Собственные проекты группы «Хрустальный» называем прямо.</p></div>
  {case_html}{review_html}
</section>'''

    # 8. что не входит и чего не обещаем
    _ctx['block'] = 'Что не входит'
    ni = ''.join(f'<li><i>×</i><p>{t(x)}</p></li>' for x in s['not_included'])
    np_ = ''.join(f'<li><i>×</i><p>{t(x)}</p></li>' for x in s['not_promised'])
    limits = f'''<section class="sec stone wrap" id="ne-vhodit">
  <div class="head"><h2 class="h2 rv">Что не входит <em>и чего не обещаем</em></h2><p class="txt rv">Чтобы через неделю не было разговора «мы думали, это тоже входит».</p></div>
  <div class="two">
    <div class="rv"><div class="word">Не входит</div><ul class="list x">{ni}</ul></div>
    <div class="rv"><div class="word">Не обещаем</div><ul class="list x">{np_}</ul></div>
  </div>
</section>'''

    # 9. вопросы
    _ctx['block'] = 'Вопросы'
    fq = ''.join(f'<details{" open" if i == 0 else ""}><summary>{esc(q["q"])}<i></i></summary><div class="a">{t(q["a"])}</div></details>' for i, q in enumerate(s['faq']))
    faq = f'''<section class="sec wrap" id="voprosy">
  <div class="head"><h2 class="h2 rv">Вопросы, которые <em>задают</em></h2><p class="txt rv">Дословно из разговоров с клиентами.</p></div>
  <div class="faq rv">{fq}</div>
</section>'''

    # 10. форма
    _ctx['block'] = 'Первый шаг'
    form = form_block(s)

    # 11. лестница
    _ctx['block'] = 'Лестница услуг'
    lad = f'''<section class="sec wrap" id="uslugi">
  <div class="head"><h2 class="h2 rv">Лестница <em>услуг</em></h2><p class="txt rv">Выбор зависит от стадии проекта. Все ступени ведут к концепции, зачёты показаны стрелками. <a class="arrow" href="/uslugi/" style="font-size:16px;margin-top:10px">Как выбрать по стадии <i>→</i></a></p></div>
  <div class="rv">{ladder(cur=slug)}</div>
</section>'''

    body = f'<body data-page="/uslugi/{slug}/" data-service="{slug}">{nav(slug)}<main>{hero}{who}{out}{res}{how}{price}{case}{limits}{faq}{form}{lad}</main>{footer()}</body></html>'
    pre = {"src": f'{base}_m.webp', "srcset": srcset} if has_img else None
    return head(seo_title, seo_desc, url, og, ld, pre) + body

# ---------- хаб ----------
def hub_page():
    _ctx['page'] = '/uslugi/'; _ctx['block'] = 'Хаб'
    url = f'{SITE}/uslugi/'
    hub = data.get('hub_page', {})
    title = 'Услуги для девелоперов и землевладельцев: аудит участка, концепция посёлка, финмодель. Концепт-бюро «Хрустальный»'
    desc = 'Пять услуг по стадии проекта: аудит участка за неделю, проверка готовых материалов, финансовая модель, продуктовая концепция, сопровождение. Цены и сроки на странице.'
    rows = ''.join(f'<li><span>{esc(r["stage"])}</span><a class="arrow" href="/uslugi/{r["service"]}/">{esc(BY[r["service"]]["title"] if not BY[r["service"]].get("flagship") else "Продуктовая концепция")} <i>→</i></a></li>' for r in hub.get('stage_table', []))
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "Услуги", "item": url}]}
    body = f'''<body data-page="/uslugi/" data-service="hub">{nav()}<main>
<section class="hero wrap" style="padding-bottom:var(--sec)">
  {crumbs([("Главная", "/"), ("Услуги", None)])}
  <div class="meta"><span class="lbl">Услуги</span><span class="lbl">Пять ступеней, одна лестница</span></div>
  <h1 class="h1">Что <em>и как</em> строить</h1>
  <p class="lead">{esc(hub.get("intro", "Выбор услуги зависит от стадии проекта, а не от роли. Ниже таблица: на какой стадии с чего начинают."))}</p>
</section>
<section class="sec stone wrap"><div class="head"><h2 class="h2 rv">Стадия проекта <em>и ступень</em></h2></div>
  <ul class="ladder rv" style="list-style:none;padding:0">{rows}</ul></section>
<section class="sec wrap" id="uslugi"><div class="head"><h2 class="h2 rv">Лестница <em>услуг</em></h2></div><div class="rv">{ladder()}</div></section>
</main>{footer()}</body></html>'''
    return head(title, desc, url, None, ld) + body

# ---------- сборка ----------
def write(path, content):
    full = os.path.join(ROOT, path); os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(content); print('  ', path, len(content)//1024, 'KB')

def main():
    only = os.environ.get('ONLY')
    pages = []
    for s in SERVICES:
        if only and s['slug'] != only: continue
        write(f'uslugi/{s["slug"]}/index.html', service_page(s)); pages.append(f'/uslugi/{s["slug"]}/')
    if not only:
        write('uslugi/index.html', hub_page()); pages.append('/uslugi/')
    today = datetime.date.today().isoformat()
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>' for p in ['/'] + pages) + '</urlset>')
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    # CONTENT-TODO
    seen = set(); lines = ['# Чего не хватает на страницах услуг', '', f'Собрано генератором `tools/build.py` {today}. Каждая заглушка `[[ЗАПОЛНИТЬ]]` из `content/*.json` и кода попадает сюда автоматически. Исходный список из пакета: `docs/services-pack/content/CONTENT-TODO.md`.', '', '| Страница | Блок | Что нужно |', '|---|---|---|']
    for p, b, x in TODOS:
        k = (p, b, x)
        if k in seen: continue
        seen.add(k); lines.append(f'| `{p}` | {b} | {x} |')
    write('CONTENT-TODO.md', '\n'.join(lines) + '\n')
    print(f'заглушек: {len(seen)}')

if __name__ == '__main__':
    main()
