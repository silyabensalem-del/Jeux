// Rendu : node render.js  → PNG 1152x1440, PNG @2x et PDF vectoriel
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const out = path.resolve(__dirname, '..');
const [n, d] = fs.readFileSync(path.join(__dirname, 'qr_path.txt'), 'utf8').split('|');

(async () => {
  const b = await chromium.launch();
  for (const [scale, v] of [[1,'A'],[2,'A']]) {
    const p = await b.newPage({ viewport: { width: 1152, height: 1440 }, deviceScaleFactor: scale });
    await p.goto('file://' + path.join(__dirname, 'save-the-date.html'));
    await p.evaluate(([n, d]) => {
      const s = document.getElementById('qr');
      s.setAttribute('viewBox', `0 0 ${n} ${n}`);
      s.querySelector('path').setAttribute('d', d);
    }, [n, d]);
    await p.evaluate(() => document.fonts.ready);
    const name = scale === 1 ? 'SaveTheDate_20ans_EDLC_1152x1440.png' : 'SaveTheDate_20ans_EDLC_2304x2880_HD.png';
    await p.screenshot({ path: path.join(out, name) });
    if (scale === 1) await p.pdf({ path: path.join(out, 'SaveTheDate_20ans_EDLC_1152x1440.pdf'), width: '1152px', height: '1440px', printBackground: true });
    await p.close();
  }
  await b.close();
})();
