// Read Pangram's verdict and AI share for every uploaded file on the dashboard results page.
//
// Run it with Claude in Chrome's javascript_tool on https://www.pangram.com/dashboard after "Check for AI" has
// finished, in your own tab. It clicks each file row, waits for that file's report, and reads the verdict line
// ("NN% of this text is AI" or "... Human") and the legend ("AI NN% Human NN%"). It works in the background;
// read the result with a second call: JSON.stringify(window.__pangram).
// The selectors are the ones the dashboard had on 2026-11-06 (B37, B38); if rows come back as {error: true},
// inspect one row's parents and update `rowSelector`.
//
// Each record: {name, pct, kind, legend_ai, words}. AI share = pct when kind is "AI", else legend_ai, else 100 - pct.
// Record the dashboard credit balance before and after the batch (the balance difference is what counts; per-file
// charges are ceil(words / 100) and sum slightly higher).
window.__pangram = []; window.__pangramDone = false;
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const rowSelector = 'button.w-full.text-left';
  const rows = [...document.querySelectorAll(rowSelector)].filter(b => /\.docx/.test(b.innerText));
  const seen = new Set();
  for (const b of rows) {
    const name = b.innerText.split('\n')[0].trim();
    if (seen.has(name)) continue;
    seen.add(name);
    b.click();
    let rec = null;
    for (let k = 0; k < 60; k++) {
      await sleep(200);
      const heads = [...document.querySelectorAll('h1,h2,h3')].map(h => h.innerText.trim());
      if (!heads.includes(name)) continue;
      const t = document.body.innerText;
      const a = t.match(/(\d+(?:\.\d+)?)\s*%\s*of this text is\s*(AI|Human Written|Human)/);
      const leg = t.match(/AI\s+(\d+(?:\.\d+)?)%\s*[\s•·]*Human\s+(\d+(?:\.\d+)?)%/);
      const w = t.match(/(\d[\d,]*) words scanned/);
      if (a) { rec = {name, pct: +a[1], kind: a[2], legend_ai: leg ? +leg[1] : null, words: w ? w[1] : null}; break; }
    }
    window.__pangram.push(rec || {name, error: true});
  }
  window.__pangramDone = true;
})();
'started';
