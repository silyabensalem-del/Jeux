// Export de video.html en MP4 1080x1080, 30 i/s.
// Usage : node export.js [dossier_images] [fichier.mp4]  (nécessite playwright + ffmpeg)
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const FPS = 30;
const frames = process.argv[2] || path.join(__dirname, 'frames');
const out = process.argv[3] || path.join(__dirname, '..', 'Video_20ans_EDLC_1080x1080.mp4');
const only = process.env.ONLY ? process.env.ONLY.split(',').map(Number) : null; // ex. ONLY=1,3,7 (secondes) pour des aperçus
(async () => {
  fs.mkdirSync(frames, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'video.html'));
  await page.evaluate(() => window.ready);
  const dur = await page.evaluate(() => window.DUR);
  const times = only || Array.from({ length: Math.round(dur * FPS) }, (_, i) => i / FPS);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => window.render(t), times[i]);
    await page.screenshot({ path: path.join(frames, `f${String(i).padStart(4, '0')}.png`) });
  }
  await browser.close();
  if (only) return;
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(frames, 'f%04d.png'),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart', out], { stdio: 'inherit' });
  console.log('OK ->', out);
})();
