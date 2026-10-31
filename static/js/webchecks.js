/*
 * Проверки страницы для заданий HTML/CSS.
 * Каждая проверка — объект из tests задания:
 *   {"check": "exists", "sel": "h1"}                         — есть элемент
 *   {"check": "count",  "sel": "li", "min": 3, "max": 5}      — сколько элементов
 *   {"check": "text",   "sel": "h1", "text": "Привет"}         — элемент содержит текст
 *   {"check": "attr",   "sel": "a", "attr": "href", "value": "kaspi"} — атрибут (и часть значения)
 *   {"check": "css",    "sel": "h1", "prop": "color", "value": "red"} — вычисленный стиль равен значению
 *   {"check": "cssnot", "sel": "div", "prop": "border-top-style", "value": "none"} — стиль задан не по умолчанию
 *   {"check": "rule", "has": ":hover", "prop": "background-color"} — в стилях есть правило (например, для наведения)
 *   {"check": "media", "text": "max-width", "prop": "flex-direction"} — есть правило @media (и свойство внутри)
 *   {"check": "keyframes"}                                    — есть анимация @keyframes
 * Используется и на сайте (окно предпросмотра), и при проверке эталонов.
 */
(function (root) {
  const norm = (s) => String(s || "").replace(/\s+/g, " ").trim().toLowerCase();

  function expectedCss(doc, win, prop, value) {
    const probe = doc.createElement("div");
    probe.style.setProperty(prop, value);
    if (!probe.style.getPropertyValue(prop)) return null;  // такого значения не бывает
    probe.style.visibility = "hidden";
    (doc.body || doc.documentElement).appendChild(probe);
    const v = win.getComputedStyle(probe).getPropertyValue(prop).trim();
    probe.remove();
    return v;
  }

  function cssMatches(doc, win, el, prop, value) {
    const actual = win.getComputedStyle(el).getPropertyValue(prop).trim();
    if (prop === "display") return actual === norm(value);  // display у пробника может поменяться
    if (prop === "font-family") return norm(actual).replace(/["']/g, "").includes(norm(value).replace(/["']/g, ""));
    const exp = expectedCss(doc, win, prop, value);
    return exp !== null && actual === exp;
  }

  // Все правила из <style>, включая вложенные в @media
  function rules(doc) {
    const out = [];
    const walk = (list, media) => {
      for (const r of Array.from(list || [])) {
        if (r.type === 1) out.push({ r, media });
        else if (r.type === 4) { out.push({ r, media }); walk(r.cssRules, r); }
        else out.push({ r, media });
      }
    };
    for (const sheet of Array.from(doc.styleSheets)) {
      try { walk(sheet.cssRules, null); } catch (e) { /* чужая таблица стилей */ }
    }
    return out;
  }

  const hasProp = (r, prop, value) => {
    if (!prop) return true;
    const v = r.style.getPropertyValue(prop);
    return v !== "" && (value === undefined || norm(v).includes(norm(value)));
  };

  function one(doc, win, c) {
    if (c.check === "rule") {
      return rules(doc).some(({ r }) => r.type === 1 && r.selectorText.includes(c.has) && hasProp(r, c.prop, c.value));
    }
    if (c.check === "media") {
      return rules(doc).some(({ r }) => r.type === 4 && norm(r.conditionText || r.media.mediaText).includes(norm(c.text || "")) &&
        (!c.prop || Array.from(r.cssRules).some((x) => x.type === 1 && hasProp(x, c.prop))));
    }
    if (c.check === "keyframes") return rules(doc).some(({ r }) => r.type === 7);
    let els;
    try {
      els = Array.from(doc.querySelectorAll(c.sel));
    } catch (e) {
      return false;
    }
    switch (c.check) {
      case "exists": return els.length > 0;
      case "count": return els.length >= (c.min || 0) && (c.max === undefined || els.length <= c.max);
      case "text": return els.some((e) => norm(e.textContent).includes(norm(c.text)));
      case "attr": return els.some((e) => {
        const v = e.getAttribute(c.attr);
        return v !== null && v.trim() !== "" && (c.value === undefined || norm(v).includes(norm(c.value)));
      });
      case "css": return els.some((e) => cssMatches(doc, win, e, c.prop, c.value));
      case "cssnot": return els.some((e) => !cssMatches(doc, win, e, c.prop, c.value));
      default: return false;
    }
  }

  root.runWebChecks = function (doc, win, checks) {
    return checks.map((c) => one(doc, win, c));
  };
})(typeof window !== "undefined" ? window : globalThis);
