// Export d'une animation HTML (fonction window.render(t)) en MP4 1080x1080, 30 i/s.
// Usage : [HTML=video_pro.html] [SUB=4] [GRAIN=1] node export.js [dossier_images] [fichier.mp4]
//   SUB   : nombre de sous-images fusionnées par image (flou de mouvement, obturateur 180°). 1 = sans flou.
//   GRAIN : ajoute un grain d'image léger.
//   ONLY=1,3,7 : n'exporte que ces instants (en secondes), pour des aperçus.
// Nécessite playwright + ffmpeg.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const FPS = 30, SUB = Number(process.env.SUB || 1);
const frames = process.argv[2] || path.join(__dirname, 'frames');
const out = process.argv[3] || path.join(__dirname, '..', 'Video_20ans_EDLC_1080x1080.mp4');
const only = process.env.ONLY ? process.env.ONLY.split(',').map(Number) : null;
(async () => {
  fs.mkdirSync(frames, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, process.env.HTML || 'video.html'));
  await page.evaluate(() => window.ready);
  const dur = await page.evaluate(() => window.DUR);
  const times = only || Array.from({ length: Math.round(dur * FPS) }, (_, i) => i / FPS);
  const sub = only ? 1 : SUB;
  let n = 0;
  for (const t0 of times)
    for (let s = 0; s < sub; s++) {
      await page.evaluate(t => window.render(t), t0 + (s / sub) * 0.5 / FPS);
      await page.screenshot({ path: path.join(frames, `f${String(n++).padStart(5, '0')}.png`) });
    }
  await browser.close();
  if (only) return;
  const vf = [];
  if (sub > 1) vf.push(`tmix=frames=${sub}`, `select='eq(mod(n\\,${sub})\\,${sub - 1})'`, `setpts=N/(${FPS}*TB)`);
  if (process.env.GRAIN) vf.push('noise=alls=5:allf=t');
  vf.push('format=yuv420p');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS * sub), '-i', path.join(frames, 'f%05d.png'),
    '-vf', vf.join(','), '-r', String(FPS), '-c:v', 'libx264', '-crf', '17', '-preset', 'slow',
    '-movflags', '+faststart', out], { stdio: 'inherit' });
  console.log('OK ->', out);
})();
