#!/usr/bin/env python3
"""Генератор раздела «Услуги». Читает content/services.json, content/cases.json, content/config.json,
собирает uslugi/index.html, uslugi/<slug>/index.html, sitemap.xml, robots.txt и CONTENT-TODO.md.
Запуск: python3 tools/build.py"""
import json, os, re, html, datetime, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = lambda *p: os.path.join(ROOT, 'content', *p)
cfg = json.load(open(C('config.json')))
data = json.load(open(C('services.json')))
cases = json.load(open(C('cases.json')))['cases']
site = json.load(open(C('site.json')))
SITE = cfg['site']['url'].rstrip('/')
SERVICES = data['services']
BY = {s['slug']: s for s in SERVICES}
ORDER = data['ladder']['order']
SIDE = data['ladder'].get('side', [])
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

def idx(slug): return ORDER.index(slug) + 1 if slug in ORDER else 0

def price_num(s):
    v = s['price']['value']; return f'{v:,}'.replace(',', ' ')

# ---------- общие части ----------
def head(title, desc, canonical, og_image=None, ld=None, preload=None):
    og = og_image or f'{SITE}/assets/img/uslugi/hub_aero_og.jpg'
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
<script type="application/json" id="cfg">{json.dumps({"bitrix": {k: v for k, v in cfg["bitrix"].items() if not k.startswith("_")}, "metrika": {"counter": cfg["metrika"]["counter"]}, "services": {sl: {"title": BY[sl]["title"], "gen": BY[sl].get("gen", BY[sl]["title"]), "short": BY[sl]["short"], "price": BY[sl]["price"]["display"], "duration": plain(BY[sl]["duration"]), "deliverables": [plain(x) for x in BY[sl]["deliverables"][:3]], "url": f"/uslugi/{sl}/"} for sl in ORDER + SIDE}}, ensure_ascii=False)}</script>
</head>'''

def nav(cur_slug=None):
    tg = cfg['contacts']['manager']['telegram']
    items = ''.join(f'<a href="/uslugi/{s["slug"]}/"{" class=cur aria-current=page" if s["slug"] == cur_slug else ""}>{esc(s["title"])}<small>{esc(s["price"]["display"])}</small></a>' for s in SERVICES)
    return f'''<header class="nav" id="nav">
  <a class="logo" href="/">{LOGO}Хрустальный</a>
  <nav class="links" aria-label="Разделы">{''.join(f'<a href="{x["url"]}"{" aria-current=page" if x["url"] == _ctx["page"] else ""}>{esc(x["title"])}</a>' for x in site["nav"])}</nav>
  <div class="right"><a class="tg" href="{tg}" rel="noopener">Написать в Telegram</a><a href="#zayavka">Заявка</a><button class="burger" type="button" aria-label="Меню"><i></i><i></i><i></i></button></div>
</header>
<div class="menu" role="dialog" aria-label="Меню сайта">
  <div class="top"><a class="logo" href="/">{LOGO}Хрустальный</a><button class="close" type="button">закрыть <i></i></button></div>
  <div class="cols">
    <div><span class="lbl">Услуги для девелоперов и землевладельцев</span><div class="pl">{items}<a href="/uslugi/" style="font-size:clamp(20px,2vw,26px);color:var(--w70)">Как выбрать по стадии проекта →</a></div></div>
    <div id="menu-portfolio" data-portfolio="{cfg["site"]["portfolio"]}"><span class="lbl">Портфолио</span><div class="pl"><a href="{cfg["site"]["portfolio"]}#built">Реализованные проекты</a><a href="{cfg["site"]["portfolio"]}#settlements">Коттеджные посёлки</a><a href="{cfg["site"]["portfolio"]}#houses">Индивидуальные дома</a><a class="all" href="{cfg["site"]["portfolio"]}">всё портфолио →</a></div></div>
    <div><span class="lbl">Бюро</span><div class="pl"><a href="/">Главная</a>{''.join(f'<a href="{x["url"]}">{esc(x["title"])}<small>{esc(x.get("small", ""))}</small></a>' for x in site["menu_bureau"])}<a href="{cfg["contacts"]["channel"]}" rel="noopener">Telegram-канал</a></div></div>
  </div>
  <div class="bottom"><a href="#zayavka">Заявка</a><a href="{tg}" rel="noopener">Telegram</a><a href="tel:{site["contacts"]["phone_tel"]}">{esc(site["contacts"]["phone_display"])}</a><a href="/kontakty/">Контакты</a></div>
