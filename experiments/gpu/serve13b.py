"""Paragraph server: the 13B LoRA writer on the Windows GPU, for loops that run on the Mac (B18 on).

Loads OLMo-2-13B (4-bit NF4) with one PEFT adapter and answers POST /continue with n sampled
continuations of a prompt, each stopped at the first newline (one paragraph), with the Guard
(guard.py, copied next to this file) and the Mac's sampling: temperature 0.8, top_p 0.95,
repetition penalty 1.05. Listens on 127.0.0.1 only; the Mac reaches it through an SSH tunnel.
Exits on POST /shutdown, after --idle minutes without a request, or after --hours, so the GPU
lock (gpu_job.cmd) is always released.

Usage: python serve13b.py --adapter out_pool/lora-13b-v1 --common common.json [--port 8765]
Request: {"prompt": str, "allowed_text": str, "n": 4, "max_new_tokens": 300, "seed": 0}
Reply: {"texts": [str], "eos": [bool], "new_tokens": [int], "secs": float}
"""

import argparse
import hashlib
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import torch

from guard import QUOTES, Guard, TorchGuard, allowed_specifics

MODEL = "allenai/OLMo-2-1124-13B"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--common", required=True)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--idle", type=float, default=20)
    ap.add_argument("--hours", type=float, default=1.9)
    a = ap.parse_args()
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, LogitsProcessorList

    tok = AutoTokenizer.from_pretrained(MODEL)
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, device_map={"": 0}, attn_implementation="sdpa", dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
    model = PeftModel.from_pretrained(base, a.adapter).eval()
    common = set(json.load(open(a.common, encoding="utf-8")))
    guards, last = {}, [time.time()]
    start = time.time()

    def guard_for(allowed_text: str) -> Guard:
        key = hashlib.sha1(allowed_text.encode()).hexdigest()
        if key not in guards:
            guards[key] = Guard(tok, allowed_specifics(allowed_text), common,
                                allow_quotes=any(q in allowed_text for q in QUOTES))
        return guards[key]

    def continue_(req: dict) -> dict:
        t0 = time.time()
        n = int(req.get("n", 4))
        ids = tok(req["prompt"], return_tensors="pt").input_ids.to("cuda").repeat(n, 1)
        procs = LogitsProcessorList([TorchGuard(guard_for(req["allowed_text"]))])
        torch.manual_seed(int(req.get("seed", 0)))
        with torch.no_grad():
            out = model.generate(ids, attention_mask=torch.ones_like(ids), do_sample=True, temperature=0.8, top_p=0.95,
                                 repetition_penalty=1.05, max_new_tokens=int(req.get("max_new_tokens", 300)),
                                 logits_processor=procs, stop_strings=["\n"], tokenizer=tok,
                                 eos_token_id=tok.eos_token_id, pad_token_id=tok.eos_token_id)[:, ids.shape[1]:]
        texts, eos, lens = [], [], []
        for row in out.tolist():
            cut = row.index(tok.eos_token_id) if tok.eos_token_id in row else len(row)
            text = tok.decode(row[:cut], skip_special_tokens=True)
            para = text.split("\n")[0]
            texts.append(para.strip())
            eos.append(cut < len(row) and "\n" not in text)  # the model ended the article in this paragraph
            lens.append(cut)
        return {"texts": texts, "eos": eos, "new_tokens": lens, "secs": round(time.time() - t0, 2)}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            last[0] = time.time()
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
            if self.path == "/shutdown":
                self._send({"ok": True})
                threading.Thread(target=server.shutdown).start()
                return
            try:
                self._send(continue_(body))
            except Exception as e:  # noqa: BLE001  report to the client, keep serving
                self._send({"error": repr(e)}, 500)

        def _send(self, obj, code=200):
            data = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            print(time.strftime("%H:%M:%S"), fmt % args, flush=True)

    def watchdog():
        while True:
            time.sleep(30)
            if time.time() - last[0] > a.idle * 60 or time.time() - start > a.hours * 3600:
                print("watchdog: stopping", flush=True)
                os._exit(0)

    server = HTTPServer(("127.0.0.1", a.port), Handler)
    threading.Thread(target=watchdog, daemon=True).start()
    print("SERVING", a.adapter, flush=True)
    server.serve_forever()
    print("STOPPED", flush=True)


if __name__ == "__main__":
    main()
