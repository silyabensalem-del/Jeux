// node render.js → PNG 1200x675 (à afficher en 600 px de large dans l'e-mail) + PNG 2400x1350 + JPG léger
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch();
  for (const s of [1, 2]) {
    const p = await b.newPage({ viewport: { width: 1200, height: 675 }, deviceScaleFactor: s });
    await p.goto('file://' + path.join(__dirname, 'email.html'));
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(__dirname, '..', s === 1 ? 'SaveTheDate_20ans_EDLC_email_1200x675.png' : 'SaveTheDate_20ans_EDLC_email_2400x1350_HD.png') });
    if (s === 1) await p.screenshot({ path: path.join(__dirname, '..', 'SaveTheDate_20ans_EDLC_email_1200x675.jpg'), type: 'jpeg', quality: 90 });
    await p.close();
  }
  await b.close();
})();
