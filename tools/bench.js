// Per-frame draw cost, loaded by app.js for a `,bench` link (tools/bench.sh runs it). Each batch of N synchronous draws
// ends with a one-pixel readback, which waits for the batch to rasterise; the cost of a frame is the slope between
// 30- and 90-frame batches, which cancels the readback. Chrome drops recorded canvas work that a later opaque
// full-canvas fill covers, so full-canvas fills are made a hair translucent here, or a batch would raster only its
// last frame. lin = t90 / t30: 3.0 means every frame ran. The result is logged and sent to the server as GET /bench?r=.
export async function bench(name, ctx, draw, buildMs) {
  const fill = ctx.fillRect.bind(ctx), cw = ctx.canvas.width, ch = ctx.canvas.height;
  ctx.fillRect = (x, y, w, h) => {
    const m = ctx.getTransform(), full = x * m.a + m.e <= 0 && y * m.d + m.f <= 0 && (x + w) * m.a + m.e >= cw && (y + h) * m.d + m.f >= ch;
    if (!full) return fill(x, y, w, h);
    const a = ctx.globalAlpha; ctx.globalAlpha = a * 0.996; fill(x, y, w, h); ctx.globalAlpha = a;
  };
  const batch = n => { const t0 = performance.now(); for (let i = 0; i < n; i++) draw(); ctx.getImageData(0, 0, 1, 1); return performance.now() - t0; };
  const slope = [], lin = [];
  batch(10);
  for (let k = 0; k < 7; k++) { const t30 = batch(30), t90 = batch(90); slope.push((t90 - t30) / 60); lin.push(t90 / t30); }
  ctx.fillRect = fill;
  const med = a => [...a].sort((p, q) => p - q)[a.length >> 1], r2 = v => +v.toFixed(2);
  const r = { name, page: location.href, dpr: devicePixelRatio, median: r2(med(slope)), min: r2(Math.min(...slope)), max: r2(Math.max(...slope)), lin: r2(med(lin)), build: Math.round(buildMs), gl: renderer() };
  console.log('BENCH', JSON.stringify(r));
  await fetch(`bench?${new URLSearchParams({ r: JSON.stringify(r) })}`).catch(() => {});
  return r;
}

// The GPU the canvas ran on: a software rasteriser (SwiftShader) makes every number several times worse.
function renderer() {
  try { const gl = document.createElement('canvas').getContext('webgl'), ext = gl.getExtension('WEBGL_debug_renderer_info'); return gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER); }
  catch { return 'none'; }
}
