// Konuşan kişi Reels kurgusu render'ı
//   node render.mjs                  -> tüm formatlar (../videos) + müzik
//   node render.mjs mux              -> sadece müziği yeniden ekler
//   node render.mjs stills 1080x1920 [zamanlar] [klasör]
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { spawn, execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(DIR, '..');
const OUT = path.join(ROOT, 'videos');
const DARK = process.env.DARK === '1';
const AUDIO = path.join(ROOT, DARK ? 'reel/work/mix2.wav' : 'reel/work/mix.wav');
const DUR = 25;
const FFMPEG = process.env.FFMPEG ||
  execSync(`python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`).toString().trim();

const FORMATS = [
  { w: 1080, h: 1920, fps: 30, name: DARK ? 'infoakademi-reel-edit-dark-1080x1920.mp4' : 'infoakademi-reel-edit-1080x1920.mp4' },
];

const TYPES = { '.html': 'text/html', '.woff2': 'font/woff2', '.webp': 'image/webp' };
const server = createServer(async (req, res) => {
  try {
    const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
    res.end(await readFile(p));
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;
const browser = await chromium.launch();

async function open(w, h, fps = 60) {
  const page = await browser.newPage({ viewport: { width: 400, height: 400 } });
  await page.goto(`http://localhost:${port}/reel/${DARK ? 'edit2' : 'edit'}.html?w=${w}&h=${h}&fps=${fps}&render=1`);
  await page.evaluate(() => window.ready);
  return page;
}
async function frame(page, t) {
  const b64 = await page.evaluate(async t => {
    await window.renderAt(t);
    return document.getElementById('c').toDataURL('image/png').split(',')[1];
  }, t);
  return Buffer.from(b64, 'base64');
}
async function video({ w, h, fps, name }) {
  const page = await open(w, h, fps);
  const file = path.join(OUT, name);
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', file],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = fps * DUR;
  for (let i = 0; i < N; i++) {
    const png = await frame(page, i / fps);
    if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) process.stdout.write(`\r${name} ${i}/${N}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log(`\r${name} ✓`);
  await page.close();
}
function mux(name) {
  const file = path.join(OUT, name), tmp = file.replace('.mp4', '.tmp.mp4');
  execSync(`"${FFMPEG}" -y -loglevel error -i "${file}" -i "${AUDIO}" -map 0:v -map 1:a -c:v copy ` +
    `-af loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000 -c:a aac -b:a 256k -shortest -movflags +faststart "${tmp}"`);
  execSync(`mv "${tmp}" "${file}"`);
  console.log(`${name} + müzik ✓`);
}

await mkdir(OUT, { recursive: true });
if (process.argv[2] === 'stills') {
  const [w, h] = (process.argv[3] || '1080x1920').split('x').map(Number);
  const times = (process.argv[4] || '0.4,1.3,2.7,4.2,4.8,5.5,7.4,8.8,9.5,10.4,11.5,13.9,16.5,19.8,22.9,24.8').split(',').map(Number);
  const dir = process.argv[5] || path.join(DIR, 'stills');
  await mkdir(dir, { recursive: true });
  const page = await open(w, h);
  for (const t of times) await writeFile(path.join(dir, `${w}x${h}_${t.toFixed(2).padStart(5, '0')}.png`), await frame(page, t));
} else {
  if (process.argv[2] !== 'mux') for (const f of FORMATS) await video(f);
  for (const f of FORMATS) mux(f.name);
}
await browser.close();
server.close();
