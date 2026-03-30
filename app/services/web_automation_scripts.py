from __future__ import annotations

import json


class WebAutomationScripts:
    @staticmethod
    def build_web_auth_script(login, password):
        script = """
(() => {
  const loginValue = __LOGIN__;
  const passwordValue = __PASSWORD__;
  const submitTextPattern = /войти|вход\\s+в|login|sign\\s*in|submit|ok|авториз/i;
  const loginOpenTextPattern = /войти|вход\\s+в|login|sign\\s*in|авториз/i;
  const loginEntryPattern = /войти|вход\\s+в|login|sign\\s*in|авториз/i;
  const accountTextPattern = /личный\\s*кабинет|мой\\s*кабинет|профил|my\\s*account|account|profile|dashboard/i;
  const accountHrefPattern = /\\/(profile|account|cabinet|lk|dashboard)(\\/|$)|[#?](profile|account|cabinet|lk|dashboard)/i;
  const workspaceTextPattern = /моя\\s*организац|текущие\\s*закупки|при[её]м\\s*заявок|подводятся\\s*итоги|переторжка/i;
  const nextButtonPattern = /далее|continue|next/i;
  const frameSources = [];
  try {
    const frameNodes = Array.from(document.querySelectorAll('frame[src], iframe[src]'));
    for (const frameNode of frameNodes) {
      const src = String(frameNode.getAttribute('src') || '').trim();
      if (src) frameSources.push(src);
    }
  } catch (e) {}

  const docs = [];
  const queue = [window];
  const seen = [];
  while (queue.length > 0) {
    const win = queue.shift();
    if (!win || seen.includes(win)) continue;
    seen.push(win);
    try {
      if (win.document) docs.push(win.document);
      const frames = win.frames || [];
      for (let i = 0; i < frames.length; i += 1) {
        try { queue.push(frames[i]); } catch (e) {}
      }
    } catch (e) {}
  }

  const isVisible = (element) => {
    if (!element || element.disabled) return false;
    try {
      const style = element.ownerDocument.defaultView.getComputedStyle(element);
      if (!style) return true;
      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
    } catch (e) {}
    return true;
  };

  const pickFirst = (root, selectors) => {
    if (!root) return null;
    for (const selector of selectors) {
      let nodes = [];
      try { nodes = Array.from(root.querySelectorAll(selector)); } catch (e) { nodes = []; }
      for (const node of nodes) {
        if (isVisible(node)) return node;
      }
    }
    return null;
  };

  const findLoginOpenButton = (doc) => {
    if (!doc) return null;
    const selectors = [
      'button[mat-raised-button]',
      'button.mat-raised-button',
      'button',
      'a'
    ];
    for (const selector of selectors) {
      let nodes = [];
      try { nodes = Array.from(doc.querySelectorAll(selector)); } catch (e) { nodes = []; }
      for (const node of nodes) {
        const text = String(
          node.innerText
          || node.textContent
          || node.getAttribute('aria-label')
          || node.getAttribute('title')
          || node.value
          || ''
        ).trim();
        if (!text) continue;
        if (text.length > 40) continue;
        if (loginOpenTextPattern.test(text)) {
          return node;
        }
      }
    }
    return null;
  };

  const clickLoginOpenButton = (doc) => {
    const loginButton = findLoginOpenButton(doc);
    if (loginButton) {
      loginButton.click();
      return true;
    }
    return false;
  };

  const hasLogoutMarker = docs.some((doc) => {
    try {
      const links = Array.from(doc.querySelectorAll('a[href], button, [role="button"]'));
      return links.some((item) => {
        const text = String(item.innerText || item.textContent || '').trim();
        const href = String(item.getAttribute('href') || '').trim();
        return /выйти|logout|log\\s*out|sign\\s*out/i.test(text) || /logout|signout/i.test(href);
      });
    } catch (e) {
      return false;
    }
  });

  const hasAccountMarker = docs.some((doc) => {
    try {
      const nodes = Array.from(doc.querySelectorAll('a[href], button, [role="button"], [aria-label], [data-testid]'));
      return nodes.some((item) => {
        const text = String(item.innerText || item.textContent || item.getAttribute('aria-label') || '').trim();
        const href = String(item.getAttribute('href') || '').trim();
        if (text && accountTextPattern.test(text) && !loginEntryPattern.test(text)) {
          return true;
        }
        if (href && accountHrefPattern.test(href) && !loginEntryPattern.test(text)) {
          return true;
        }
        return false;
      });
    } catch (e) {
      return false;
    }
  });

  const hasLoginDialog = docs.some((doc) => {
    try {
      return Boolean(doc.querySelector('mat-dialog-container form input[formcontrolname="password"]'));
    } catch (e) {
      return false;
    }
  });
  const hasLoginEntryButton = docs.some((doc) => Boolean(findLoginOpenButton(doc)));
  const hasPasswordField = docs.some((doc) => {
    try {
      return Boolean(
        doc.querySelector(
          'input[type="password"], input[formcontrolname="password"], input[name*="pass" i], input[id*="pass" i]'
        )
      );
    } catch (e) {
      return false;
    }
  });
  const hasWorkspaceMarker = docs.some((doc) => {
    try {
      const nodes = Array.from(doc.querySelectorAll('a, button, span, div, [role="menuitem"], [class*="menu" i]'));
      return nodes.some((item) => {
        const text = String(item.innerText || item.textContent || item.getAttribute('aria-label') || '').trim();
        return text && workspaceTextPattern.test(text);
      });
    } catch (e) {
      return false;
    }
  });
  const loginUiPresent = hasLoginDialog || hasLoginEntryButton;
  const sessionMarkerPresent =
    hasLogoutMarker
    || (hasAccountMarker && !loginUiPresent)
    || (hasWorkspaceMarker && !hasPasswordField && !loginUiPresent);

  if (sessionMarkerPresent) {
    return {
      ok: true,
      found_fields: false,
      submitted: false,
      already_authorized: true,
      session_marker_present: true,
      login_ui_present: loginUiPresent,
      frame_sources: frameSources,
      message: hasLogoutMarker
        ? 'Вход уже выполнен'
        : (hasWorkspaceMarker ? 'Обнаружена активная рабочая сессия' : 'Обнаружены признаки активной сессии')
    };
  }

  if (!hasLoginDialog) {
    for (const doc of docs) {
      if (clickLoginOpenButton(doc)) {
        return {
          ok: true,
          found_fields: false,
          submitted: false,
          already_authorized: false,
          dialog_opened: true,
          captcha_required: false,
          submit_disabled: false,
          login_ui_present: true,
          frame_sources: frameSources,
          message: 'Открыто окно входа'
        };
      }
    }
  }

  const loginSelectors = [
    'input[formcontrolname="login"]',
    'input[name="username"]',
    'input[name="user"]',
    'input[name="login"]',
    'input[name="email"]',
    'input[id*="user" i]',
    'input[id*="login" i]',
    'input[id*="email" i]',
    'input[placeholder*="логин" i]',
    'input[placeholder*="email" i]',
    'input[autocomplete="username"]',
    'input[type="email"]',
    'input[type="text"]',
    'input:not([type])'
  ];
  const passwordSelectors = [
    'input[formcontrolname="password"]',
    'input[name="password"]',
    'input[name="pass"]',
    'input[id*="pass" i]',
    'input[placeholder*="парол" i]',
    'input[autocomplete="current-password"]',
    'input[type="password"]'
  ];

  let loginInput = null;
  let passwordInput = null;
  let sourceDoc = null;
  for (const doc of docs) {
    const pass = pickFirst(doc, passwordSelectors);
    if (!pass) continue;
    let login = pickFirst(doc, loginSelectors);
    if (!login && pass.form) login = pickFirst(pass.form, loginSelectors);
    if (!login) {
      const root = pass.form || doc;
      login = pickFirst(root, ['input[type="text"]', 'input[type="email"]', 'input:not([type])']);
    }
    if (login) {
      loginInput = login;
      passwordInput = pass;
      sourceDoc = doc;
      break;
    }
  }

  if (!loginInput || !passwordInput) {
    return {
      ok: false,
      found_fields: false,
      submitted: false,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: false,
      submit_disabled: false,
      login_ui_present: loginUiPresent,
      frame_sources: frameSources,
      message: `Поля входа не найдены (проверено документов: ${docs.length})`
    };
  }

  const setNativeValue = (input, value) => {
    try {
      const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(input), 'value');
      if (descriptor && typeof descriptor.set === 'function') {
        descriptor.set.call(input, value);
      } else {
        input.value = value;
      }
    } catch (e) {
      input.value = value;
    }
    input.focus();
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    input.dispatchEvent(new Event('blur', { bubbles: true }));
  };

  setNativeValue(loginInput, loginValue);
  setNativeValue(passwordInput, passwordValue);

  const findSubmitControl = (root) => {
    if (!root) return null;
    const selectors = [
      'button.mat-raised-button.mat-primary',
      'button[type="submit"]',
      'input[type="submit"]',
      'button[name*="login" i]',
      'button[id*="login" i]',
      'button[id*="submit" i]',
      'input[name*="login" i]',
      'input[id*="login" i]',
      'button',
      'input[type="button"]'
    ];
    for (const selector of selectors) {
      let nodes = [];
      try { nodes = Array.from(root.querySelectorAll(selector)); } catch (e) { nodes = []; }
      for (const node of nodes) {
        if (!isVisible(node)) continue;
        const text = String(node.innerText || node.textContent || node.value || node.getAttribute('aria-label') || '').trim();
        if (selector === 'button.mat-raised-button.mat-primary') {
          if (node.classList.contains('alt-auth-button')) continue;
          if (!submitTextPattern.test(text) && !nextButtonPattern.test(text)) continue;
        } else if (selector === 'button' || selector === 'input[type="button"]') {
          if (!submitTextPattern.test(text) && !nextButtonPattern.test(text)) continue;
        }
        return node;
      }
    }
    return null;
  };

  const tokenInput = sourceDoc
    ? sourceDoc.querySelector('input[name="smart-token"]')
    : null;
  const smartToken = String((tokenInput && tokenInput.value) || '').trim();
  const hasSmartCaptcha = sourceDoc
    ? Boolean(sourceDoc.querySelector('um-smart-captcha, iframe[src*="smartcaptcha"], iframe[title*="SmartCaptcha"]'))
    : false;
  const captchaRequired = hasSmartCaptcha && smartToken.length === 0;

  const form = passwordInput.form || loginInput.form || null;
  const submitControl = findSubmitControl(form) || findSubmitControl(sourceDoc);
  if (submitControl && submitControl.disabled) {
    return {
      ok: false,
      found_fields: true,
      submitted: false,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: captchaRequired,
      submit_disabled: true,
      login_ui_present: true,
      frame_sources: frameSources,
      message: captchaRequired
        ? 'Кнопка входа неактивна: ожидается SmartCaptcha'
        : 'Кнопка входа неактивна'
    };
  }

  if (captchaRequired && !submitControl) {
    return {
      ok: false,
      found_fields: true,
      submitted: false,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: true,
      submit_disabled: true,
      login_ui_present: true,
      frame_sources: frameSources,
      message: 'Ожидание SmartCaptcha для продолжения входа'
    };
  }

  if (submitControl) {
    submitControl.click();
    return {
      ok: true,
      found_fields: true,
      submitted: true,
      already_authorized: false,
      dialog_opened: false,
      captcha_required: false,
      submit_disabled: false,
      login_ui_present: true,
      frame_sources: frameSources,
      message: 'Форма входа отправлена кнопкой'
    };
  }

  if (form) {
    if (typeof form.requestSubmit === 'function') {
      form.requestSubmit();
      return {
        ok: true,
        found_fields: true,
        submitted: true,
        already_authorized: false,
        dialog_opened: false,
        captcha_required: false,
        submit_disabled: false,
        login_ui_present: true,
        frame_sources: frameSources,
        message: 'Форма входа отправлена через requestSubmit()'
      };
    }
    if (typeof form.submit === 'function') {
      form.submit();
      return {
        ok: true,
        found_fields: true,
        submitted: true,
        already_authorized: false,
        dialog_opened: false,
        captcha_required: false,
        submit_disabled: false,
        login_ui_present: true,
        frame_sources: frameSources,
        message: 'Форма входа отправлена через submit()'
      };
    }
  }

  passwordInput.focus();
  const enterEventData = { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true };
  passwordInput.dispatchEvent(new KeyboardEvent('keydown', enterEventData));
  passwordInput.dispatchEvent(new KeyboardEvent('keypress', enterEventData));
  passwordInput.dispatchEvent(new KeyboardEvent('keyup', enterEventData));
  return {
    ok: true,
    found_fields: true,
    submitted: true,
    already_authorized: false,
    dialog_opened: false,
    captcha_required: false,
    submit_disabled: false,
    login_ui_present: true,
    frame_sources: frameSources,
    message: 'Форма входа отправлена через Enter'
  };
})();
"""
        script = script.replace("__LOGIN__", json.dumps(login))
        script = script.replace("__PASSWORD__", json.dumps(password))
        return script

    @staticmethod
    def build_bid_submission_navigation_script():
        return """
(() => {
  const targetPath = '/trades';
  const targetPage = 'purchases.trades.filters.BID_SUBMISSION';
  const normalizeText = (value) => String(value || '')
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/\\s+/g, ' ')
    .trim();
  const isTargetUrl = (value) => {
    if (!value) return false;
    try {
      const parsed = new URL(value, window.location.href);
      return parsed.pathname === targetPath
        && String(parsed.searchParams.get('page') || '') === targetPage;
    } catch (e) {
      return false;
    }
  };

  if (isTargetUrl(window.location.href)) {
    return { ok: true, already_on_target: true };
  }

  const selectors = [
    'a.navigation-anchor[href]',
    'a[mat-list-item][href]',
    'um-navigation-item a[href]',
    'a[href]'
  ];
  const links = [];
  const seenNodes = [];
  for (const selector of selectors) {
    let nodes = [];
    try { nodes = Array.from(document.querySelectorAll(selector)); } catch (e) { nodes = []; }
    for (const node of nodes) {
      if (!node || seenNodes.includes(node)) continue;
      seenNodes.push(node);
      links.push(node);
    }
  }

  let textMatch = null;
  for (const link of links) {
    const href = String(link.getAttribute('href') || '').trim();
    if (isTargetUrl(href)) {
      link.click();
      return { ok: true, clicked: true, href };
    }
    const text = normalizeText(
      link.innerText
      || link.textContent
      || link.getAttribute('aria-label')
      || link.getAttribute('title')
      || ''
    );
    if (text.includes('прием заявок')) {
      textMatch = link;
    }
  }

  if (textMatch) {
    const href = String(textMatch.getAttribute('href') || '').trim();
    textMatch.click();
    return { ok: true, clicked: true, href };
  }

  const fallbackUrl = `${targetPath}?page=${encodeURIComponent(targetPage)}`;
  try {
    const parsedCurrent = new URL(window.location.href);
    parsedCurrent.pathname = targetPath;
    parsedCurrent.search = `page=${encodeURIComponent(targetPage)}`;
    window.location.assign(parsedCurrent.toString());
    return { ok: true, redirected: true, target_url: parsedCurrent.toString() };
  } catch (e) {
    window.location.assign(fallbackUrl);
    return { ok: true, redirected: true, target_url: fallbackUrl };
  }
})();
"""

    @staticmethod
    def build_bid_request_search_script(request_number):
        script = """
(() => {
  const requestNumber = __REQUEST_NUMBER__;
  const normalizeText = (value) => String(value || '')
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/\\s+/g, ' ')
    .trim();
  const latinLikeMap = {
    'а': 'a',
    'в': 'b',
    'е': 'e',
    'к': 'k',
    'м': 'm',
    'н': 'h',
    'о': 'o',
    'р': 'p',
    'с': 'c',
    'т': 't',
    'у': 'y',
    'х': 'x'
  };
  const toComparable = (value) => {
    const normalized = normalizeText(value);
    let transformed = '';
    for (const ch of normalized) {
      transformed += latinLikeMap[ch] || ch;
    }
    return transformed.replace(/[^a-zа-я0-9]/g, '');
  };

  const target = normalizeText(requestNumber);
  const targetComparable = toComparable(requestNumber);
  if (!target) {
    return {
      ok: false,
      retry: false,
      input_filled: false,
      search_triggered: false,
      match_found: false,
      match_opened: false,
      message: 'Номер заявки не указан'
    };
  }

  const docs = [];
  const seenDocs = [];
  const addDoc = (doc) => {
    if (!doc || seenDocs.includes(doc)) return;
    seenDocs.push(doc);
    docs.push(doc);
  };

  addDoc(document);
  for (const frame of Array.from(document.querySelectorAll('iframe, frame'))) {
    try { addDoc(frame.contentDocument); } catch (e) {}
  }

  const isVisible = (node) => {
    if (!node || !node.ownerDocument || !node.ownerDocument.defaultView) return false;
    const style = node.ownerDocument.defaultView.getComputedStyle(node);
    if (!style || style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity || 1) === 0) {
      return false;
    }
    const rect = node.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };

  const setNativeValue = (element, value) => {
    const tagName = String(element.tagName || '').toLowerCase();
    const proto = tagName === 'textarea' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');
    if (descriptor && typeof descriptor.set === 'function') {
      descriptor.set.call(element, value);
    } else {
      element.value = value;
    }
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  };

  const fireEnter = (element) => {
    const data = { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true };
    element.dispatchEvent(new KeyboardEvent('keydown', data));
    element.dispatchEvent(new KeyboardEvent('keypress', data));
    element.dispatchEvent(new KeyboardEvent('keyup', data));
  };

  const textPattern = /поиск|search|найти|фильтр|номер|заяв|request|bid|tender/i;
  const authPattern = /логин|парол|password|signin|auth|account/i;
  const searchButtonPattern = /поиск|search|найти|применить|фильтр|обновить/i;
  const openActionPattern = /участвовать|перейти|открыть|подробн|details|view|participate/i;

  const inputCandidates = [];
  for (const doc of docs) {
    let fields = [];
    try {
      fields = Array.from(
        doc.querySelectorAll('input[type="search"], input[type="text"], input:not([type]), textarea')
      );
    } catch (e) {
      fields = [];
    }
    for (const field of fields) {
      if (!isVisible(field)) continue;
      const metadata = normalizeText(
        field.placeholder
        || field.name
        || field.id
        || field.getAttribute('aria-label')
        || field.getAttribute('title')
        || ''
      );
      let score = 0;
      if (String(field.type || '').toLowerCase() === 'search') score += 7;
      if (textPattern.test(metadata)) score += 8;
      if (authPattern.test(metadata)) score -= 10;
      if (field.form) score += 1;
      if (score > 0) {
        inputCandidates.push({ field, score });
      }
    }
  }

  inputCandidates.sort((a, b) => b.score - a.score);
  const targetInput = inputCandidates.length ? inputCandidates[0].field : null;

  const clickSearchControl = (root) => {
    if (!root || typeof root.querySelectorAll !== 'function') return false;
    let nodes = [];
    try {
      nodes = Array.from(root.querySelectorAll('button, [role="button"], a'));
    } catch (e) {
      nodes = [];
    }
    for (const node of nodes) {
      if (!isVisible(node)) continue;
      const text = normalizeText(
        node.innerText
        || node.textContent
        || node.getAttribute('aria-label')
        || node.getAttribute('title')
        || ''
      );
      if (!text || !searchButtonPattern.test(text)) continue;
      try {
        node.click();
        return true;
      } catch (e) {}
    }
    return false;
  };

  let inputFilled = false;
  let searchTriggered = false;

  if (targetInput) {
    targetInput.focus();
    setNativeValue(targetInput, requestNumber);
    inputFilled = true;

    const roots = [];
    if (targetInput.form) roots.push(targetInput.form);
    if (targetInput.parentElement) roots.push(targetInput.parentElement);
    const container = targetInput.closest
      ? targetInput.closest('form, .filters, .filter, [role="search"], [class*="filter"], [class*="search"]')
      : null;
    if (container) roots.push(container);

    for (const root of roots) {
      if (clickSearchControl(root)) {
        searchTriggered = true;
        break;
      }
    }

    if (!searchTriggered) {
      fireEnter(targetInput);
      searchTriggered = true;
    }
  }

  const isNavNode = (node) => {
    if (!node || !node.closest) return false;
    const nav = node.closest(
      'aside, nav, [class*="sidebar" i], [class*="menu" i], [class*="navigation" i]'
    );
    return Boolean(nav);
  };

  const triggerClick = (node) => {
    if (!node) return false;
    try { node.scrollIntoView({ block: 'center', inline: 'center' }); } catch (e) {}
    const view = (node.ownerDocument && node.ownerDocument.defaultView) || window;
    const mouseData = { bubbles: true, cancelable: true, composed: true, view };
    const pointerData = { bubbles: true, cancelable: true, composed: true, pointerType: 'mouse' };
    try { node.dispatchEvent(new PointerEvent('pointerdown', pointerData)); } catch (e) {}
    try { node.dispatchEvent(new MouseEvent('mousedown', mouseData)); } catch (e) {}
    try { node.dispatchEvent(new PointerEvent('pointerup', pointerData)); } catch (e) {}
    try { node.dispatchEvent(new MouseEvent('mouseup', mouseData)); } catch (e) {}
    try { node.dispatchEvent(new MouseEvent('click', mouseData)); } catch (e) {}
    try { node.click(); } catch (e) {}
    return true;
  };

  const findClickable = (node) => {
    if (!node) return null;
    if (node.closest) {
      const clickable = node.closest(
        'a, button, [role="button"], [role="link"], [onclick], [class*="btn" i], [class*="button" i], tr, [role="row"], li'
      );
      if (clickable && !isNavNode(clickable)) return clickable;
    }
    if (isNavNode(node)) return null;
    return node;
  };

  const collectOpenActionCandidates = (root) => {
    if (!root || typeof root.querySelectorAll !== 'function') return [];
    let nodes = [];
    try {
      nodes = Array.from(
        root.querySelectorAll(
          'button, a, [role="button"], [role="link"], [onclick], [class*="btn" i], [class*="button" i], [tabindex]'
        )
      );
    } catch (e) {
      nodes = [];
    }
    const result = [];
    for (const node of nodes) {
      if (!isVisible(node) || isNavNode(node)) continue;
      const text = normalizeText(
        node.innerText
        || node.textContent
        || node.getAttribute('aria-label')
        || node.getAttribute('title')
        || ''
      );
      if (!text || !openActionPattern.test(text)) continue;
      const clickable = findClickable(node) || node;
      if (clickable && isVisible(clickable) && !result.includes(clickable)) {
        result.push(clickable);
      }
    }
    return result;
  };

  const textMatches = [];
  const selectors = 'a, button, [role="button"], [role="link"], td, th, tr, [role="row"], div, span';
  for (const doc of docs) {
    let nodes = [];
    try {
      nodes = Array.from(doc.querySelectorAll(selectors));
    } catch (e) {
      nodes = [];
    }
    for (const node of nodes) {
      if (textMatches.length >= 30) break;
      if (!isVisible(node)) continue;
      const text = normalizeText(node.innerText || node.textContent || '');
      const comparable = toComparable(text);
      if (!text || text.length > 220) continue;
      if (
        text.includes(target)
        || (targetComparable && comparable.includes(targetComparable))
      ) {
        textMatches.push(node);
      }
    }
  }

  const openActionFromMatch = textMatches
    .flatMap((node) => {
      const roots = [];
      if (node && node.closest) {
        const container = node.closest(
          '[class*="trade" i], [class*="purchase" i], [class*="request" i], [class*="lot" i], [class*="card" i], article, tr, [role="row"], li, div'
        );
        if (container) roots.push(container);
      }
      if (node && node.parentElement) roots.push(node.parentElement);
      return roots.flatMap((root) => collectOpenActionCandidates(root));
    })
    .find((node) => Boolean(node && isVisible(node)));

  if (openActionFromMatch) {
    try {
      triggerClick(openActionFromMatch);
      return {
        ok: true,
        retry: false,
        input_filled: inputFilled,
        search_triggered: searchTriggered,
        match_found: true,
        match_opened: true,
        message: 'Заявка найдена и открыта'
      };
    } catch (e) {}
  }

  const clickableMatch = textMatches
    .map((node) => findClickable(node))
    .find((node) => Boolean(node && isVisible(node)));

  if (clickableMatch) {
    try {
      triggerClick(clickableMatch);
      return {
        ok: true,
        retry: false,
        input_filled: inputFilled,
        search_triggered: searchTriggered,
        match_found: true,
        match_opened: true,
        message: 'Заявка найдена и открыта'
      };
    } catch (e) {}
  }

  const globalOpenActions = docs
    .flatMap((doc) => collectOpenActionCandidates(doc.body || doc))
    .filter((node, index, arr) => arr.indexOf(node) === index);

  if (globalOpenActions.length === 1) {
    try {
      triggerClick(globalOpenActions[0]);
      return {
        ok: true,
        retry: false,
        input_filled: inputFilled,
        search_triggered: searchTriggered,
        match_found: true,
        match_opened: true,
        message: 'Открыта найденная заявка'
      };
    } catch (e) {}
  }

  if (globalOpenActions.length > 1 && textMatches.length > 0) {
    try {
      triggerClick(globalOpenActions[0]);
      return {
        ok: true,
        retry: false,
        input_filled: inputFilled,
        search_triggered: searchTriggered,
        match_found: true,
        match_opened: true,
        message: 'Открыта первая заявка из отфильтрованного списка'
      };
    } catch (e) {}
  }

  const participateCandidates = docs
    .flatMap((doc) => {
      const root = doc.body || doc;
      if (!root || typeof root.querySelectorAll !== 'function') return [];
      let nodes = [];
      try {
        nodes = Array.from(
          root.querySelectorAll(
            'button, a, [role="button"], [role="link"], [onclick], [class*="btn" i], [class*="button" i], div, span'
          )
        );
      } catch (e) {
        nodes = [];
      }
      return nodes
        .filter((node) => isVisible(node) && !isNavNode(node))
        .filter((node) => {
          const text = normalizeText(
            node.innerText
            || node.textContent
            || node.getAttribute('aria-label')
            || node.getAttribute('title')
            || ''
          );
          return text.includes('участвовать') || text.includes('participate');
        })
        .map((node) => findClickable(node) || node);
    })
    .filter((node, index, arr) => Boolean(node) && arr.indexOf(node) === index);

  if (
    participateCandidates.length === 1
    && (textMatches.length > 0 || inputFilled || searchTriggered)
  ) {
    try {
      triggerClick(participateCandidates[0]);
      return {
        ok: true,
        retry: false,
        input_filled: inputFilled,
        search_triggered: searchTriggered,
        match_found: true,
        match_opened: true,
        message: 'Открыта заявка через кнопку «Участвовать»'
      };
    } catch (e) {}
  }

  if (participateCandidates.length > 1 && textMatches.length > 0) {
    try {
      triggerClick(participateCandidates[0]);
      return {
        ok: true,
        retry: false,
        input_filled: inputFilled,
        search_triggered: searchTriggered,
        match_found: true,
        match_opened: true,
        message: 'Открыта первая заявка через кнопку «Участвовать»'
      };
    } catch (e) {}
  }

  if (textMatches.length > 0) {
    return {
      ok: true,
      retry: true,
      input_filled: inputFilled,
      search_triggered: searchTriggered,
      match_found: true,
      match_opened: false,
      message: 'Заявка найдена в списке, пробуем открыть'
    };
  }

  if (inputFilled || searchTriggered) {
    return {
      ok: true,
      retry: true,
      input_filled: inputFilled,
      search_triggered: searchTriggered,
      match_found: false,
      match_opened: false,
      message: 'Поиск заявки запущен, ожидание результатов'
    };
  }

  return {
    ok: false,
    retry: true,
    input_filled: false,
    search_triggered: false,
    match_found: false,
    match_opened: false,
    message: `Не удалось найти поле поиска заявки (совпадений: ${textMatches.length}, кнопок: ${globalOpenActions.length})`
  };
})();
"""
        return script.replace("__REQUEST_NUMBER__", json.dumps(request_number))