</div>'''

def footer():
    c = site['contacts']
    cols = (f'<div><span class="lbl">Бюро</span><a href="/o-byuro/">О бюро</a><a href="/portfolio/">Портфолио</a><a href="/uslugi/">Услуги</a><a href="/obuchenie/">Обучение</a><a href="/kontakty/">Контакты</a></div>'
            f'<div><span class="lbl">Услуги</span>' + ''.join(f'<a href="/uslugi/{sl}/">{esc(BY[sl]["title"])}</a>' for sl in ORDER + SIDE) + '</div>'
            f'<div><span class="lbl">Связь</span><a href="{c["telegram_manager"]}" rel="noopener">Telegram</a><a href="tel:{c["phone_tel"]}">{esc(c["phone_display"])}</a><a href="mailto:{c["email"]}">{esc(c["email"])}</a><a href="{c["telegram_channel"]}" rel="noopener">Telegram-канал</a></div>')
    return (f'<footer class="footer"><div class="ftop"><a class="logo" href="/">{LOGO}Хрустальный</a><p class="cap">Концепт-бюро группы «Хрустальный». {esc(cfg["facts"]["years"])}, {esc(cfg["facts"]["settlements"])}, {esc(cfg["facts"]["residents"])}. Иркутск, работаем по всей России.</p></div>'
            f'<div class="fcols">{cols}</div><div class="fbot"><span class="cap">{esc(c["legal"]["name"])} · ИНН {esc(c["legal"]["inn"])}</span><a class="cap" href="/politika/">Политика обработки данных</a><a class="cap" href="{cfg["site"]["home"]}">hrustalni.com</a></div></footer>'
            f'<script src="/assets/js/site.js" defer></script>')

def crumbs(items, dark=False):
    li = ''.join(f'<li><a href="{h}">{esc(n)}</a></li>' if h else f'<li aria-current="page">{esc(n)}</li>' for n, h in items)
    return f'<nav aria-label="Вы здесь"><ol class="crumbs">{li}</ol></nav>'

def form_block(s, inner=False):
    """Блок «Первый шаг»: одна форма, поля по ТЗ, без капчи. Подтверждение говорит, что будет дальше."""
    tg = cfg['contacts']['manager']['telegram']
    success = (f'<div class="success"><h2 class="h2">Заявка получена. <em>Ответ</em> в ближайший рабочий день</h2><div class="rule"></div>'
               f'<p class="txt">Первый разговор занимает 30 минут: по кадастровому номеру и схеме участка скажем, что там можно, а что нельзя, и нужен ли вам этот этап вообще. Если удобнее сразу: <a href="{tg}" rel="noopener" style="text-decoration:underline;text-underline-offset:3px">Telegram</a>.</p></div>')
    policy = cfg.get('policy_url') or ''
    pol = f'<a href="{policy or "/politika/"}">политикой обработки данных</a>'
    formhtml = f'''<form id="leadForm" class="form" novalidate data-service-title="{esc(s["title"])}" data-cta="{esc(s["cta"])}" data-success="{esc(success)}">
        <div class="f"><label for="f-name">Имя</label><input id="f-name" name="name" type="text" autocomplete="name" required placeholder="Как к вам обращаться"><span class="err">Напишите имя</span></div>
        <div class="f"><label for="f-contact">Телефон или Telegram</label><input id="f-contact" name="contact" type="text" inputmode="tel" autocomplete="tel" required placeholder="+7 ··· или @ник"><span class="err">Нужен телефон или ник в Telegram</span></div>
        <div class="f"><label for="f-object">Кадастровый номер или ссылка на проект</label><input id="f-object" name="object" type="text" placeholder="38:06:······:···· или ссылка"></div>
        <div class="f"><label for="f-about">Коротко о проекте, необязательно</label><textarea id="f-about" name="about" rows="2" placeholder="Площадь, стадия, что сейчас мешает"></textarea></div>
        <div class="f" style="position:absolute;left:-9999px" aria-hidden="true"><label for="f-company">Компания</label><input id="f-company" name="company" type="text" tabindex="-1" autocomplete="off"></div>
        <div class="foot"><button class="btn" type="submit"><span>{esc(s["cta"])}</span><i>→</i></button><p class="cap">Нажимая кнопку, вы соглашаетесь с {pol}. Без рассылок: один звонок или сообщение по делу.</p></div>
        <p class="msg" role="alert"></p><input type="hidden" name="diag" value="">
      </form>'''
    if inner: return '<span class="lbl" style="display:block;margin-bottom:22px">Заявка</span>' + formhtml
    return (f'<section class="sec dark wrap" id="zayavka"><div class="grid"><div class="c5 rv"><span class="lbl">Первый шаг</span><h2 class="h2" style="margin-top:14px">{s["hero_cta_h2"]}</h2><div class="rule"></div>'
            f'<p class="txt">{t(s["first_step_text"], "Первый шаг")}</p><p class="cap" style="margin-top:18px">Если удобнее без формы: <a href="{tg}" rel="noopener" style="text-decoration:underline;text-underline-offset:3px">Telegram</a>.</p></div>'
            f'<div class="c6 c6r rv">{formhtml}</div></div></section>')

def ladder(cur=None, dark=False):
    """Лестница услуг с зачётами. Текущая подсвечена."""
    rows = []
    for i, slug in enumerate(ORDER):
        s = BY[slug]; n = f'{i+1:02d}'
        cls = ' '.join(filter(None, ['cur' if slug == cur else '', 'flag' if s.get('flagship') else '']))
        title = s['title']
        note = s['price'].get('note', '')
        href = f'/uslugi/{slug}/'
        inner = f'<span class="n">{n}</span><span class="t">{esc(title)}<small>{t(s["duration"])}</small></span><span class="d">{t(note)}</span><span class="p">{esc(s["price"]["display"])}</span><span class="a">{"Вы здесь" if slug == cur else "Подробнее <i>→</i>"}</span>'
        rows.append(f'<li class="{cls}">' + (f'<a href="{href}">{inner}</a>' if slug != cur else f'<a aria-current="page">{inner}</a>') + '</li>')
        if slug == 'audit-proekta':
            rows.append('<li class="off"><span>↓ Аудит засчитывается в стоимость концепции</span></li>')
    for slug in SIDE:
        s = BY[slug]
        inner = f'<span class="n">·</span><span class="t">{esc(s["title"])}<small>{esc(s["short"])}</small></span><span class="d">{t(s["duration"])}</span><span class="p">{esc(s["price"]["display"])}</span><span class="a">{"Вы здесь" if slug == cur else "Подробнее <i>→</i>"}</span>'
        rows.append(f'<li class="side{" cur" if slug == cur else ""}">' + (f'<a href="/uslugi/{slug}/">{inner}</a>' if slug != cur else f'<a aria-current="page">{inner}</a>') + '</li>')
    if SIDE: rows.insert(len(rows) - len(SIDE), '<li class="off sidehead"><span>Отдельно</span></li>')
    entry = data['ladder'].get('entry')
    first = (f'<li class="entry"><a href="#zayavka"><span class="n">00</span><span class="t">{esc(entry["title"])}<small>{esc(entry["text"])}</small></span><span class="d"></span><span class="p">{esc(entry["price"])}</span><span class="a">Начать <i>↓</i></span></a></li>' if entry else '')
    return f'<ol class="ladder">{first}{"".join(rows)}</ol>'


def others(cur=None):
    """«Другие услуги»: короткий список с ценами."""
    rows = []
    for slug in ORDER + SIDE:
        if slug == cur: continue
        s = BY[slug]
        rows.append(f'<li><a href="/uslugi/{slug}/"><span class="t">{esc(s["title"])}<small>{esc(s["short"])}</small></span><span class="p">{esc(s["price"]["display"])}<small>{esc(plain(s["duration"]) or "срок по объёму")}</small></span><span class="a">Подробнее <i>→</i></span></a></li>')
    return '<ul class="others">' + ''.join(rows) + '</ul>'

def doors_block():
    """Три двери: вопрос клиента его словами, ответ, срок и цена, ссылка на услугу."""
    _ctx['block'] = 'Три двери'
    h = data['hub_page']
    cards = ''
    for x in h['doors']:
        cards += (f'<a class="door rv" href="/uslugi/{x["service"]}/"><span class="num">{x["n"]}</span>'
                  f'<h3 class="h3">{esc(x["q"])}</h3><p class="txt">{esc(x["a"])}</p>'
                  f'<span class="meta cap">{esc(x["meta"])}</span><span class="arrow">{esc(x["label"])} <i>→</i></span></a>')
    return f'<section class="sec wrap" id="s-chego-nachat"><div class="doors">{cards}</div><p class="txt side rv">{h["doors_side"]}</p></section>'

def scope_block():
    _ctx['block'] = 'Границы работы'
    c = data['hub_page']['scope']
    return f'<section class="sec stone wrap" id="granicy"><div class="grid"><div class="c4 rv"><span class="lbl">{esc(c["lbl"])}</span></div><div class="c7 c7r rv"><p class="txt" style="max-width:60ch;font-size:clamp(17px,1.4vw,22px);line-height:1.45;color:var(--ink)">{esc(c["text"])}</p></div></div></section>'

def diag_block(page_slug):
    """Диагност: четыре вопроса, карточка с рекомендацией, форма с ответами."""
    _ctx['block'] = 'Диагност'
    dg = data['hub_page']['diagnostic']
    qs = ''
    for q in dg['q']:
        typ = 'checkbox' if q.get('multi') else 'radio'
        opts = ''.join(f'<label class="opt"><input type="{typ}" name="dq_{q["id"]}" value="{v}"><span>{esc(l)}</span></label>' for v, l in q['opts'])
        qs += f'<fieldset class="dq"><legend class="lbl">{esc(q["t"])}</legend><div class="opts">{opts}</div></fieldset>'
    form = form_block({'slug': page_slug, 'title': 'Заявка после диагноста', 'hero_cta_h2': '', 'first_step_text': '', 'cta': 'Прислать информацию об участке'}, inner=True)
    return (f'<section class="sec dark wrap" id="zayavka"><div class="grid">'
            f'<div class="c5 rv"><span class="lbl">Первый шаг</span><h2 class="h2" style="margin-top:14px">{dg["title"]}</h2><div class="rule"></div><p class="txt">{esc(dg["lead"])}</p>'
            f'<div class="diag" id="diag" data-prefix="{esc(dg["result_prefix"])}" data-note="{esc(dg["note_small"])}">{qs}</div>'
            f'<div class="dres" id="dres" hidden><span class="lbl">Рекомендация</span><h3 class="h3 rt"></h3><p class="txt rs"></p><ul class="list rd"></ul><p class="cap rn" hidden></p><a class="arrow rl" href="#">Подробнее <i>→</i></a></div></div>'
            f'<div class="c6 c6r rv">{form}</div></div></section>')

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
         "offers": {"@type": "Offer", "price": s['price']['value'], "priceCurrency": "RUB", "description": s['price']['display'] + ', ' + plain(s['duration'])}},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "Услуги", "item": SITE + '/uslugi/'}, {"@type": "ListItem", "position": 3, "name": s['title'], "item": url}]},
        faq_ld]}
    s.setdefault('hero_cta_h2', 'Расскажите <em>о проекте</em>')
    s.setdefault('first_step_text', 'Ответим в ближайший рабочий день и скажем, с чего имеет смысл начинать.')
    report = cfg['report_example']['url']
    report_link = (f'<a class="arrow" href="{report}" data-goal="report_example" target="_blank" rel="noopener">Посмотреть пример отчёта <i>↗</i></a>' if report
                   else '<a class="arrow" href="#zayavka" data-goal="report_example">Прислать пример отчёта <i>↓</i></a>')
    if not report: TODOS.append((_ctx['page'], 'Обложка, кнопка «Посмотреть пример отчёта»', 'Обезличенный пример отчёта в PDF, 4-6 страниц. Пока файла нет, кнопка ведёт на форму'))

    # 1. обложка
    photo = (f'<figure class="photo rv"><img src="{base}_m.webp" srcset="{srcset}" sizes="100vw" width="2400" height="1409" alt="{esc(img["alt"])}" fetchpriority="high" decoding="async">'
             f'<figcaption class="cap">{esc(img.get("caption", ""))}</figcaption></figure>' if has_img else '<div class="photo empty rv" role="img" aria-label="Место для фотографии"></div>')
    if not has_img: TODOS.append((_ctx['page'], 'Обложка', f'Фотография на обложку услуги «{s["title"]}»'))
    _ctx['block'] = 'Обложка'
    f2 = s.get('fact2', {})
    hero = (f'<section class="hero wrap">{crumbs([("Главная", "/"), ("Услуги", "/uslugi/"), (s["title"], None)])}'
            f'<div class="meta"><span class="lbl">{t(s["duration"])}</span><span class="lbl">{esc(s["price"]["display"])}</span></div>'
            f'<h1 class="h1">{s.get("h1", esc(s["title"]))}</h1><p class="lead">{t(s.get("result_line") or s["promise"])}</p>'
            f'<div class="facts"><div><b>{esc(s["price"]["display"])}</b><span class="cap">{t(s["duration"])}</span></div>'
            f'<div><b>{esc(f2.get("b", ""))}</b><span class="cap">{t(f2.get("cap", s["price"]["note"]))}</span></div></div>'
            f'<div class="actions"><a class="btn" href="#zayavka" data-goal="cta_click">{esc(s["cta"])} <i>→</i></a>{report_link}</div>{photo}</section>')

    # 2. кому подходит
    _ctx['block'] = 'Кому подходит'
    li = lambda items, mark: ''.join(f'<li><i>{mark}</i><p>{t(x)}</p></li>' for x in items)
    who = (f'<section class="sec wrap" id="komu"><div class="head"><h2 class="h2 rv">Кому подходит <em>и кому нет</em></h2><p class="txt rv">{t(s.get("who_intro", ""))}</p></div>'
           f'<div class="two"><div class="rv"><div class="word">Подходит</div><ul class="list">{li(s["for_whom"], "+")}</ul></div>'
           f'<div class="rv"><div class="word">Не подходит</div><ul class="list x">{li(s["not_for_whom"], "×")}</ul></div></div></section>')

    # 3. что получаете: пять на виду
    _ctx['block'] = 'Что получаете на выходе'
    dl = s['deliverables']; vis, rest = dl[:5], dl[5:]
    dl_html = '<ol class="deliv">' + ''.join(f'<li><p>{t(x)}</p></li>' for x in vis) + '</ol>'
    if rest:
        dl_html += f'<details class="moredl"><summary class="arrow">Ещё {len(rest)} <i>↓</i></summary><ol class="deliv" start="6">' + ''.join(f'<li><p>{t(x)}</p></li>' for x in rest) + '</ol></details>'
    frame_img = ''
    if s.get('artifact_image'):
        ai = s['artifact_image']; frame_img = f'<img src="/assets/img/uslugi/{ai["src"]}_m.webp" alt="{esc(ai["alt"])}" loading="lazy" decoding="async">'
    else:
        TODOS.append((_ctx['page'], 'Что получаете на выходе', 'Снимок разворота отчёта или экрана с документом для правой колонки. Пока контейнер пустой'))
    fcap = esc(s['artifact_image'].get('caption', '')) if frame_img else ''
    out = (f'<section class="sec dark wrap" id="na-vyhode"><div class="grid">'
           f'<div class="c7 rv"><span class="lbl">Что получаете на выходе</span><h2 class="h2" style="margin-top:14px">Что окажется <em>у вас в руках</em></h2><div class="rule"></div><div style="margin-top:28px">{dl_html}</div></div>'
           f'<div class="c4 c4r rv" style="align-self:end"><div class="frame{" has" if frame_img else ""}">{frame_img}<span class="cap">{fcap}</span></div><p class="cap" style="margin-top:14px">{report_link}</p></div></div></section>')

    # 4. стоимость
    _ctx['block'] = 'Стоимость'
    moves = s['price'].get('what_moves_it')
    moves_html = ('<ul class="list">' + ''.join(f'<li><i>·</i><p>{t(x)}</p></li>' for x in moves) + '</ul>') if moves else ''
    scale = f'<p class="txt" style="margin-top:18px">{t(s["price"]["scale_argument"])}</p>' if s['price'].get('scale_argument') else ''
    nxt = (f' Следующий шаг: {BY[ORDER[n]]["title"]}, {BY[ORDER[n]]["price"]["display"]}.' if 0 < n < len(ORDER) else '')
    price = (f'<section class="sec stone wrap price" id="stoimost"><div class="grid">'
             f'<div class="c5 rv"><span class="lbl" style="display:block">Стоимость</span><b class="big" style="margin-top:14px">{esc(s["price"]["display"])}</b><span class="cap" style="display:block;margin-top:8px">{t(s["duration"])}</span>'
             f'<p class="txt" style="margin-top:22px">{t(s["price"]["note"])}.{esc(nxt)}</p>{scale}'
             f'<p class="txt" style="margin-top:14px"><span class="lbl" style="display:block;margin-bottom:6px">Оплата</span>{t(s["payment"])}</p></div>'
             f'<div class="c6 c6r rv"><span class="lbl" style="display:block;margin-bottom:8px">Что двигает цену</span>{moves_html}<p class="txt" style="margin-top:22px">{t(s.get("price_long", ""))}</p>'
             f'<div class="actions" style="margin-top:28px"><a class="btn" href="#zayavka" data-goal="cta_click">{esc(s["cta"])} <i>→</i></a></div></div></div></section>')

    # 5. кейс
    _ctx['block'] = 'Кейс'
    ref = s.get('case_ref', '')
    cs = [c for c in cases if c['id'] == ref] or ([] if is_todo(ref) else [c for c in cases if slug in c['services']])
    if cs:
        c = cs[0]
        if slug not in c.get('primary', c['services'][:1]): TODOS.append((_ctx['page'], 'Кейс', f'Кейс именно по услуге «{s["title"]}». Пока показан смежный кейс «{c["title"]}»'))
        row = lambda k, v: f'<div><dt>{k}</dt><dd>{t(v)}</dd></div>'
        case_html = (f'<div class="case rv"><div class="fig"><b>{esc(c["figure"])}</b><p class="cap">{esc(c["figure_caption"])}</p><p class="cap" style="margin-top:18px">{esc(c["meta"])}</p></div>'
                     f'<div><h3 class="h3" style="margin-bottom:18px">{esc(c["title"])}</h3><dl>{row("Ситуация", c["situation"])}{row("Что нашли", c["found"])}{row("Что поменяли", c["changed"])}{row("Что изменилось", c["result"])}</dl></div></div>')
    else:
        case_html = f'<p class="txt rv">{t(ref if is_todo(ref) else "[[ЗАПОЛНИТЬ: кейс по услуге «" + s["title"] + "»]]")}</p>'
    review = s.get('review')
    review_html = (f'<blockquote class="quote rv"><p>{esc(review["text"])}</p><footer class="cap">{esc(review["name"])}, {esc(review["role"])}, {esc(review["project"])}</footer></blockquote>' if review and not is_todo(review.get('text', '')) else '')
    if not review_html: TODOS.append((_ctx['page'], 'Кейс, отзыв', f'Отзыв клиента по услуге «{s["title"]}»: имя, должность, проект, 2-4 предложения. Пока блок не выводится'))
    case = f'<section class="sec wrap" id="keis"><div class="head"><h2 class="h2 rv">Кейс <em>по этой работе</em></h2><p class="txt rv">Клиентские проекты не называем, собственные называем прямо.</p></div>{case_html}{review_html}</section>'

    # 6. подробнее о работе
    _ctx['block'] = 'Подробнее о работе'
    rl = ''.join(f'<li><b>{i+1:02d}</b><p>{t(x)}</p></li>' for i, x in enumerate(s['results']))
    st = ''.join(f'<li><span class="lbl">{t(x["term"])}</span><h3 class="h3">{esc(x["name"])}</h3><p>{t(x["out"])}</p></li>' for x in s['stages'])
    ni = ''.join(f'<li><i>×</i><p>{t(x)}</p></li>' for x in s['not_included']); np_ = ''.join(f'<li><i>×</i><p>{t(x)}</p></li>' for x in s['not_promised'])
    fq = ''.join(f'<details><summary>{esc(q["q"])}<i></i></summary><div class="a">{t(q["a"])}</div></details>' for q in s['faq'])
    more = (f'<section class="sec stone wrap" id="podrobnee"><div class="head"><h2 class="h2 rv">Подробнее <em>о работе</em></h2><p class="txt rv">Этапы, границы и вопросы с первых звонков. Для тех, кто принимает решение.</p></div>'
            f'<details class="dsec rv"><summary><span class="word">Что сможете решить по итогам</span><i></i></summary><ol class="res n{len(s["results"])}">{rl}</ol></details>'
            f'<details class="dsec rv"><summary><span class="word">Как устроена работа</span><i></i></summary><ol class="steps" style="--n:{len(s["stages"])}">{st}</ol></details>'
            f'<details class="dsec rv"><summary><span class="word">Что не входит и чего не обещаем</span><i></i></summary><div class="two"><div><ul class="list x">{ni}</ul></div><div><ul class="list x">{np_}</ul></div></div></details>'
            f'<details class="dsec rv" id="voprosy"><summary><span class="word">Вопросы</span><i></i></summary><div class="faq">{fq}</div></details></section>')

    # 7. форма и другие услуги
    _ctx['block'] = 'Первый шаг'
    form = form_block(s)
    _ctx['block'] = 'Другие услуги'
    oth = f'<section class="sec wrap" id="uslugi"><div class="head"><h2 class="h2 rv">{data["ladder"]["others_title"]}</h2><p class="txt rv">{t(data["ladder"]["others_lead"])}</p></div><div class="rv">{others(cur=slug)}</div></section>'

    body = f'<body data-page="/uslugi/{slug}/" data-service="{slug}">{nav(slug)}<main>{hero}{who}{out}{price}{case}{more}{form}{oth}</main>{footer()}</body></html>'
    pre = {"src": f'{base}_m.webp', "srcset": srcset} if has_img else None
    return head(seo_title, seo_desc, url, og, ld, pre) + body

# ---------- общие блоки хаба и главной ----------
def facts_strip():
    items = [('17 лет', 'в загородном девелопменте'), ('10', 'посёлков построили и ведём'), ('7 000+', 'жителей живут в наших посёлках'), ('1/2', 'продаж приходит по рекомендации')]
    return '<div class="facts4 rv">' + ''.join(f'<div><b>{esc(a)}</b><span class="cap">{esc(b)}</span></div>' for a, b in items) + '</div>'

def cases_block(ids=None, title='Кейсы <em>клиентов</em>'):
    _ctx['block'] = 'Кейсы'
    cs = [c for c in cases if not ids or c['id'] in ids]
    cards = ''
    for c in cs:
        cards += (f'<a class="ccard rv" href="/uslugi/{c["primary"][0]}/#keis"><div class="fig"><b>{esc(c["figure"])}</b><p class="cap">{esc(c["figure_caption"])}</p></div>'
                  f'<h3 class="h3">{esc(c["title"])}</h3><p class="txt">{esc(c.get("summary", plain(c["changed"])))}</p>'
                  f'<span class="arrow">Как это было <i>→</i></span></a>')
    return f'<section class="sec wrap" id="keisy"><div class="head"><h2 class="h2 rv">{title}</h2><p class="txt rv">Два случая из работы бюро. Клиентские проекты не называем, собственные называем прямо.</p></div><div class="cgrid">{cards}</div></section>'

def portfolio_block(per_cat=2):
    """Плитки портфолио: кадры из реестра портфолио (portfolio/projects.json, симлинк на соседний репозиторий)."""
    _ctx['block'] = 'Портфолио'
    h = data['hub_page']['home_portfolio']
    reg_path = os.path.join(ROOT, 'portfolio', 'projects.json')
    tiles = ''
    if os.path.exists(reg_path):
        reg = json.load(open(reg_path))
        proot = cfg['site']['portfolio']
        order = ['built', 'settlements', 'houses']
        for c in sorted(reg['categories'], key=lambda c: order.index(c['id']) if c['id'] in order else 9):
            for pr in [x for x in reg['projects'] if x['category'] == c['id']][:per_cat]:
                cv = proot + pr['cover']
                tiles += (f'<a class="tile rv" href="{proot}{pr["slug"]}/"><span class="ph"><img src="{cv}_s.webp" srcset="{cv}_s.webp 800w, {cv}_m.webp 1400w" sizes="(max-width:900px) 100vw, 33vw" alt="{esc(pr["title"])}" loading="lazy" decoding="async"></span>'
                          f'<span class="lbl">{esc(c["short"])}{(" · " + esc(pr["year"])) if pr.get("year") else ""}</span><span class="t">{esc(pr["title"])}</span><span class="cap">{esc(pr["meta"])}</span></a>')
    else:
        TODOS.append((_ctx['page'], 'Портфолио', 'Реестр портфолио не найден при сборке: положить симлинк portfolio → соседний репозиторий'))
    return (f'<section class="sec wrap" id="portfolio"><div class="head"><h2 class="h2 rv">{h["title"]}</h2><p class="txt rv">{esc(h["lead"])}</p></div>'
            f'<div class="tiles">{tiles}</div><p class="rv" style="margin-top:32px"><a class="arrow" href="{cfg["site"]["portfolio"]}">Всё портфолио <i>→</i></a></p></section>')

def generic_form(slug, title, h2, text, cta):
    return form_block({'slug': slug, 'title': title, 'hero_cta_h2': h2, 'first_step_text': text, 'cta': cta})

def hero_photo(src, alt, caption):
    base = f'/assets/img/uslugi/{src}'
    return f'<figure class="photo rv"><img src="{base}_m.webp" srcset="{base}_s.webp 800w, {base}_m.webp 1400w, {base}.webp 2400w" sizes="100vw" width="2400" height="1409" alt="{esc(alt)}" fetchpriority="high" decoding="async"><figcaption class="cap">{esc(caption)}</figcaption></figure>'

# ---------- хаб ----------
def hub_page():
    _ctx['page'] = '/uslugi/'; _ctx['block'] = 'Хаб'
    url = f'{SITE}/uslugi/'; h = data['hub_page']
    title = 'Услуги концепт-бюро «Хрустальный»: сценарии для участка, концепция посёлка, аудит проекта'
    desc = 'С чего начать загородный проект: сценарии для участка, продуктовая концепция посёлка, аудит проекта, упаковка. Цены и сроки открыты. Четыре вопроса, чтобы понять, что нужно именно вам.'
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "Услуги", "item": url}]},
        {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f'{SITE}/uslugi/{sl}/', "name": BY[sl]['title']} for i, sl in enumerate(ORDER + SIDE)]}]}
    body = (f'<body data-page="/uslugi/" data-service="hub">{nav()}<main>'
            f'<section class="hero wrap short">{crumbs([("Главная", "/"), ("Услуги", None)])}<div class="meta"><span class="lbl">Услуги</span><span class="lbl">Четыре работы и два отдельных входа</span></div>'
            f'<h1 class="h1">С чего <em>начать</em></h1><p class="lead">{esc(h["lead"])}</p></section>'
            f'<section class="sec wrap" id="uslugi" style="padding-top:clamp(40px,6vh,72px)"><div class="rv">{ladder()}</div><p class="txt side rv" style="margin-top:28px;max-width:70ch">{h["doors_side"]}</p></section>{scope_block()}{portfolio_block(per_cat=1)}{diag_block("hub")}</main>{footer()}</body></html>')
    return head(title, desc, url, f'{SITE}/assets/img/uslugi/hub_aero_og.jpg', ld) + body

# ---------- главная ----------
def home_page():
    _ctx['page'] = '/'; _ctx['block'] = 'Главная'
    url = SITE + '/'; h = data['hub_page']
    title = 'Концепт-бюро «Хрустальный»: что строить на земле и сколько это принесёт'
    desc = 'Концепции коттеджных посёлков и загородных проектов: сценарии для участка, продуктовая концепция, аудит проекта. Семнадцать лет строим и продаём посёлки, чужие проекты считаем так же, как свои.'
    ld = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": cfg['site']['name'], "url": url, "sameAs": [cfg['site']['home'], cfg['contacts']['channel']], "description": desc, "areaServed": "RU",
          "founder": {"@type": "Person", "name": "Кристина Яковенко", "jobTitle": "сооснователь и директор по развитию"}}
    body = (f'<body data-page="/" data-service="home">{nav()}<main><section class="hero wrap">'
            f'<div class="meta"><span class="lbl">Концепт-бюро «Хрустальный»</span><span class="lbl">Загородный девелопмент</span><span class="lbl">Иркутск · Челябинск · Братск · Подмосковье</span></div>'
            f'<h1 class="h1">{h["hero"]["title"]}</h1><p class="lead">{esc(h["hero"]["lead"])}</p>'
            f'<div class="actions"><a class="btn" href="#s-chego-nachat" data-goal="cta_click">С чего начать <i>↓</i></a><a class="arrow" href="{cfg["site"]["portfolio"]}">Портфолио <i>→</i></a></div>'
            f'{hero_photo("home_aero", "Аэросъёмка Хрустального парка: построенные очереди, свободная земля и вода", "Хрустальный парк, Иркутск. Проект группы «Хрустальный»")}</section>'
            f'<section class="sec wrap" id="fakty" style="padding-bottom:0">{facts_strip()}</section>{doors_block()}{scene_block()}{scope_block()}'
            f'{portfolio_block()}{awards_line()}'
            f'{diag_block("home")}</main>{footer()}</body></html>')
    return head(title, desc, url, f'{SITE}/assets/img/uslugi/home_aero_og.jpg', ld) + body

# ---------- страницы бюро: о бюро, контакты, обучение, политика, 404 ----------
def scene_block():
    """Тёмная полноэкранная сцена на главной: фото с параллаксом, гигантское слово, три строки."""
    _ctx['block'] = 'Сцена'
    sc = site['home']['scene']; base = f'/assets/img/uslugi/{sc["photo"]}'
    lines = ''.join(f'<li class="rv">{esc(x)}</li>' for x in sc['lines'])
    return (f'<section class="scene" id="my-sami"><div class="ph" data-parallax><img src="{base}_m.webp" srcset="{base}_s.webp 800w, {base}_m.webp 1400w, {base}.webp 2400w" sizes="100vw" alt="{esc(sc["alt"])}" loading="lazy" decoding="async"></div>'
            f'<div class="wrap in"><h2 class="giant rv">{esc(sc["word"])}</h2><ul class="lines">{lines}</ul><a class="arrow rv" href="{sc["link"]}">{esc(sc["cta"])} <i>→</i></a></div></section>')

def awards_line():
    items = ''.join(f'<span>{esc(x)}</span>' for x in site['home']['awards_line'])
    return f'<section class="wrap awline rv"><span class="lbl">Награды посёлков группы</span><div class="items">{items}</div><a class="arrow" href="/o-byuro/#nagrady">Все награды <i>→</i></a></section>'

def about_page():
    _ctx['page'] = '/o-byuro/'; _ctx['block'] = 'О бюро'
    a = site['about']; url = f'{SITE}/o-byuro/'
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": SITE + '/#org', "name": cfg['site']['name'], "url": SITE + '/', "logo": SITE + '/assets/img/favicon.svg', "foundingDate": "2009",
         "address": {"@type": "PostalAddress", "addressLocality": "Иркутск", "addressCountry": "RU"}, "sameAs": [x['url'] for x in site['contacts']['social']],
         "founder": [{"@type": "Person", "name": t_['name'], "jobTitle": plain(t_['role'])} for t_ in a['team']],
         "award": [plain(x['t']) for x in a['awards']], "areaServed": "RU"},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "О бюро", "item": url}]}]}
    story = ''.join(f'<div class="rv"><span class="num">0{i+1}</span><h3 class="h3" style="margin:12px 0 10px">{esc(x["t"])}</h3><p class="txt">{t(x["d"])}</p></div>' for i, x in enumerate(a['story']))
    team = ''
    for m in a['team']:
        ph = (f'<span class="ph"><img src="/assets/img/uslugi/{m["photo"]}_m.webp" alt="{esc(m["alt"])}" loading="lazy" decoding="async"></span>' if m.get('photo') else '<span class="ph empty"></span>')
        if not m.get('photo'): TODOS.append((_ctx['page'], 'Команда', f'Портрет: {m["name"]}'))
        team += f'<div class="member rv">{ph}<h3 class="h3">{esc(m["name"])}</h3><p class="cap">{t(m["role"])}</p><p class="txt" style="margin-top:12px">{t(m["text"])}</p></div>'
    fp = a['founders_photo']; fbase = f'/assets/img/uslugi/{fp["src"]}'
    rules = ''.join(f'<li><span class="num">0{i+1}</span><div><h3 class="h3">{esc(x["t"])}</h3><p class="txt" style="margin-top:10px">{esc(x["d"])}</p></div></li>' for i, x in enumerate(data['hub_page']['how_we_work']['items']))
    awards = ''.join(f'<li class="rv"><span class="y">{esc(x["year"])}</span><span>{esc(x["t"])}</span></li>' for x in a['awards'])
    body = (f'<body data-page="/o-byuro/" data-service="about">{nav()}<main>'
            f'<section class="hero wrap">{crumbs([("Главная", "/"), ("О бюро", None)])}<div class="meta"><span class="lbl">О бюро</span><span class="lbl">Иркутск · работаем по всей России</span></div>'
            f'<h1 class="h1">{a["h1"]}</h1><p class="lead">{esc(a["lead"])}</p>'
            f'<div class="actions"><a class="btn" href="/uslugi/" data-goal="cta_click">Услуги бюро <i>→</i></a><a class="arrow" href="/portfolio/">Портфолио <i>→</i></a></div>'
            f'{hero_photo("street_french2", "Улица Французского квартала Хрустального парка: дома, аллея, вечернее солнце", "Хрустальный парк, Иркутск. Проект группы «Хрустальный»")}</section>'
            f'<section class="sec wrap" id="fakty" style="padding-bottom:0">{facts_strip()}</section>'
            f'<section class="sec wrap" id="istoriya"><div class="story">{story}</div></section>'
            f'<section class="sec stone wrap" id="komanda"><div class="head"><h2 class="h2 rv">Кто <em>ведёт</em> проекты</h2><p class="txt rv">Гипотезы, продукт и защита на всех гейтах не делегируются: их ведут сооснователи.</p></div>'
            f'<div class="teamgrid"><figure class="founders rv"><img src="{fbase}_m.webp" srcset="{fbase}_s.webp 800w, {fbase}_m.webp 1400w" sizes="(max-width:900px) 100vw, 40vw" alt="{esc(fp["alt"])}" loading="lazy" decoding="async"><figcaption class="cap">{t(fp["caption"])}</figcaption></figure><div class="members">{team}</div></div></section>'
            f'<section class="sec dark wrap" id="pravila"><div class="head"><h2 class="h2 rv">{a["principles_title"]}</h2><p class="txt rv">Из рабочего стандарта бюро.</p></div><ol class="rules">{rules}</ol></section>'
            f'<section class="sec wrap" id="nagrady"><div class="head"><h2 class="h2 rv">{a["awards_title"]}</h2><p class="txt rv">{t(a["awards_note"])}</p></div><ul class="awards">{awards}</ul></section>'
            f'<section class="sec stone wrap" id="geo"><div class="grid"><div class="c4 rv"><span class="lbl">{esc(a["geo_title"])}</span></div><div class="c7 c7r rv"><p class="txt" style="max-width:60ch;font-size:clamp(17px,1.4vw,22px);line-height:1.45;color:var(--ink)">{esc(a["geo_text"])}</p></div></div></section>'
            f'{generic_form("about", "Заявка со страницы о бюро", "Пришлите <em>информацию</em> об участке", "Кадастровый номер, схема, стадия и задача своими словами. За 30 минут разговора скажем, что там можно, а что нельзя, и с чего имеет смысл начинать.", "Прислать информацию об участке")}'
            f'</main>{footer()}</body></html>')
    return head(a['seo']['title'], a['seo']['description'], url, f'{SITE}/assets/img/uslugi/street_french2_og.jpg', ld) + body

def contacts_page():
    _ctx['page'] = '/kontakty/'; _ctx['block'] = 'Контакты'
    c = site['contacts']; url = f'{SITE}/kontakty/'
    title = 'Контакты концепт-бюро «Хрустальный», Иркутск: телефон, Telegram, почта'
    desc = 'Связаться с концепт-бюро «Хрустальный»: телефон, Telegram, почта. Бюро в Иркутске, работаем с девелоперами и землевладельцами по всей России.'
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "ProfessionalService", "@id": SITE + '/#business', "name": cfg['site']['name'], "url": SITE + '/', "telephone": c['phone_tel'], "email": c['email'],
         "address": {"@type": "PostalAddress", "addressLocality": "Иркутск", "addressCountry": "RU"}, "areaServed": "RU", "sameAs": [x['url'] for x in c['social']],
         "openingHours": "Mo-Fr 09:00-18:00"},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "Контакты", "item": url}]}]}
    soc = ''.join(f'<a href="{x["url"]}" rel="noopener">{esc(x["title"])}</a>' for x in c['social'])
    body = (f'<body data-page="/kontakty/" data-service="contacts">{nav()}<main>'
            f'<section class="hero wrap short">{crumbs([("Главная", "/"), ("Контакты", None)])}<div class="meta"><span class="lbl">Контакты</span><span class="cap">{esc(c["hours"])}</span></div>'
            f'<h1 class="h1">Напишите <em>или позвоните</em></h1><p class="lead">Первый разговор занимает полчаса и ничего не стоит. Удобнее всего Telegram: там отвечаем быстрее всего.</p></section>'
            f'<section class="sec wrap" id="kanaly"><div class="contacts">'
            f'<div class="rv"><span class="lbl">Telegram</span><a class="big-link" href="{c["telegram_manager"]}" rel="noopener">Написать в Telegram <i>→</i></a><p class="cap">Заявки и вопросы по проектам</p></div>'
            f'<div class="rv"><span class="lbl">Телефон</span><a class="big-link" href="tel:{c["phone_tel"]}">{esc(c["phone_display"])}</a><p class="cap">{t(c["phone_note"])}</p></div>'
            f'<div class="rv"><span class="lbl">Почта</span><a class="big-link" href="mailto:{c["email"]}">{esc(c["email"])}</a><p class="cap">{t(c["email_note"])}</p></div>'
            f'<div class="rv"><span class="lbl">Офис</span><p class="big-link" style="cursor:default">{esc(c["city"])}</p><p class="cap">{t(c["address"])}</p></div>'
            f'</div><div class="rv" style="margin-top:48px"><span class="lbl" style="display:block;margin-bottom:12px">Где читать и смотреть</span><div class="soc">{soc}</div></div></section>'
            f'{generic_form("contacts", "Заявка со страницы контактов", "Пришлите <em>информацию</em> об участке", "Кадастровый номер, схема, стадия и задача своими словами. Ответим в ближайший рабочий день и скажем, с чего имеет смысл начинать.", "Прислать информацию об участке")}'
            f'<section class="sec wrap" id="rekvizity"><span class="lbl">Реквизиты</span><p class="cap" style="margin-top:12px">{esc(c["legal"]["name"])} · ИНН {esc(c["legal"]["inn"])}. {t(c["legal"]["inn_note"])}</p></section>'
            f'</main>{footer()}</body></html>')
    return head(title, desc, url, None, ld) + body

def education_page():
    _ctx['page'] = '/obuchenie/'; _ctx['block'] = 'Обучение'
    e = site['education']; url = f'{SITE}/obuchenie/'
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "Обучение", "item": url}]}
    cards = ''.join(f'<article class="edu rv"><h2 class="h3" style="font-size:clamp(26px,2.4vw,36px)">{esc(x["t"])}</h2><p class="txt" style="margin-top:14px">{esc(x["d"])}</p><p class="big" style="font-size:clamp(28px,3vw,44px);margin-top:22px">{esc(x["price"])}</p><a class="btn" href="{x["url"]}" rel="noopener" style="margin-top:22px">{esc(x["cta"])} <i>↗</i></a></article>' for x in e['items'])
    body = (f'<body data-page="/obuchenie/" data-service="education">{nav()}<main>'
            f'<section class="hero wrap short">{crumbs([("Главная", "/"), ("Обучение", None)])}<div class="meta"><span class="lbl">Обучение</span><span class="lbl">Отдельная ветка бюро</span></div>'
            f'<h1 class="h1">{e["h1"]}</h1><p class="lead">{esc(e["lead"])}</p></section>'
            f'<section class="sec wrap" id="formaty"><div class="edugrid">{cards}</div><p class="txt rv" style="margin-top:40px;max-width:60ch">{esc(e["note"])} <a class="arrow" href="/uslugi/" style="font-size:16px">Услуги бюро <i>→</i></a></p></section>'
            f'{hero_photo("team_kristina_stage", "Кристина Яковенко на сцене, за спиной планировки домов", "Кристина Яковенко, выступление для застройщиков")}'
            f'</main>{footer()}</body></html>')
    return head(e['seo']['title'], e['seo']['description'], url, f'{SITE}/assets/img/uslugi/team_kristina_stage_og.jpg', ld) + body

def policy_page():
    _ctx['page'] = '/politika/'; _ctx['block'] = 'Политика'
    c = site['contacts']; p = site['policy']; url = f'{SITE}/politika/'
    txt = f'''<p class="txt">Настоящая политика описывает, какие персональные данные собирает {esc(c["legal"]["name"])} (далее оператор) через сайт {SITE.replace("https://", "")}, зачем и как долго их хранит. {t(p["operator_note"])}</p>
