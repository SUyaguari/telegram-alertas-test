const input = $input.first().json;
const { umbralUsd: threshold, alertarSenalSinUsd = false } = $('Umbral en USD').first().json;
const message = typeof input.body?.message === 'string' ? input.body.message : '';
if (!Number.isFinite(threshold) || threshold < 0) {
  throw new Error('El umbral en USD debe ser un número no negativo.');
}
const noAlert = [{ json: { alert: false } }];
if (input.body?.chatType !== 'group' || !message) return noAlert;

const lines = message.normalize('NFKC').split(/\r?\n/)
  .map(line => line.trim()).filter(Boolean);
const statsLine = /^(?:数据|數據|数据\s*\(|市值|价格|價格|多空比|datos\b|data\b|dados\b|données\b|market cap\b|price\b|precio\b|capitalizaci[oó]n\b)/iu;
const exchange = /交易所|取引所|거래소|бирж|بورص|منص[ةه]|\b(?:exchanges?|corretoras?|bourses?|börsen?)\b/iu;
const outflow = /流出|出金|引き出|출금|유출|вывод|отток|سحب|خروج|\b(?:outflows?|withdrawals?|withdrawn|salidas?|retiros?|sa[ií]das?|saques?|retraits?|abfl[uü]sse?)\b|\b(?:from|desde|de la|da|des)\s+(?:an?\s+|the\s+|(?:la|las|os|el|los|les)\s+)?exchanges?\b/iu;
const inflow = /流入|入金|입금|유입|депозит|приток|ввод|إيداع|ايداع|دخول|\b(?:inflows?|deposits?|entradas?|dep[oó]sitos?|d[eé]p[oô]ts?|zufl[uü]sse?)\b|\b(?:to|into|hacia|a|para)\s+(?:an?\s+|the\s+|(?:la|las|a|o|el|los|les)\s+)?exchanges?\b/iu;
const ticker = /\$\s*([A-Z0-9][A-Z0-9_-]{0,19})(?![a-zA-Z0-9_-])/gu;
const number = '(?:[0-9]{1,3}(?: [0-9]{3})+(?:[.,][0-9]+)?|[0-9]+(?:[.,][0-9]+)*)';
const unit = '(?:mil millones|mill[oó]n(?:es)?|milh(?:ão|ões)|million(?:s)?|billion(?:s)?|тыс\.?|млн\.?|млрд\.?|万|萬|亿|億|千|mil|[KMB])';
const before = new RegExp('(?:US\\s*\\$|\\bUSD\\b\\s*[:=]?|\\$)\\s*(' + number + ')\\s*(' + unit + ')?(?![\\p{L}\\p{N}.,])', 'giu');
const after = new RegExp('(?<![\\p{L}\\p{N}.,$])(' + number + ')\\s*(' + unit + ')?\\s*(?:USD\\b|d[oó]lares?\\b)', 'giu');
const factors = {
  k: 1e3, mil: 1e3, 'тыс': 1e3, 千: 1e3, 万: 1e4, 萬: 1e4,
  m: 1e6, millón: 1e6, millones: 1e6, milhão: 1e6, milhões: 1e6,
  million: 1e6, millions: 1e6, млн: 1e6, 亿: 1e8, 億: 1e8,
  b: 1e9, billion: 1e9, billions: 1e9, 'mil millones': 1e9, млрд: 1e9,
};

function amountUsd(raw, suffix) {
  let value = raw.replace(/ /g, '');
  const separators = value.match(/[.,]/g) || [];
  if (separators.length && new Set(separators).size === 2) {
    const decimal = separators.at(-1);
    value = value.split(decimal === '.' ? ',' : '.').join('').replace(decimal, '.');
  } else if (/^[0-9]{1,3}(?:([.,])[0-9]{3})(?:\1[0-9]{3})*$/u.test(value) &&
      (!suffix || separators.length > 1)) {
    value = value.replace(/[.,]/g, '');
  } else {
    value = value.replace(',', '.');
  }
  const multiplier = suffix ? factors[suffix.toLowerCase().replace(/\.$/, '')] : 1;
  return Number(value) * multiplier;
}

const group = typeof input.body.group === 'string' && input.body.group.trim()
  ? input.body.group.trim() : String(input.body.chatId ?? 'Grupo de Telegram');
const usdFormat = new Intl.NumberFormat('es-EC', { maximumFractionDigits: 6 });
const symbolStart = /^\$([A-Z0-9][A-Z0-9_-]{0,19})\s*/u;
const percent = '[+-]?[0-9]+(?:[.,][0-9]+)?%';
const oiHeader = /^\$([A-Z0-9][A-Z0-9_-]{0,19})\s*\|\s*(.+)$/u;
const oiAcceleration = new RegExp('^OI\\s+ускорение\\s*\\(([^)]+)\\)\\s*(' + percent + ')$', 'iu');
const oiGain = new RegExp('^Прирост\\s*:\\s*\\+?\\s*\\$\\s*(' + number + ')\\s*(' + unit + ')?\\s*$', 'iu');
const cycleHeader = new RegExp(
  '^\\$([A-Z0-9][A-Z0-9_-]{0,19})\\s*[·•]\\s*(\\d+\\s*[mhd])\\s*(?:价格|價格)\\s*(' + percent +
  ')\\s*\\|\\s*(?:持仓|持倉)\\s*(' + percent + ')$',
  'iu',
);

function alert(symbol, label, details, fields) {
  return [{ json: {
    alert: true,
    symbol,
    ...fields,
    text: `Alerta de Telegram | ${group}\n${symbol} · ${label}\n${details.join('\n')}\n\nMensaje original:\n${message}`,
  } }];
}

const firstLine = lines[0] ?? '';
const openInterest = firstLine.match(oiHeader);
if (openInterest && lines.some(line => oiAcceleration.test(line))) {
  const exchanges = openInterest[2].split(/\s*\+\s*/u).map(name => name.trim()).filter(Boolean);
  const increases = [];
  let market;
  let acceleration;
  for (const line of lines.slice(1)) {
    const exchangeName = exchanges.find(name => name.toLowerCase() === line.toLowerCase());
    if (exchangeName) {
      market = exchangeName;
      acceleration = undefined;
      continue;
    }
    const movement = line.match(oiAcceleration);
    if (movement && market) acceleration = movement;
    const gain = line.match(oiGain);
    if (!market || !acceleration || !gain) continue;
    const usd = amountUsd(gain[1], gain[2]);
    if (Number.isFinite(usd)) {
      increases.push({ exchange: market, usd, window: acceleration[1], change: acceleration[2] });
    }
    acceleration = undefined;
  }

  const qualifying = increases.filter(increase => increase.usd >= threshold);
  if (!qualifying.length) return noAlert;
  const details = qualifying.map(({ exchange, usd, window, change }) =>
    `${exchange}: +${usdFormat.format(usd)} USD · ${change} en ${window.replace(/ч/giu, ' h')}`);
  return alert(openInterest[1], 'Aumento de interés abierto', details, {
    type: 'open_interest_increase',
    exchanges: qualifying,
  });
}

const cycle = firstLine.match(cycleHeader);
if (cycle) {
  const signal = lines.map(line => line.match(/^(?:信号|信號)\s*:\s*(.+)$/u)).find(Boolean);
  if (!alertarSenalSinUsd || !signal) return noAlert;
  const [, symbol, window, priceChange, openInterestChange] = cycle;
  return alert(symbol, 'Señal de ciclo', [
    `Ventana: ${window} · Precio: ${priceChange} · Interés abierto: ${openInterestChange}`,
    `Señal: ${signal[1]}`,
    'Aumento en USD: no informado',
  ], { type: 'cycle_signal', window, priceChange, openInterestChange });
}

const parts = [];
for (const line of lines.slice(0, 4)) {
  if (statsLine.test(line)) break;
  parts.push(line);
}
for (let index = 0; index < parts.length; index++) {
  const line = parts[index];
  for (const header of [line, [line, parts[index + 1]].filter(Boolean).join(' ')]) {
    const isOutflow = outflow.test(header);
    const isInflow = inflow.test(header);
    if (!exchange.test(header) || isOutflow === isInflow) continue;

    const symbol = [...header.matchAll(ticker)]
      .find(match => /[A-Z]/.test(match[1]) && !/^\d+[KMB]$|^USD$/u.test(match[1]));
    if (!symbol) continue;

    const amount = [...header.matchAll(before), ...header.matchAll(after)]
      .sort((a, b) => a.index - b.index)[0];
    if (!amount) continue;
    const usd = amountUsd(amount[1], amount[2]);
    if (!Number.isFinite(usd) || usd < threshold) return noAlert;

    const direction = isOutflow ? 'Salida de exchange' : 'Entrada a exchange';
    return alert(symbol[1], direction, [`Monto: ${usdFormat.format(usd)} USD`], {
      type: 'exchange_transfer', usd, direction,
    });
  }
}
return noAlert;
