/* Логика страницы софта.
 *
 * ЧЕТЫРЕ ПРАВИЛА, КОТОРЫЕ ЗДЕСЬ НЕЛЬЗЯ НАРУШАТЬ
 *
 * 1. ЗАГЛУШКА ДОЛЖНА ГОВОРИТЬ, ЧТО ОНА ЗАГЛУШКА.
 *    Кнопка «Купить» не берёт денег. Если она выглядит как настоящая,
 *    человек нажмёт, не найдёт оплаты и решит, что его обманули или
 *    что у него сломалась карта. Первое хуже.
 *
 * 2. ПУСТОЕ НЕ ДОЛЖНО ВЫГЛЯДЕТЬ КАК РЕЗУЛЬТАТ.
 *    Нет товаров, нет реестра, нет отправки - везде пишется причина.
 *    Тишина в интерфейсе читается как согласие.
 *
 * 3. НЕ СОБИРАТЬ ДАННЫЕ, КОТОРЫЕ НЕКУДА ОТПРАВЛЯТЬ.
 *    Почта вводится и остаётся в браузере. Ни один запрос на сервер
 *    не уходит, и об этом сказано под полем, а не в подвале.
 *
 * 4. ВЕРСИЯ ФОРМАТА ПРОВЕРЯЕТСЯ.
 *    Без неё список товаров - это просто слова, и неизвестная версия
 *    может значить что угодно, включая «злоумысел».
 */
