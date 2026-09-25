// Kullanım:
//   node render.mjs                  -> iki videoyu da render eder (../videos)
//   node render.mjs mux              -> sadece müziği mevcut videolara ekler
//   node render.mjs stills 1080x1920 -> kontrol için ara kareleri PNG olarak kaydeder
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { spawn, execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(DIR, '../videos');
const FPS = 60, DUR = 15;
const AUDIO = path.resolve(DIR, '../audio/infoakademi-music.wav');
const FFMPEG = process.env.FFMPEG ||
  execSync(`python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`).toString().trim();

const TYPES = { '.html': 'text/html', '.woff2': 'font/woff2', '.js': 'text/javascript' };
const server = createServer(async (req, res) => {
  try {
    const p = path.join(DIR, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
    res.end(await readFile(p));
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--disable-gpu-vsync'] });

async function open(w, h) {
  const page = await browser.newPage({ viewport: { width: 400, height: 400 } });
  await page.goto(`http://localhost:${port}/infoakademi.html?w=${w}&h=${h}&render=1`);
  await page.evaluate(() => window.ready);
  return page;
}
async function frame(page, t) {
  const b64 = await page.evaluate(t => {
    window.renderAt(t);
    return document.getElementById('c').toDataURL('image/png').split(',')[1];
  }, t);
  return Buffer.from(b64, 'base64');
}

async function video(w, h, name) {
  const page = await open(w, h);
  const file = path.join(OUT, name);
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
    '-movflags', '+faststart', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = FPS * DUR;
  for (let i = 0; i < N; i++) {
    const png = await frame(page, i / FPS);
    if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) process.stdout.write(`\r${name} ${i}/${N}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log(`\r${name} ✓`);
  await page.close();
}

// müziği (../audio/infoakademi-music.wav, `python3 music.py` ile üretilir) videoya ekler
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
  const times = (process.argv[4] || '0.4,1.0,1.7,2.3,3.2,4.2,4.8,5.6,6.6,7.3,8.2,9.0,9.6,10.2,10.9,11.6,12.3,12.9,13.6,14.9').split(',').map(Number);
  const dir = process.argv[5] || path.join(DIR, 'stills');
  await mkdir(dir, { recursive: true });
  const page = await open(w, h);
  const { writeFile } = await import('node:fs/promises');
  for (const t of times) await writeFile(path.join(dir, `${w}x${h}_${t.toFixed(2)}.png`), await frame(page, t));
} else {
  const names = ['infoakademi-reels-1080x1920.mp4', 'infoakademi-x-1920x1080.mp4'];
  if (process.argv[2] !== 'mux') {
    await video(1080, 1920, names[0]);
    await video(1920, 1080, names[1]);
  }
  for (const n of names) mux(n);
}
await browser.close();
server.close();
