/* Концепт-бюро «Хрустальный». Общий скрипт страниц: шапка, меню, появление, UTM, форма в Битрикс24, цели Метрики.
   Настройки берутся из <script type="application/json" id="cfg"> на странице (генерируются из content/config.json). */
(function () {
  'use strict';
  document.documentElement.classList.add('js');
  var cfg = {};
  try { cfg = JSON.parse(document.getElementById('cfg').textContent); } catch (e) {}
  var page = document.body.dataset.page || location.pathname;
  var service = document.body.dataset.service || '';

  /* ---- Метрика: подключается только если задан номер счётчика ---- */
  var ymId = cfg.metrika && cfg.metrika.counter ? String(cfg.metrika.counter) : '';
  if (ymId) {
    (function (m, e, t, r, i, k, a) { m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); }; m[i].l = 1 * new Date();
      k = e.createElement(t); a = e.getElementsByTagName(t)[0]; k.async = 1; k.src = r; a.parentNode.insertBefore(k, a); })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
    window.ym(ymId, 'init', { clickmap: true, trackLinks: true, accurateTrackBounce: true, webvisor: false });
  }
  var goal = function (name, params) {
    if (ymId && window.ym) { window.ym(ymId, 'reachGoal', name, params || {}); }
    else if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') { console.info('[goal]', name, params || ''); }
  };

  /* ---- UTM: запоминаем при первом заходе, чтобы метка дожила до отправки формы ---- */
  var UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  (function () {
    var q = new URLSearchParams(location.search), found = {};
    UTM_KEYS.forEach(function (k) { if (q.get(k)) found[k] = q.get(k); });
    if (Object.keys(found).length) { store.set('hr_utm', JSON.stringify(found)); store.set('hr_utm_ts', String(Date.now())); }
    if (!store.get('hr_landing')) store.set('hr_landing', location.href);
    if (!store.get('hr_referrer') && document.referrer) store.set('hr_referrer', document.referrer);
  })();
  var utm = function () { try { return JSON.parse(store.get('hr_utm') || '{}'); } catch (e) { return {}; } };

  /* ---- шапка меняет цвет над фото и тёмными полосами ---- */
  var nav = document.querySelector('.nav');
  if (nav) {
    var darkZones = document.querySelectorAll('.hero .photo, .dark, .scene');
    var check = function () {
      var y = 44, on = false;
      darkZones.forEach(function (z) { var r = z.getBoundingClientRect(); if (r.top <= y && r.bottom >= y) on = true; });
      nav.classList.toggle('ondark', on);
    };
    addEventListener('scroll', check, { passive: true }); addEventListener('resize', check); check();
  }

  /* ---- меню ---- */
  var menu = document.querySelector('.menu');
  if (menu) {
    var open = function () { menu.classList.add('open'); document.body.classList.add('menu-open'); menu.querySelector('.close').focus(); };
    var close = function () { menu.classList.remove('open'); document.body.classList.remove('menu-open'); };
    document.querySelectorAll('.burger').forEach(function (b) { b.addEventListener('click', open); });
    menu.querySelector('.close').addEventListener('click', close);
    menu.querySelectorAll('a[href^="#"]').forEach(function (a) { a.addEventListener('click', close); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  }

  /* ---- портфолио: меню и кадры на главной строятся из /portfolio/projects.json ---- */
  var mp = document.getElementById('menu-portfolio');
  var pRoot = mp ? mp.dataset.portfolio : '/portfolio/';
  fetch(pRoot + 'projects.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }).then(function (data) {
    var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
    var byCat = function (id) { return data.projects.filter(function (p) { return p.category === id; }); };
    if (mp) {
      mp.querySelector('.pl').innerHTML = data.categories.map(function (c) {
        var list = byCat(c.id); if (!list.length) return '';
        return '<a href="' + pRoot + '#' + c.id + '">' + esc(c.title) + '<small>' + list.length + '</small></a>';
      }).join('') + '<a class="all" href="' + pRoot + '">всё портфолио →</a>';
    }
    document.querySelectorAll('.pcard[data-cat]').forEach(function (card) {
      var list = byCat(card.dataset.cat).slice(0, 2); if (!list.length) return;
      card.querySelector('.ph').innerHTML = list.map(function (p) { return '<img src="' + pRoot + p.cover + '_s.webp" alt="" loading="lazy" decoding="async">'; }).join('');
    });
  }).catch(function () {});

  /* ---- диагност: четыре вопроса → рекомендация → ответы в заявку ---- */
  var diag = document.getElementById('diag');
  if (diag) {
    var lead = document.getElementById('leadForm');
    var pick = function (name) { var el = diag.querySelector('input[name="dq_' + name + '"]:checked'); return el ? el.value : ''; };
    var picks = function (name) { return [].map.call(diag.querySelectorAll('input[name="dq_' + name + '"]:checked'), function (e) { return e.value; }); };
    var label = function (name, v) { var el = diag.querySelector('input[name="dq_' + name + '"][value="' + v + '"]'); return el ? el.nextElementSibling.textContent : v; };
    /* Ответы не превращаются в рекомендацию: они уходят в заявку как есть. */
    var render = function () {
      if (!lead || !lead.elements.diag) return;
      var stage = pick('stage'), pain = pick('pain'), houses = pick('houses'), docs = picks('docs');
      lead.elements.diag.value = [
        stage ? 'Стадия: ' + label('stage', stage) : '',
        pain ? 'Мешает: ' + label('pain', pain) : '',
        houses ? 'Домов в год: ' + label('houses', houses) : '',
        docs.length ? 'На руках: ' + docs.map(function (v) { return label('docs', v); }).join(', ') : ''
      ].filter(Boolean).join('\n');
    };
    diag.addEventListener('change', render);
  }

  /* ---- параллакс сцены и счётчики фактов ---- */
  var par = document.querySelectorAll('[data-parallax]');
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (par.length && !reduce) {
    var tick = false;
    var move = function () {
      par.forEach(function (el) {
        var r = el.parentElement.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return;
        var p = (r.top + r.height / 2 - innerHeight / 2) / innerHeight; el.style.transform = 'translateY(' + (p * -10) + '%)';
      }); tick = false;
    };
    addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(move); } }, { passive: true }); move();
  }
  var counted = false;
  var countUp = function () {
    document.querySelectorAll('.facts4 b').forEach(function (b) {
      var m = b.textContent.match(/^([\d\s]+)(.*)$/); if (!m) return;
      var target = parseInt(m[1].replace(/\s/g, ''), 10), suffix = m[2], t0 = performance.now(), dur = 1400;
      var fmt = function (n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); };
      var step = function (now) { var k = Math.min(1, (now - t0) / dur); k = 1 - Math.pow(1 - k, 3); b.textContent = fmt(Math.round(target * k)) + suffix; if (k < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    });
  };

  /* ---- появление при скролле ---- */
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px 40px 0px' });
    document.querySelectorAll('.rv, .scene .lines li').forEach(function (el) { io.observe(el); });
    var f4 = document.querySelector('.facts4');
    if (f4 && !reduce) { var fio = new IntersectionObserver(function (es) { if (es[0].isIntersecting && !counted) { counted = true; countUp(); fio.disconnect(); } }, { threshold: .4 }); fio.observe(f4); }
    /* цель: дочитывание до блока стоимости */
    var price = document.querySelector('#stoimost');
    if (price) { var pio = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { goal('price_view', { service: service }); pio.disconnect(); } }); }, { threshold: .3 }); pio.observe(price); }
  } else { document.querySelectorAll('.rv').forEach(function (el) { el.classList.add('in'); }); }

  /* ---- клики: основная кнопка, пример отчёта, Telegram ---- */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a,button'); if (!a) return;
    if (a.dataset.goal) goal(a.dataset.goal, { service: service, page: page });
    if (a.href && /t\.me\//.test(a.href)) goal('tg_click', { service: service });
  });

  /* ---- форма → Битрикс24 ---- */
  var form = document.getElementById('leadForm');
  if (form) {
    var hook = cfg.bitrix && cfg.bitrix.webhook ? cfg.bitrix.webhook.replace(/\/+$/, '') : '';
    var field = function (n) { return form.elements[n]; };
    var setBad = function (el, bad) { el.closest('.f').classList.toggle('bad', bad); };
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = field('name'), contact = field('contact'), obj = field('object'), about = field('about');
      var isEvent = form.dataset.kind === 'event', question = field('question');
      var ok = true;
      setBad(name, !name.value.trim()); ok = ok && !!name.value.trim();
      var cv = contact.value.trim(); var okc = /^(\+?\d[\d\s()-]{8,}|@?[a-zA-Z0-9_]{4,32}|https?:\/\/t\.me\/\S+)$/.test(cv);
      setBad(contact, !okc); ok = ok && okc;
      if (isEvent) { setBad(question, !question.value.trim()); ok = ok && !!question.value.trim(); }
      if (!ok) { form.querySelector('.f.bad input').focus(); return; }
      if (field('company') && field('company').value) return; /* ловушка для ботов вместо капчи */

      var u = utm(), title = (form.dataset.serviceTitle || 'Заявка с сайта') + ': ' + name.value.trim();
      var diagv = field('diag') ? field('diag').value : '';
      var evParts = [];
      if (isEvent) { var it = form.querySelector('input[name="interest"]:checked'); evParts = ['Интерес: ' + (it ? it.nextElementSibling.textContent : 'не указан'), 'Компания и город: ' + (field('company_city').value.trim() || 'не указано'), 'Вопрос для разбора: ' + question.value.trim()]; }
      var comments = ['Услуга: ' + (form.dataset.serviceTitle || ''), diagv ? 'Диагност:\n' + diagv : ''].concat(evParts, [obj ? 'Объект / кадастровый номер: ' + (obj.value.trim() || 'не указан') : '',
        about && about.value.trim() ? 'О проекте: ' + about.value.trim() : '', 'Страница: ' + location.href,
        'Первый заход: ' + (store.get('hr_landing') || ''), 'Реферер: ' + (store.get('hr_referrer') || 'прямой'),
        'UTM: ' + (Object.keys(u).length ? JSON.stringify(u) : 'нет')]).filter(Boolean).join('\n');
      var fields = { TITLE: title, NAME: name.value.trim(), COMMENTS: comments, SOURCE_ID: (cfg.bitrix && cfg.bitrix.source_id) || 'WEB',
        SOURCE_DESCRIPTION: 'Сайт бюро, ' + service + ', ' + page, OPENED: 'Y',
        UTM_SOURCE: u.utm_source || '', UTM_MEDIUM: u.utm_medium || '', UTM_CAMPAIGN: u.utm_campaign || '', UTM_CONTENT: u.utm_content || '', UTM_TERM: u.utm_term || '' };
      if (/^\+?\d/.test(cv)) fields.PHONE = [{ VALUE: cv, VALUE_TYPE: 'WORK' }]; else fields.IM = [{ VALUE: cv.replace(/^https?:\/\/t\.me\//, '@').replace(/^@?/, '@'), VALUE_TYPE: 'TELEGRAM' }];
      if (cfg.bitrix && cfg.bitrix.assigned_by_id) fields.ASSIGNED_BY_ID = cfg.bitrix.assigned_by_id;

      var btn = form.querySelector('[type=submit]'), msg = form.querySelector('.msg');
      btn.disabled = true; btn.querySelector('span').textContent = 'Отправляем';
      var done = function () { goal('form_' + service, { service: service }); form.innerHTML = form.dataset.success; form.classList.add('success'); form.setAttribute('aria-live', 'polite'); };
      var fail = function () { btn.disabled = false; btn.querySelector('span').textContent = form.dataset.cta; msg.style.display = 'block';
        msg.textContent = 'Не отправилось. Напишите нам в Telegram, ссылка ниже, или повторите через минуту.'; };

      if (!hook) { console.info('[lead → Битрикс24, тестовый режим]', fields); setTimeout(done, 500); return; }
      fetch(hook + '/crm.lead.add.json', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fields: fields, params: { REGISTER_SONET_EVENT: 'Y' } }) })
        .then(function (r) { return r.json(); }).then(function (j) { if (j && j.result) done(); else { console.error(j); fail(); } }).catch(fail);
    });
  }
})();