(function () {
  "use strict";

  var KEY = "shop.remember.v1";
  var el = function (id) { return document.getElementById(id); };

  function say(node, text, kind) {
    if (!node) { return; }
    node.textContent = text;
    node.className = "msg" + (kind ? " " + kind : "");
  }

  /* --- чтение реестра ------------------------------------------------- */
  function readData() {
    var d = window.SHOP_DATA;
    if (!d) {
      return { ok: false, причина: "файл shop-data.js не пришёл" };
    }
    if (typeof d.format !== "number") {
      return { ok: false, причина: "в реестре нет номера версии формата" };
    }
    if (d.format !== 1) {
      return { ok: false, причина: "формат версии " + d.format +
                                   ", страница умеет только 1" };
    }
    if (Object.prototype.toString.call(d.items) !== "[object Array]") {
      return { ok: false, причина: "items - не массив" };
    }
    return { ok: true, data: d };
  }

  /* --- запоминание ---------------------------------------------------- */
  /* Только имя и выбор версии. Почту не запоминаем: она и вводится
   * для ответа, и в localStorage живёт годами, а человек про неё
   * забывает. Причина в том же и предупреждается. */
  function loadRemembered() {
    var raw;
    try { raw = localStorage.getItem(KEY); } catch (e) { return null; }
    if (!raw) { return null; }
    try {
      var box = JSON.parse(raw);
      return (box && typeof box === "object") ? box : null;
    } catch (e) {
      try { localStorage.removeItem(KEY); } catch (e2) { /* нечего */ }
      return null;
    }
  }

  function saveRemembered(name, which) {
    try {
      localStorage.setItem(KEY, JSON.stringify({ name: name, which: which }));
      return null;
    } catch (e) {
      return "не сохранилось: браузер не даёт хранилище (" +
             (e && e.name ? e.name : "ошибка") + ")";
    }
  }

  /* --- товары --------------------------------------------------------- */
  function drawGoods(data) {
    var box = el("goods");
    box.textContent = "";

    if (data.items.length === 0) {
      say(el("goods-msg"),
          "Реестр пришёл, но в нём 0 товаров. Это не то же самое, что " +
          "файла нет: файла нет - об этом написано выше.", "bad");
      return;
    }

    var select = el("which");
    select.textContent = "";

    data.items.forEach(function (item, i) {
      var цена = data.price_rub;
      var card = document.createElement("article");
      card.className = "good";

      var h = document.createElement("h2");
      h.className = "good-title";
      /* Название без текста читалось бы как «товар». Поэтому при
       * отсутствии поля подставляем номер, а не пустоту. */
      h.textContent = item.title || ("товар №" + (i + 1) + " (без названия)");
      card.appendChild(h);

      var price = document.createElement("div");
      price.className = "price";
      price.textContent = цена + " ₽";
      card.appendChild(price);

      var note = document.createElement("p");
      note.className = "note";
      note.textContent = item.note || "описания нет в реестре";
      card.appendChild(note);

      if (item.what_you_get && item.what_you_get.length) {
        var ul = document.createElement("ul");
        item.what_you_get.forEach(function (line) {
          var li = document.createElement("li");
          li.textContent = line;
          ul.appendChild(li);
        });
        card.appendChild(ul);
      }

      var meta = document.createElement("div");
      meta.className = "meta";
      /* Отсутствующее поле здесь читалось бы как «без ограничений»,
       * а это выдумка. Пишем «не указано». */
      meta.textContent = "лицензия: " + (item.license || "не указана") +
                         " · обновления: " + (item.updates || "не указаны");
      card.appendChild(meta);

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "buy";
      btn.textContent = "Купить за " + цена + " ₽";
      btn.addEventListener("click", function () { buy(item, btn); });
      card.appendChild(btn);

      box.appendChild(card);

      var opt = document.createElement("option");
      opt.value = item.id || String(i);
      opt.textContent = item.title || ("товар №" + (i + 1));
      select.appendChild(opt);
    });

    say(el("goods-msg"), data.items.length + " варианта в реестре.");
  }

  /* --- покупка -------------------------------------------------------- */
  /* Здесь нет ни одного сетевого запроса, и это не опечатка. */
  function buy(item, btn) {
    btn.disabled = true;
    var live = window.SHOP_DATA && window.SHOP_DATA.payment_live;
    if (live) {
      say(el("goods-msg"),
          "Оплата подключена, но формы оплаты ещё нет на этой странице. " +
          "Нажмите ещё раз, когда она появится.", "bad");
      btn.disabled = false;
      return;
    }
    say(el("goods-msg"),
        "«" + (item.title || "товар") + "» стоит " +
        window.SHOP_DATA.price_rub + " ₽. Оплата НЕ подключена: сейчас " +
        "ничего не списывается и карту я не спрошу. Оставьте заявку ниже, " +
        "и когда появится оплата, я напишу.", "bad");
    btn.textContent = "Оплата не подключена";
    btn.disabled = true;
  }

  /* --- заявка --------------------------------------------------------- */
  function submit() {
    var name = el("name").value.trim();
    var mail = el("mail").value.trim();
    var which = el("which").value;
    var about = el("about").value.trim();

    if (!name) {
      say(el("form-msg"), "Как к вам обращаться - пусто. Заявка без имени " +
                         "не нужна никому.", "bad");
      return;
    }
    if (mail && mail.indexOf("@") < 1) {
      say(el("form-msg"), "Почта выглядит не как почта: знака @ нет. " +
                         "Если отвечать не нужно - оставьте поле пустым.", "bad");
      return;
    }

    if (el("save").checked) {
      var warn = saveRemembered(name, which);
      if (warn) {
        say(el("form-msg"), "Запомнить не вышло: " + warn, "bad");
        return;
      }
    }

    /* ЧЕСТНЫЙ ОТВЕТ, А НЕ «ОТПРАВЛЕНО».
     *
     * Здесь нет сервера. Любой текст вида «заявка отправлена» был бы
     * враньём, и человек потом бы ждал ответа, которого не будет.
     */
    say(el("form-msg"),
        "Заявка НЕ ушла: на этой странице нет сервера, и заявка никуда " +
        "не передаётся. Я записал её у себя в браузере, чтобы вы её не " +
        "потеряли, но мне её не видно. Пока страница такая - пишите " +
        "мне напрямую или ждите, когда появится сервер.", "bad");
  }

  /* --- запуск --------------------------------------------------------- */
  function start() {
    var read = readData();
    if (!read.ok) {
      say(el("goods-msg"),
          "Реестр товаров не прочитан: " + read.причина +
          ". Показать магазин без него нельзя: человек увидит пустоту и " +
          "решит, что товаров нет.", "bad");
      el("shop-title").textContent = "Реестр не пришёл";
      el("shop-sub").textContent = "страница не знает, что продаётся";
      return;
    }

    var data = read.data;
    document.title = data.title || "Софт";
    el("shop-title").textContent = data.title || "Софт";
    el("shop-sub").textContent = data.subtitle || "";

    /* Плашка про оплату рисуется только когда оплаты нет. Когда она
     * появится по-настоящему, плашка исчезнет сама, и это единственное
     * место, где она упоминается. */
    if (!data.payment_live && data.payment_note) {
      var note = el("pay-note");
      note.hidden = false;
      note.textContent = data.payment_note;
    }

    el("foot-note").textContent = data.payment_live
      ? ""
      : "Цена указана как ориентир. Оплата не подключена.";

    drawGoods(data);

    var how = el("how-list");
    (data.how_to_buy || []).forEach(function (step) {
      var li = document.createElement("li");
      li.textContent = step;
      how.appendChild(li);
    });
    if (!(data.how_to_buy || []).length) {
      how.appendChild(document.createTextNode("шагов не описано"));
    }

    el("form-note").textContent = data.payment_live
      ? "Заявка уйдёт на сервер."
      : "Важно: эта страница работает без сервера. Заявка НЕ уйдёт " +
        "никому, и почта никуда не передаётся. Если вы оставите её " +
        "здесь, я её тоже не увижу.";

    var пом = loadRemembered();
    if (пом) {
      el("save").setChecked(true);
      if (пом.name) { el("name").value = пом.name; }
      if (пом.which) { el("which").value = пом.which; }
    }

    el("submit").addEventListener("click", submit);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();