<h2 class="h3" style="margin-top:36px">1. Какие данные собираем</h2><p class="txt">Имя, телефон или ник в Telegram, кадастровый номер или ссылку на проект и текст, который вы написали в форме. Технические данные: адрес страницы, с которой отправлена форма, метки рекламных кампаний, данные счётчика Яндекс.Метрики.</p>
<h2 class="h3" style="margin-top:28px">2. Зачем</h2><p class="txt">Чтобы связаться с вами по заявке, подготовиться к первому разговору и понять, какие страницы сайта помогают клиентам. Рассылок по заявкам не ведём.</p>
<h2 class="h3" style="margin-top:28px">3. Основание</h2><p class="txt">Ваше согласие, которое вы даёте, нажимая кнопку отправки формы, и статья 6 Федерального закона № 152-ФЗ «О персональных данных».</p>
<h2 class="h3" style="margin-top:28px">4. Кому передаём</h2><p class="txt">Заявка попадает в CRM-систему оператора (Битрикс24). Статистика посещений обрабатывается сервисом Яндекс.Метрика. Третьим лицам данные не продаём и не передаём.</p>
<h2 class="h3" style="margin-top:28px">5. Сколько храним</h2><p class="txt">Пока вы не попросите удалить данные или пока не пройдёт три года с последнего контакта.</p>
<h2 class="h3" style="margin-top:28px">6. Ваши права</h2><p class="txt">Вы можете запросить, какие данные о вас есть, исправить их или попросить удалить. Для этого напишите на <a href="mailto:{c["email"]}" style="text-decoration:underline">{esc(c["email"])}</a> или в <a href="{c["telegram_manager"]}" style="text-decoration:underline">Telegram</a>.</p>
<p class="cap" style="margin-top:36px">Редакция от {esc(p["updated"])}.</p>'''
    body = (f'<body data-page="/politika/" data-service="policy">{nav()}<main><section class="hero wrap short">{crumbs([("Главная", "/"), ("Политика обработки данных", None)])}'
            f'<h1 class="h1" style="font-size:clamp(40px,7vw,96px)">Политика <em>обработки данных</em></h1></section><section class="sec wrap" style="padding-top:24px"><div class="grid"><div class="c8">{txt}</div></div></section></main>{footer()}</body></html>')
    return head(p['title'] + '. Концепт-бюро «Хрустальный»', 'Какие данные собирает сайт концепт-бюро «Хрустальный», зачем, на каком основании и как их удалить.', url) + body

def notfound_page():
    _ctx['page'] = '/404.html'
    body = (f'<body data-page="/404" data-service="404">{nav()}<main><section class="hero wrap short"><div class="meta"><span class="lbl">Ошибка 404</span></div>'
            f'<h1 class="h1">Такой страницы <em>нет</em></h1><p class="lead">Возможно, адрес изменился при переезде сайта. Ниже всё, что есть.</p>'
            f'<div class="actions"><a class="btn" href="/uslugi/">Услуги <i>→</i></a><a class="arrow" href="/portfolio/">Портфолио <i>→</i></a><a class="arrow" href="/">Главная <i>→</i></a></div></section></main>{footer()}</body></html>')
    return head('Страница не найдена. Концепт-бюро «Хрустальный»', 'Страницы нет. Услуги, портфолио и контакты концепт-бюро «Хрустальный».', SITE + '/404.html') + body


# ---------- мероприятия ----------
def event_page(ev):
    slug = ev['slug']; _ctx['page'] = f'/{slug}/'; _ctx['block'] = 'Мероприятие'
    url = f'{SITE}/{slug}/'; f = ev['form']; hp = ev['hosts_photo']; hb = f'/assets/img/uslugi/{hp["src"]}'
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BusinessEvent", "name": "Бизнес-завтрак для загородных застройщиков, Екатеринбург", "description": plain(ev['seo']['description']),
         "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "startDate": "2026-10-02T10:00+05:00", "endDate": "2026-10-02T12:00+05:00",
         "location": {"@type": "Place", "name": "Центр Екатеринбурга, адрес сообщается участникам", "address": {"@type": "PostalAddress", "addressLocality": "Екатеринбург", "addressCountry": "RU"}},
         "organizer": {"@type": "Organization", "name": cfg['site']['name'], "url": SITE + '/'}, "isAccessibleForFree": True, "maximumAttendeeCapacity": 12, "url": url, "image": f'{SITE}{hb}_og.jpg',
         "performer": [{"@type": "Person", "name": h['name']} for h in ev['hosts']]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q['q'], "acceptedAnswer": {"@type": "Answer", "text": q['a']}} for q in ev['faq']]},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + '/'}, {"@type": "ListItem", "position": 2, "name": "Бизнес-завтрак в Екатеринбурге", "item": url}]}]}
    facts = ''.join(f'<div><b>{esc(x["b"])}</b><span class="cap">{esc(x["cap"])}</span></div>' for x in ev['facts'])
    topics = ''.join(f'<div class="rv"><span class="num">0{i+1}</span><h3 class="h3" style="margin:12px 0 10px">{esc(x["t"])}</h3><p class="txt">{esc(x["d"])}</p></div>' for i, x in enumerate(ev['topics']))
    hosts = ''.join(f'<div class="rv"><h3 class="h3">{esc(h["name"])}</h3><p class="cap" style="margin:6px 0 12px">{esc(h["role"])}</p><p class="txt">{esc(h["d"])}</p></div>' for h in ev['hosts'])
    li = lambda items, mark: ''.join(f'<li><i>{mark}</i><p>{esc(x)}</p></li>' for x in items)
    terms = ''.join(f'<li class="rv"><span class="lbl">{esc(x["t"])}</span><h3 class="h3" style="margin:10px 0 8px;font-size:22px">{esc(x["d"].split(".")[0])}</h3><p>{esc(".".join(x["d"].split(".")[1:]).strip())}</p></li>' for x in ev['terms'])
    fq = ''.join(f'<details{" open" if i == 0 else ""}><summary>{esc(q["q"])}<i></i></summary><div class="a">{esc(q["a"])}</div></details>' for i, q in enumerate(ev['faq']))
    interest = ''.join(f'<label class="opt"><input type="radio" name="interest" value="{v}"{" checked" if i == 0 else ""}><span>{esc(l)}</span></label>' for i, (v, l) in enumerate(f['interest']))
    tg = cfg['contacts']['manager']['telegram']
    success = f'<div class="success"><h2 class="h2">{f["success_h2"]}</h2><div class="rule"></div><p class="txt">{esc(f["success_text"])} <a href="{tg}" rel="noopener" style="text-decoration:underline;text-underline-offset:3px">Telegram</a>.</p></div>'
    form = (f'<form id="leadForm" class="form" novalidate data-kind="event" data-service-title="Бизнес-завтрак Екатеринбург" data-cta="{esc(f["cta"])}" data-success="{esc(success)}">'
            f'<div class="f"><label for="f-name">Имя</label><input id="f-name" name="name" type="text" autocomplete="name" required placeholder="Как к вам обращаться"><span class="err">Напишите имя</span></div>'
            f'<div class="f"><label for="f-contact">Телефон или Telegram</label><input id="f-contact" name="contact" type="text" inputmode="tel" autocomplete="tel" required placeholder="+7 ··· или @ник"><span class="err">Нужен телефон или ник в Telegram</span></div>'
            f'<div class="f"><label for="f-company">{esc(f["company_label"])}</label><input id="f-company" name="company_city" type="text" placeholder="Компания, город"></div>'
            f'<div class="f"><span class="lbl" style="display:block;margin-bottom:10px">{esc(f["interest_label"])}</span><div class="opts">{interest}</div></div>'
            f'<div class="f"><label for="f-question">{esc(f["question_label"])}</label><textarea id="f-question" name="question" rows="3" required placeholder="{esc(f["question_ph"])}"></textarea><span class="err">Напишите вопрос, по нему соберём повестку</span></div>'
            f'<div class="f" style="position:absolute;left:-9999px" aria-hidden="true"><label for="f-hp">Компания</label><input id="f-hp" name="company" type="text" tabindex="-1" autocomplete="off"></div>'
            f'<div class="foot"><button class="btn" type="submit"><span>{esc(f["cta"])}</span><i>→</i></button><p class="cap">Нажимая кнопку, вы соглашаетесь с <a href="/politika/">политикой обработки данных</a>. Один звонок накануне встречи и адрес, без рассылок.</p></div>'
            f'<p class="msg" role="alert"></p><input type="hidden" name="diag" value=""></form>'
            f'<!-- Место для виджета GetCourse, если решите собирать заявки через него: вставить код виджета вместо формы выше -->')
    body = (f'<body data-page="/{slug}/" data-service="{slug}">{nav()}<main>'
            f'<section class="hero wrap">{crumbs([("Главная", "/"), ("Бизнес-завтрак в Екатеринбурге", None)])}<div class="meta"><span class="lbl">{esc(ev["label"])}</span><span class="lbl">{esc(ev["date_prelim"])}</span></div>'
            f'<h1 class="h1">{ev["h1"]}</h1><p class="lead">{esc(ev["lead"])}</p><p class="cap" style="margin-top:14px;max-width:60ch">{esc(ev["date_note"])}</p>'
            f'<div class="facts">{facts}</div><div class="actions"><a class="btn" href="#zayavka" data-goal="cta_click">{esc(ev["cta"])} <i>→</i></a><a class="arrow" href="#o-chem">О чём поговорим <i>↓</i></a></div>'
            f'{hero_photo(ev["cover"]["src"], ev["cover"]["alt"], ev["cover"]["caption"])}</section>'
            f'<section class="sec wrap" id="o-chem"><div class="head"><h2 class="h2 rv">{ev["topics_title"]}</h2><p class="txt rv">{esc(ev["topics_lead"])}</p></div><div class="story">{topics}</div></section>'
            f'<section class="sec stone wrap" id="vedut"><div class="head"><h2 class="h2 rv">{ev["hosts_title"]}</h2><p class="txt rv">{esc(ev["hosts_lead"])}</p></div>'
            f'<div class="teamgrid"><figure class="founders rv"><img src="{hb}_m.webp" srcset="{hb}_s.webp 800w, {hb}_m.webp 1400w" sizes="(max-width:900px) 100vw, 40vw" alt="{esc(hp["alt"])}" loading="lazy" decoding="async"><figcaption class="cap">{t(hp["caption"])}</figcaption></figure><div class="members" style="grid-template-columns:1fr;gap:28px">{hosts}</div></div></section>'
            f'<section class="sec dark wrap" id="piter"><div class="grid"><div class="c5 rv"><span class="lbl">Опыт</span><h2 class="h2" style="margin-top:14px">{ev["spb_title"]}</h2></div><div class="c6 c6r rv"><p class="txt" style="font-size:clamp(17px,1.4vw,22px);line-height:1.45;color:#fff;max-width:none">{esc(ev["spb_text"])}</p></div></div></section>'
            f'<section class="sec wrap" id="komu"><div class="head"><h2 class="h2 rv">{ev["for_title"]}</h2></div><div class="two"><div class="rv"><div class="word">Подходит</div><ul class="list">{li(ev["for_whom"], "+")}</ul></div><div class="rv"><div class="word">Не подходит</div><ul class="list x">{li(ev["not_for"], "×")}</ul></div></div></section>'
            f'<section class="sec stone wrap" id="kak"><div class="head"><h2 class="h2 rv">{ev["terms_title"]}</h2></div><ol class="steps" style="--n:4">{terms}</ol><p class="txt rv" style="margin-top:36px;max-width:64ch">{esc(ev["forum_line"])}</p></section>'
            f'<section class="sec dark wrap" id="zayavka"><div class="grid"><div class="c5 rv"><span class="lbl">{esc(f["lbl"])}</span><h2 class="h2" style="margin-top:14px">{f["h2"]}</h2><div class="rule"></div><p class="txt">{esc(f["text"])}</p><p class="cap" style="margin-top:18px">Если удобнее без формы: <a href="{tg}" rel="noopener" style="text-decoration:underline;text-underline-offset:3px">Telegram</a>.</p></div><div class="c6 c6r rv">{form}</div></div></section>'
            f'<section class="sec wrap" id="voprosy"><div class="head"><h2 class="h2 rv">Вопросы</h2></div><div class="faq rv">{fq}</div></section>'
            f'</main>{footer()}</body></html>')
    return head(ev['seo']['title'], ev['seo']['description'], url, f'{SITE}{hb}_og.jpg', ld) + body


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
        write('index.html', home_page())
        write('o-byuro/index.html', about_page()); pages.append('/o-byuro/')
        write('kontakty/index.html', contacts_page()); pages.append('/kontakty/')
        write('obuchenie/index.html', education_page()); pages.append('/obuchenie/')
        write('politika/index.html', policy_page()); pages.append('/politika/')
        write('404.html', notfound_page())
        for ef in sorted(glob.glob(C('events', '*.json'))):
            ev = json.load(open(ef)); write(f'{ev["slug"]}/index.html', event_page(ev)); pages.append(f'/{ev["slug"]}/')
    reg = {"site": {"root": "/", "services": "/uslugi/", "portfolio": cfg['site']['portfolio'], "home": cfg['site']['home'], "request": "/uslugi/#zayavka", "telegram": cfg['contacts']['manager']['telegram'], "nav": site["nav"]},
           "services": [{"slug": sl, "title": BY[sl]['title'], "short": BY[sl].get('short', ''), "price": BY[sl]['price']['display'], "duration": plain(BY[sl]['duration']), "url": f"/uslugi/{sl}/", "side": sl in SIDE} for sl in ORDER + SIDE]}
    write('services.json', json.dumps(reg, ensure_ascii=False, indent=1))
    today = datetime.date.today().isoformat()
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>' for p in ['/'] + pages) + '</urlset>')
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    # CONTENT-TODO
    seen = set(); lines = ['# Чего не хватает на страницах услуг', '', f'Собрано генератором `tools/build.py` {today}. Каждая заглушка `[[ЗАПОЛНИТЬ]]` из `content/*.json` и кода попадает сюда автоматически. Исходный список из пакета: `docs/services-pack/content/CONTENT-TODO.md`.', '', '| Страница | Блок | Что нужно |', '|---|---|---|']
    for p, b, x in TODOS:
        k = (p, b, x)
        if k in seen: continue
        seen.add(k); lines.append(f'| `{p}` | {b} | {x} |')
    dec = data['_meta'].get('decisions', [])
    if dec:
        lines += ['', '## Решения, которые нужно принять', ''] + [f'- {x}' for x in dec]
    write('CONTENT-TODO.md', '\n'.join(lines) + '\n')
    print(f'заглушек: {len(seen)}')

if __name__ == '__main__':
    main()
