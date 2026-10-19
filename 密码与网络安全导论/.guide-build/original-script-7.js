/* Native, offline teaching labs. Inline after DATA (before or after DOM readiness).
 * Only mounts #classical-lab, #random-lab and #sm3-lab; exports no globals.
 * All variable text, including inputs and trace data, is inserted as textContent/value.
 */
(function () {
  'use strict';

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  }
  function add(parent, tag, text, className) {
    const node = el(tag, text, className);
    parent.appendChild(node);
    return node;
  }
  function button(parent, text, action, primary) {
    const node = add(parent, 'button', text, primary ? 'btn btn-primary' : 'btn');
    node.type = 'button';
    if (action) node.addEventListener('click', action);
    return node;
  }
  function field(parent, id, label, type, value, hint) {
    const wrap = add(parent, 'div', null, 'lab-field');
    const lab = add(wrap, 'label', label);
    lab.htmlFor = id;
    const input = add(wrap, type === 'textarea' ? 'textarea' : type === 'select' ? 'select' : 'input');
    input.id = id;
    if (input.tagName === 'INPUT') input.type = type;
    if (value !== undefined) input.value = value;
    if (type === 'textarea') input.rows = 3;
    if (type === 'text' || type === 'textarea') {
      input.spellcheck = false;
      input.autocomplete = 'off';
    }
    if (hint) {
      const p = add(wrap, 'p', hint, 'caption');
      p.id = id + '-hint';
      input.setAttribute('aria-describedby', p.id);
    }
    return { wrap: wrap, input: input, label: lab };
  }
  function options(select, list) {
    list.forEach(function (item) {
      const option = add(select, 'option', item[1]);
      option.value = item[0];
    });
  }
  function status(parent, id) {
    const p = add(parent, 'p', '', 'lab-status');
    p.id = id;
    p.setAttribute('role', 'status');
    p.setAttribute('aria-live', 'polite');
    p.setAttribute('aria-atomic', 'true');
    return p;
  }
  function notice(parent, title, text, type) {
    const box = add(parent, 'div', null, 'callout ' + (type || 'intuition'));
    add(box, 'strong', title);
    add(box, 'p', text);
    return box;
  }
  function table(parent, caption, headings, rows) {
    const wrap = add(parent, 'div', null, 'table-wrap');
    wrap.tabIndex = 0;
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label', caption + '，可横向滚动');
    const t = add(wrap, 'table', null, 'lab-table');
    add(t, 'caption', caption);
    const tr = add(add(t, 'thead'), 'tr');
    headings.forEach(function (heading) {
      const th = add(tr, 'th', heading);
      th.scope = 'col';
    });
    const body = add(t, 'tbody');
    rows.forEach(function (row) {
      const r = add(body, 'tr');
      row.forEach(function (value, i) {
        const cell = add(r, i === 0 ? 'th' : 'td');
        if (i === 0) cell.scope = 'row';
        if (value && typeof value === 'object' && value.nodeType) cell.appendChild(value);
        else cell.textContent = String(value);
      });
    });
    return t;
  }
  function fail(input, message) {
    const error = new Error(message);
    error.input = input;
    throw error;
  }
  function clearInvalid(inputs) {
    inputs.forEach(function (input) { input.removeAttribute('aria-invalid'); });
  }
  function reportError(output, live, error) {
    output.replaceChildren();
    live.textContent = error.message;
    live.classList.add('lab-error');
    if (error.input) {
      error.input.setAttribute('aria-invalid', 'true');
      error.input.focus();
    }
  }
  function success(live, text) {
    live.classList.remove('lab-error');
    live.textContent = text;
  }
  function stale(form, output, live, callback) {
    function change() {
      clearInvalid(Array.from(form.querySelectorAll('input,textarea,select')));
      output.replaceChildren();
      success(live, '参数已更改；请重新计算，旧结果已清除。');
      if (callback) callback();
    }
    form.addEventListener('input', change);
    form.addEventListener('change', change);
  }
  function configureRoot(root, title) {
    root.classList.add('lab', 'native-lab');
    const heading = add(root, 'h3', title);
    heading.id = root.id + '-title';
    root.setAttribute('aria-labelledby', heading.id);
  }

  function classical(root) {
    configureRoot(root, '古典密码逐字演算台');
    add(root, 'p', '先编码，再加减，最后取模。只演示已知密钥的加密与解密，不提供密钥搜索或破解功能。');
    notice(root, '教学约定', 'A=0，B=1，…，Z=25；输入忽略大小写，输出统一大写。仅允许英文字母和普通空格，空格原样保留、不消耗密钥位；最多150个字符（含空格）。古典密码不能保护真实秘密。');
    const form = add(root, 'form', null, 'lab-controls');
    form.noValidate = true;
    const preset = field(form, 'cl-preset', '原题预设', 'select');
    options(preset.input, [
      ['hello', '移位：HELLOWORLD，K=3（第二讲P9、32–33）'],
      ['midnight', '移位：we will meet at midnight，K=11（P11–12）'],
      ['cipher', '维吉尼亚：HELLOWORLD，CIPHER（P21）'],
      ['key', '维吉尼亚：CRYPTOGRAPHY，KEY（P23–24、50）']
    ]);
    const presetBar = add(form, 'div', null, 'lab-actions');
    const grid = add(form, 'div', null, 'lab-grid');
    const method = field(grid, 'cl-method', '算法', 'select');
    options(method.input, [['shift', '移位密码'], ['vigenere', '维吉尼亚密码']]);
    const direction = field(grid, 'cl-direction', '运算方向', 'select');
    options(direction.input, [['encrypt', '加密（加密钥）'], ['decrypt', '解密（减密钥）']]);
    const shift = field(grid, 'cl-shift', '移位量 K', 'text', '3', '只接受0–25的十进制整数；K=0也是合法密钥。');
    shift.input.inputMode = 'numeric';
    shift.input.maxLength = 2;
    const key = field(grid, 'cl-key', '循环密钥 KEY', 'text', 'KEY', '1–150个英文字母；不能包含空格、数字或标点。');
    key.input.maxLength = 150;
    const text = field(form, 'cl-text', '待加密或解密的文字', 'textarea', 'HELLOWORLD');
    text.input.maxLength = 150;
    const actions = add(form, 'div', null, 'lab-actions');
    const run = button(actions, '生成逐字演算表', null, true);
    run.type = 'submit';
    const reverse = button(actions, '用结果反向验算', reverseResult);
    reverse.disabled = true;
    const live = status(root, 'cl-status');
    const output = add(root, 'div', null, 'lab-output');
    let result = null;
    const presets = {
      hello: ['shift', 'HELLOWORLD', '3', '第二讲P33原答案首两字母有误；正确答案为 KHOORZRUOG。'],
      midnight: ['shift', 'we will meet at midnight', '11', '第二讲P11–12：T=19，19+11=30，30 mod26=4，对应E，不是3。'],
      cipher: ['vigenere', 'HELLOWORLD', 'CIPHER', '第二讲P21：循环密钥流为CIPHERCIPH，结果为JMASSNQZAK。'],
      key: ['vigenere', 'CRYPTOGRAPHY', 'KEY', '第二讲P23–24、32–33、50：KEY重复四次，结果为MVWZXMQVYZLW。']
    };
    const sourceNote = add(root, 'p', presets.hello[3], 'caption');
    function syncMode() {
      const isShift = method.input.value === 'shift';
      shift.wrap.hidden = !isShift;
      shift.input.disabled = !isShift;
      key.wrap.hidden = isShift;
      key.input.disabled = isShift;
    }
    function calculate(event) {
      if (event) event.preventDefault();
      result = null;
      reverse.disabled = true;
      clearInvalid([text.input, shift.input, key.input, method.input, direction.input]);
      output.replaceChildren();
      try {
        const raw = text.input.value;
        if (!raw.length || raw.length > 150 || !/^[A-Za-z ]+$/.test(raw) || !/[A-Za-z]/.test(raw)) {
          fail(text.input, '文字须含至少一个英文字母，最多150字符；只允许A–Z、a–z和普通空格，不允许换行或标点。');
        }
        if (!['shift', 'vigenere'].includes(method.input.value)) fail(method.input, '请选择有效算法。');
        if (!['encrypt', 'decrypt'].includes(direction.input.value)) fail(direction.input, '请选择加密或解密。');
        const isShift = method.input.value === 'shift';
        let keys;
        if (isShift) {
          if (!/^(0|[1-9]|1[0-9]|2[0-5])$/.test(shift.input.value)) fail(shift.input, 'K必须是0–25的整数；不接受符号、小数、指数或多余空格。');
          keys = [Number(shift.input.value)];
        } else {
          if (!/^[A-Za-z]{1,150}$/.test(key.input.value)) fail(key.input, 'KEY须为1–150个英文字母，不能含空格、数字或标点。');
          keys = Array.from(key.input.value.toUpperCase(), function (c) { return c.charCodeAt(0) - 65; });
        }
        const decrypt = direction.input.value === 'decrypt';
        const sign = decrypt ? '−' : '+';
        let letterIndex = 0;
        let answer = '';
        const rows = Array.from(raw.toUpperCase(), function (char, pos) {
          if (char === ' ') {
            answer += ' ';
            return [pos + 1, '空格', '不编码', '不消耗密钥位', '—', '—', '空格（原样保留）'];
          }
          const x = char.charCodeAt(0) - 65;
          const keyIndex = letterIndex % keys.length;
          const k = keys[keyIndex];
          const total = decrypt ? x - k : x + k;
          const remainder = ((total % 26) + 26) % 26;
          const out = String.fromCharCode(65 + remainder);
          answer += out;
          letterIndex += 1;
          return [pos + 1, char, x, isShift ? 'K=' + k : '第' + (keyIndex + 1) + '位 ' + String.fromCharCode(65 + k) + '=' + k,
            x + ' ' + sign + ' ' + k + ' = ' + total, total + ' mod26 = ' + remainder, out];
        });
        add(output, 'h4', decrypt ? '解密结果（大写）' : '加密结果（大写）');
        const answerNode = add(output, 'pre', answer, 'mono lab-result');
        answerNode.tabIndex = 0;
        add(output, 'p', '公式：' + (decrypt ? 'x=(y−k) mod26' : 'y=(x+k) mod26') + '。余数统一在0–25之间；负数也必须归一化，例如−3 mod26=23。', 'caption');
        table(output, '每个输入位置的完整演算（空格也列出）', ['位置', '输入', '编码', '所用密钥', '加减（未取模）', '非负余数', '输出'], rows);
        result = answer;
        reverse.disabled = false;
        success(live, '已完成' + (decrypt ? '解密' : '加密') + '：' + letterIndex + '个字母，' + (raw.length - letterIndex) + '个空格。完整结果与逐字步骤在下方。');
      } catch (error) { reportError(output, live, error); }
    }
    function reverseResult() {
      if (result === null) return;
      text.input.value = result;
      direction.input.value = direction.input.value === 'encrypt' ? 'decrypt' : 'encrypt';
      calculate();
    }
    button(presetBar, '载入原题并演算', function () {
      const p = presets[preset.input.value];
      if (!p) return;
      method.input.value = p[0];
      text.input.value = p[1];
      (p[0] === 'shift' ? shift.input : key.input).value = p[2];
      direction.input.value = 'encrypt';
      sourceNote.textContent = p[3];
      syncMode();
      calculate();
    });
    stale(form, output, live, function () {
      result = null;
      reverse.disabled = true;
      sourceNote.textContent = '自定义参数；原题预设需点击“载入原题并演算”。';
      syncMode();
    });
    form.addEventListener('submit', calculate);
    syncMode();
    calculate();
  }

  // Decimal values are bounded BEFORE conversion to BigInt. No precision-losing Number arithmetic.
  function decimal(input, label, maxDigits) {
    const value = input.value;
    if (value.length < 1 || value.length > maxDigits || !/^[0-9]+$/.test(value)) {
      fail(input, label + '须为最多' + maxDigits + '位的非负十进制整数，不接受负号、小数、指数、空格或十六进制。');
    }
    return BigInt(value);
  }
  function stepCount(input) {
    if (!/^[1-9][0-9]{0,2}$/.test(input.value) || Number(input.value) > 100) fail(input, '步数须为1–100的整数。');
    return Number(input.value);
  }
  function integerField(parent, id, label, value, maxLength, hint) {
    const f = field(parent, id, label, 'text', value, hint);
    f.input.inputMode = 'numeric';
    f.input.maxLength = maxLength;
    return f.input;
  }
  function random(root) {
    configureRoot(root, '确定性发生器实验');
    notice(root, '只供学习，不能生成真实密钥', 'LCG与平方取中法都不是密码学安全随机数生成器。长周期、看似均匀或改变种子，都不代表不可预测。不要将这里的输出用作密钥、口令、验证码或安全令牌。', 'trap');
    if (typeof BigInt !== 'function') {
      notice(root, '浏览器不支持BigInt', '请使用支持BigInt的现代浏览器；本实验不会退回可能丢失精度的浮点运算。', 'trap');
      return;
    }
    add(root, 'h4', '线性同余 LCG');
    add(root, 'p', 'Xₙ₊₁=(aXₙ+c) mod m。所有乘加和取模使用BigInt。m限制为2–10³⁰，0<a<m，0≤c<m，0≤X₀<m；每次最多100步。');
    const form = add(root, 'form', null, 'lab-controls');
    form.noValidate = true;
    const grid = add(form, 'div', null, 'lab-grid');
    const m = integerField(grid, 'lcg-m', '模数 m', '4', 31);
    const a = integerField(grid, 'lcg-a', '乘数 a', '1', 31);
    const c = integerField(grid, 'lcg-c', '增量 c', '1', 31);
    const seed = integerField(grid, 'lcg-seed', '初始状态 X₀', '3', 31);
    const steps = integerField(grid, 'lcg-steps', '递推步数', '8', 3, '1–100步；行n展示从Xₙ₋₁算出Xₙ。');
    const bar = add(form, 'div', null, 'lab-actions');
    const run = button(bar, '计算LCG序列', null, true);
    run.type = 'submit';
    const live = status(root, 'lcg-status');
    const output = add(root, 'div', null, 'lab-output');
    notice(root, '原题反例：相同前四个输出，不同第五个', '第三讲P14–20：观测X₁…X₄=0,1,2,3，只能推出a=c=1、整数m≥4。m=4时X₅=0，m=5时X₅=4；m=3不可能输出3。预设取X₀=m−1，使表格与原题的X₁起始编号一致。', 'intuition');
    function calculate(event) {
      if (event) event.preventDefault();
      clearInvalid([m, a, c, seed, steps]);
      output.replaceChildren();
      try {
        const modulus = decimal(m, 'm', 31);
        const multiplier = decimal(a, 'a', 31);
        const increment = decimal(c, 'c', 31);
        let x = decimal(seed, 'X₀', 31);
        const count = stepCount(steps);
        if (modulus < 2n || modulus > 10n ** 30n) fail(m, 'm必须在2到10³⁰之间。');
        if (multiplier < 1n || multiplier >= modulus) fail(a, 'a必须满足0<a<m。');
        if (increment >= modulus) fail(c, 'c必须满足0≤c<m。');
        if (x >= modulus) fail(seed, 'X₀必须满足0≤X₀<m。');
        const initial = x;
        const seen = new Map([[String(x), 0]]);
        let cycle = null;
        const rows = [];
        const sequence = [];
        for (let n = 1; n <= count; n += 1) {
          const previous = x;
          const total = multiplier * previous + increment;
          x = total % modulus;
          let note = '首次出现';
          if (seen.has(String(x))) {
            const first = seen.get(String(x));
            note = '与X' + first + '相同';
            if (!cycle) cycle = { start: first, period: n - first };
          } else seen.set(String(x), n);
          rows.push(['X' + n, previous, multiplier + ' × ' + previous + ' + ' + increment + ' = ' + total, total + ' mod ' + modulus + ' = ' + x, x, note]);
          sequence.push(String(x));
        }
        add(output, 'p', '初始状态X₀=' + initial + '；下方输出从X₁开始。', 'caption');
        add(output, 'pre', sequence.join(' → '), 'mono lab-result');
        table(output, 'LCG逐步乘加与取模', ['输出项', '前一状态', '完整乘加', '取模', '新状态', '重复检查'], rows);
        const note = cycle ? '观察到循环：从X' + cycle.start + '进入，周期为' + cycle.period + '。' : '本次' + count + '步内未见重复，不表示不会循环，更不表示安全。';
        add(output, 'p', note, 'caption');
        success(live, '已用BigInt精确计算' + count + '步。' + note);
      } catch (error) { reportError(output, live, error); }
    }
    [4, 5].forEach(function (modulus) {
      button(bar, '反例 m=' + modulus, function () {
        m.value = String(modulus); a.value = '1'; c.value = '1'; seed.value = String(modulus - 1); steps.value = '8';
        calculate();
      });
    });
    stale(form, output, live);
    form.addEventListener('submit', calculate);
    calculate();

    add(root, 'h4', '平方取中：补零后再截取');
    add(root, 'p', '采用偶数位十进制状态：先平方，左补零至2d位，再取正中间d位。d可选2、4、6、8、10、12；最多100步。前导零是显示宽度的一部分，不能省略。');
    const squareForm = add(root, 'form', null, 'lab-controls');
    squareForm.noValidate = true;
    const squareGrid = add(squareForm, 'div', null, 'lab-grid');
    const width = field(squareGrid, 'square-width', '状态宽度 d（十进制位数）', 'select');
    options(width.input, [2, 4, 6, 8, 10, 12].map(function (d) { return [String(d), d + '位']; }));
    width.input.value = '4';
    const squareSeed = integerField(squareGrid, 'square-seed', '初始状态（可含前导零）', '1326', 12, '最多d位数字；不足d位时左补零。');
    const squareSteps = integerField(squareGrid, 'square-steps', '平方取中步数', '5', 3, '1–100步。');
    const squareBar = add(squareForm, 'div', null, 'lab-actions');
    const squareRun = button(squareBar, '计算平方取中', null, true);
    squareRun.type = 'submit';
    const squareLive = status(root, 'square-status');
    const squareOutput = add(root, 'div', null, 'lab-output');
    function calculateSquare(event) {
      if (event) event.preventDefault();
      clearInvalid([width.input, squareSeed, squareSteps]);
      squareOutput.replaceChildren();
      try {
        if (!['2', '4', '6', '8', '10', '12'].includes(width.input.value)) fail(width.input, '状态宽度必须是2–12的偶数。');
        const d = Number(width.input.value);
        let x = decimal(squareSeed, '初始状态', d);
        const count = stepCount(squareSteps);
        const seen = new Map([[String(x), 0]]);
        let cycle = null;
        const rows = [];
        for (let n = 1; n <= count; n += 1) {
          const before = x.toString().padStart(d, '0');
          const squared = x * x;
          const full = squared.toString().padStart(2 * d, '0');
          const middle = full.slice(d / 2, d / 2 + d);
          const digits = el('span', null, 'mono lab-square-digits');
          add(digits, 'span', full.slice(0, d / 2));
          add(digits, 'mark', middle);
          add(digits, 'span', full.slice(d / 2 + d));
          digits.setAttribute('aria-label', '补零平方' + full + '；取中间' + d + '位' + middle);
          x = BigInt(middle);
          let note = '首次出现';
          if (seen.has(String(x))) {
            const first = seen.get(String(x));
            note = '与第' + first + '步状态相同';
            if (!cycle) cycle = { start: first, period: n - first };
          } else seen.set(String(x), n);
          rows.push([n, before, before + '² = ' + squared, digits, middle, note]);
        }
        table(squareOutput, '平方取中完整计算（第0步为初始状态）', ['步', '旧状态', '精确平方', '补足2d位／高亮中间d位', '新状态', '重复检查'], rows);
        const note = cycle ? '已发现循环：第' + cycle.start + '步起，周期' + cycle.period + '。' : '本次未见重复；有限状态的确定性发生器最终必然进入循环。';
        add(squareOutput, 'p', note, 'caption');
        success(squareLive, '已用BigInt完成' + count + '步平方取中。' + note);
      } catch (error) { reportError(squareOutput, squareLive, error); }
    }
    button(squareBar, '原题 1326（第三讲P12）', function () {
      width.input.value = '4'; squareSeed.value = '1326'; squareSteps.value = '5'; calculateSquare();
    });
    button(squareBar, '退化反例 0000', function () {
      width.input.value = '4'; squareSeed.value = '0000'; squareSteps.value = '5'; calculateSquare();
    });
    stale(squareForm, squareOutput, squareLive);
    squareForm.addEventListener('submit', calculateSquare);
    calculateSquare();
  }

  const IV = ['7380166f', '4914b2b9', '172442d7', 'da8a0600', 'a96f30bc', '163138aa', 'e38dee4d', 'b0fb0e4e'];
  const ABC_DIGEST = '66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0';
  function hex(value) { return (value >>> 0).toString(16).padStart(8, '0'); }
  function word(value) { return parseInt(value, 16) >>> 0; }
  function rol(value, shift) {
    const n = shift % 32;
    return ((value << n) | (value >>> ((32 - n) % 32))) >>> 0;
  }
  function p0(x) { return (x ^ rol(x, 9) ^ rol(x, 17)) >>> 0; }
  function p1(x) { return (x ^ rol(x, 15) ^ rol(x, 23)) >>> 0; }
  // Reject incomplete/wrong trace instead of silently presenting a misleading partial lab.
  function validateTrace(trace) {
    function check(condition) { if (!condition) throw new Error('SM3 trace缺失、不完整或验算不一致；请内嵌完整的lec3_audit/sm3_abc_trace.json到DATA.trace，再重新打开页面。'); }
    function hexWord(value) { return typeof value === 'string' && /^[0-9a-fA-F]{8}$/.test(value); }
    check(trace && Array.isArray(trace.W) && trace.W.length === 68 && Array.isArray(trace.W_prime) && trace.W_prime.length === 64 && Array.isArray(trace.rounds) && trace.rounds.length === 64);
    check(trace.W.every(hexWord) && trace.W_prime.every(hexWord) && trace.digest === ABC_DIGEST);
    check(trace.L === 24 && trace.K === 423 && typeof trace.padded_hex === 'string' && trace.padded_hex.toLowerCase() === '61626380' + '0'.repeat(118) + '18');
    const W = trace.W.map(word);
    for (let j = 0; j < 68; j += 1) {
      if (j < 16) check(hex(W[j]) === trace.padded_hex.slice(j * 8, j * 8 + 8).toLowerCase());
      else check(W[j] === ((p1(W[j - 16] ^ W[j - 9] ^ rol(W[j - 3], 15)) ^ rol(W[j - 13], 7) ^ W[j - 6]) >>> 0));
    }
    let state = IV.map(word);
    trace.rounds.forEach(function (round, j) {
      check(round && round.j === j && Array.isArray(round.state) && round.state.length === 8 && round.state.every(hexWord));
      check(['FF', 'GG', 'SS1', 'SS2', 'TT1', 'TT2'].every(function (key) { return hexWord(round[key]); }));
      check(word(trace.W_prime[j]) === ((W[j] ^ W[j + 4]) >>> 0));
      const [A, B, C, D, E, F, G, H] = state;
      const FF = (j < 16 ? A ^ B ^ C : (A & B) | (A & C) | (B & C)) >>> 0;
      const GG = (j < 16 ? E ^ F ^ G : (E & F) | (~E & G)) >>> 0;
      const SS1 = rol((rol(A, 12) + E + rol(j < 16 ? 0x79cc4519 : 0x7a879d8a, j)) >>> 0, 7);
      const SS2 = (SS1 ^ rol(A, 12)) >>> 0;
      const TT1 = (FF + D + SS2 + word(trace.W_prime[j])) >>> 0;
      const TT2 = (GG + H + SS1 + W[j]) >>> 0;
      const calculated = { FF: FF, GG: GG, SS1: SS1, SS2: SS2, TT1: TT1, TT2: TT2 };
      Object.keys(calculated).forEach(function (key) { check(calculated[key] === word(round[key])); });
      state = [TT1, A, rol(B, 9), C, p0(TT2), E, rol(F, 19), G];
      check(state.every(function (value, i) { return value === word(round.state[i]); }));
    });
    check(state.map(function (value, i) { return hex(value ^ word(IV[i])); }).join('') === trace.digest);
    return trace;
  }

  function sm3(root) {
    configureRoot(root, 'SM3：跟踪abc的64轮压缩');
    add(root, 'p', '消息是小写abc，不含引号、空格或换行。来源：第三讲P42–53；完整trace为经复算的理解补充，并非课件原有的64轮表。');
    let trace;
    try {
      // Supports both a classic-script lexical `const DATA` and window.DATA.
      trace = validateTrace(typeof DATA !== 'undefined' ? DATA.trace : window.DATA && window.DATA.trace);
    } catch (error) {
      const live = status(root, 'sm3-error');
      live.classList.add('lab-error');
      live.textContent = error.message;
      return;
    }
    notice(root, '先约定读法', '所有8位十六进制字都是32bit；“+”只保留低32bit（mod 2³²）；<<<是32位循环左移，位移量按mod32；⊕为按位异或，∧为与，∨为或，¬为32位取反。j从0计数，因此j=16是第17轮。');
    const controls = add(root, 'div', null, 'lab-controls');
    const slider = field(controls, 'sm3-round', '轮下标 j（0–63）', 'range', '0', '方向键逐轮移动；Home到0，End到63。也可使用下方跳转按钮。');
    slider.input.min = '0'; slider.input.max = '63'; slider.input.step = '1';
    const bar = add(controls, 'div', null, 'lab-actions');
    const previous = button(bar, '上一轮', function () { render(current - 1); });
    const next = button(bar, '下一轮', function () { render(current + 1); });
    const jumpButtons = [0, 15, 16, 63].map(function (j) {
      return { j: j, button: button(bar, '跳到 j=' + j, function () { render(j); }) };
    });
    const live = status(root, 'sm3-status');
    const boundary = notice(root, 'j=16是切换边界', '', 'trap');
    const boundaryText = boundary.querySelector('p');
    const output = add(root, 'div', null, 'lab-output');
    output.id = 'sm3-round-output';
    slider.input.setAttribute('aria-controls', output.id);
    let current = 0;
    function render(j) {
      if (!Number.isInteger(j) || j < 0 || j > 63) return;
      current = j;
      const round = trace.rounds[j];
      const before = j === 0 ? IV : trace.rounds[j - 1].state;
      const T = j < 16 ? 0x79cc4519 : 0x7a879d8a;
      slider.input.value = String(j);
      slider.input.setAttribute('aria-valuetext', 'j=' + j + '，第' + (j + 1) + '轮，共64轮');
      previous.disabled = j === 0;
      next.disabled = j === 63;
      jumpButtons.forEach(function (entry) { entry.button.setAttribute('aria-pressed', String(entry.j === j)); });
      boundaryText.textContent = j < 16
        ? '当前j=' + j + '：仍在0–15段，Tj=79cc4519，FF和GG都取三个输入的异或。' + (j === 15 ? '这是前一段最后一轮；点“下一轮”观察三项一起切换。' : '到j=16时才同时切换常量与FF/GG。')
        : '当前j=' + j + '：已在16–63段，Tj=7a879d8a；FF改为多数函数，GG改为选择函数。' + (j === 16 ? '这正是边界第一轮；不是j=15，也不是j=17。' : '后续轮保持此规则直到j=63。');
      output.replaceChildren();
      add(output, 'h4', 'j=' + j + '：第' + (j + 1) + '轮 / 64轮');
      add(output, 'p', j === 0 ? '本轮前状态直接取IV（V₀），不是第0轮的轮后状态。' : '本轮前状态取j=' + (j - 1) + '的轮后状态。所有右侧计算均使用旧寄存器值。', 'caption');
      const updateRules = ['TT1', '旧A', '旧B <<< 9', '旧C', 'P0(TT2)', '旧E', '旧F <<< 19（注意是G，不是D）', '旧G'];
      table(output, 'A–H轮前与轮后状态（十六进制）', ['寄存器', j === 0 ? '轮前：IV' : '轮前：上一轮输出', '轮后：本轮输出', '更新来源'],
        Array.from('ABCDEFGH', function (name, i) { return [name, before[i], round.state[i], updateRules[i]]; }));
      const ffRule = j < 16 ? 'A⊕B⊕C' : '(A∧B)∨(A∧C)∨(B∧C)';
      const ggRule = j < 16 ? 'E⊕F⊕G' : '(E∧F)∨((¬E)∧G)';
      table(output, '本轮消息字、常量与中间量（十六进制）', ['量', '值', '本轮计算规则'], [
        ['W[' + j + ']', trace.W[j], '本轮消息扩展字'],
        ['W′[' + j + ']', trace.W_prime[j], 'W[' + j + ']⊕W[' + (j + 4) + ']'],
        ['Tj', hex(T), j < 16 ? '0≤j≤15：79cc4519' : '16≤j≤63：7a879d8a'],
        ['Tj <<< (j mod32)', hex(rol(T, j)), '本轮循环左移' + (j % 32) + '位'],
        ['A <<< 12', hex(rol(word(before[0]), 12)), '旧A循环左移12位'],
        ['FFj(A,B,C)', round.FF, ffRule],
        ['GGj(E,F,G)', round.GG, ggRule],
        ['SS1', round.SS1, '((A<<<12)+E+(Tj<<<(j mod32)))<<<7'],
        ['SS2', round.SS2, 'SS1⊕(A<<<12)'],
        ['TT1', round.TT1, 'FFj(A,B,C)+D+SS2+W′[' + j + ']（mod 2³²）'],
        ['TT2', round.TT2, 'GGj(E,F,G)+H+SS1+W[' + j + ']（mod 2³²）'],
        ['P0(TT2)', hex(p0(word(round.TT2))), 'TT2⊕(TT2<<<9)⊕(TT2<<<17)，送入新E']
      ]);
      if (j === 63) notice(output, '还差最后的前馈异或', '第63轮的轮后A…H不是最终摘要。abc只有一个块，须将它们逐字与IV异或，得到下面的256bit摘要。', 'trap');
      success(live, '已显示j=' + j + '（第' + (j + 1) + '轮）；' + (j < 16 ? '异或阶段。' : '多数／选择阶段。') + (j === 0 ? '轮前状态为IV。' : ''));
    }
    slider.input.addEventListener('input', function () { render(Number(slider.input.value)); });
    slider.input.addEventListener('change', function () { render(Number(slider.input.value)); });
    render(0);

    const expanded = add(root, 'details', null, 'lab-details');
    add(expanded, 'summary', '核对填充与全部68个W、64个W′');
    add(expanded, 'p', 'abc为24bit，补1bit的1、423bit的0，再附64bit大端长度24；总计512bit。只有整条填充消息最后64bit存原长。');
    add(expanded, 'pre', trace.padded_hex, 'mono lab-result');
    add(expanded, 'p', 'P1(X)=X⊕(X<<<15)⊕(X<<<23)；W[j]=P1(W[j−16]⊕W[j−9]⊕(W[j−3]<<<15))⊕(W[j−13]<<<7)⊕W[j−6]，16≤j≤67；W′[j]=W[j]⊕W[j+4]，0≤j≤63。', 'caption');
    table(expanded, '全部消息扩展字（68个W不等于68轮）', ['下标', 'W', 'W′'], trace.W.map(function (w, i) { return [i, w, i < 64 ? trace.W_prime[i] : '—（不定义）']; }));
    const finalSection = add(root, 'div', null, 'lab-final');
    add(finalSection, 'h4', '最终摘要：完成64轮，再与IV异或');
    const feedforward = add(finalSection, 'details', null, 'lab-details');
    add(feedforward, 'summary', '展开最终8个字的前馈异或');
    table(feedforward, '最终状态逐字与IV异或，不是相加', ['字', '第63轮后', 'IV', '异或所得摘要字'], IV.map(function (iv, i) {
      return [String.fromCharCode(65 + i), trace.rounds[63].state[i], iv, trace.digest.slice(i * 8, i * 8 + 8)];
    }));
    const digestField = field(finalSection, 'sm3-digest', 'SM3(abc)，完整64位十六进制摘要', 'textarea', trace.digest, '256bit=32字节=64个十六进制字符；复制不含空格或换行。');
    digestField.input.readOnly = true;
    digestField.input.classList.add('mono');
    digestField.input.rows = 2;
    const copyBar = add(finalSection, 'div', null, 'lab-actions');
    const copyLive = status(finalSection, 'sm3-copy-status');
    const copyButton = button(copyBar, '复制完整摘要', async function () {
      copyButton.disabled = true;
      let copied = false;
      try {
        if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
          try { await navigator.clipboard.writeText(trace.digest); copied = true; } catch (_) { /* file:// or denied permission: use local fallback. */ }
        }
        if (!copied) {
          digestField.input.focus();
          digestField.input.select();
          digestField.input.setSelectionRange(0, trace.digest.length);
          try { copied = typeof document.execCommand === 'function' && document.execCommand('copy'); } catch (_) { copied = false; }
        }
        if (copied) {
          success(copyLive, '已复制完整64字符摘要。');
        } else {
          digestField.input.focus();
          digestField.input.select();
          success(copyLive, '浏览器禁止自动复制。摘要已选中，请按Ctrl+C（Mac为⌘C）或使用系统复制菜单。');
        }
      } finally { copyButton.disabled = false; }
    });
    notice(root, '课件勘误', '第三讲P50–52：前16轮常量应为79cc4519；两段下标为0–15、16–63；寄存器更新应为G←F<<<19，不是D←F<<<19。最终一步是与输入链值异或，不是直接输出轮后状态。', 'trap');
  }

  function init() {
    [['classical-lab', classical], ['random-lab', random], ['sm3-lab', sm3]].forEach(function (entry) {
      const root = document.getElementById(entry[0]);
      if (!root || root.dataset.nativeLabMounted === 'true') return;
      root.dataset.nativeLabMounted = 'true';
      root.replaceChildren();
      try { entry[1](root); }
      catch (_) {
        const live = status(root, entry[0] + '-fatal');
        live.classList.add('lab-error');
        live.textContent = '此实验未能初始化。请使用支持原生ES2020与BigInt的现代浏览器，并检查内嵌数据；其他实验不受影响。';
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
}());
