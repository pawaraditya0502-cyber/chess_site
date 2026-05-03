"""
ChessMaster — Online Multiplayer + Stockfish AI + Review
=========================================================
pip install flask
python chess_app.py
Open: http://localhost:5000

Online: Two players open the same URL → click FIND MATCH → auto-paired instantly.
        No codes, no links, pure random matchmaking via HTTP long-polling.
AI:     Play vs Stockfish WASM at all 20 levels (400–3200 Elo) in the browser.
Review: Paste any PGN → full Stockfish analysis, eval bar, accuracy %, blunders.
"""

from flask import Flask, request, jsonify, render_template_string
import threading, uuid, time, random

app = Flask(__name__)

# ── Global state ──────────────────────────────────────────────────────────────
_lock          = threading.Lock()
_waiting       = None          # {"pid": str, "evt": DataEvent, "ts": float}
_games         = {}            # game_id → GameState

class DataEvent:
    def __init__(self):
        self._e = threading.Event()
        self._d = None
    def resolve(self, data):
        self._d = data
        self._e.set()
    def wait(self, timeout=28):
        self._e.wait(timeout)
        return self._d

class GameState:
    def __init__(self, gid, wp, bp):
        self.gid      = gid
        self.white    = wp
        self.black    = bp
        self.moves    = []          # list of SAN
        self.fen      = "start"
        self.status   = "active"
        self.result   = None
        self.ts       = time.time()
        self._lock    = threading.Lock()
        self._queues  = {wp: [], bp: []}

    def push(self, pid, ev):
        with self._lock:
            if pid in self._queues:
                self._queues[pid].append(ev)

    def push_both(self, ev):
        with self._lock:
            for q in self._queues.values():
                q.append(ev)

    def drain(self, pid, timeout=22):
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                q = self._queues.get(pid, [])
                if q:
                    self._queues[pid] = []
                    return q
            time.sleep(0.12)
        return []

def _reap():
    while True:
        time.sleep(120)
        cutoff = time.time() - 3600
        with _lock:
            dead = [g for g, s in _games.items() if s.ts < cutoff]
            for g in dead:
                del _games[g]

threading.Thread(target=_reap, daemon=True).start()

# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/queue", methods=["POST"])
def api_queue():
    global _waiting
    pid = (request.json or {}).get("pid") or str(uuid.uuid4())
    with _lock:
        if _waiting and _waiting["pid"] != pid:
            opp   = _waiting
            _waiting = None
            flip  = random.random() < 0.5
            wp    = pid if flip else opp["pid"]
            bp    = opp["pid"] if flip else pid
            gid   = uuid.uuid4().hex[:10]
            gs    = GameState(gid, wp, bp)
            _games[gid] = gs
            my_color  = "w" if wp == pid else "b"
            opp_color = "b" if my_color == "w" else "w"
            opp["evt"].resolve({"status": "matched", "gid": gid,
                                "color": opp_color, "pid": opp["pid"]})
            return jsonify({"status": "matched", "gid": gid,
                            "color": my_color, "pid": pid})
        else:
            ev = DataEvent()
            _waiting = {"pid": pid, "evt": ev, "ts": time.time()}

    result = ev.wait(28)
    with _lock:
        if _waiting and _waiting["pid"] == pid:
            _waiting = None
    if result:
        return jsonify(result)
    return jsonify({"status": "waiting", "pid": pid})


@app.route("/api/move", methods=["POST"])
def api_move():
    d   = request.json or {}
    gid = d.get("gid"); pid = d.get("pid")
    with _lock:
        gs = _games.get(gid)
    if not gs:
        return jsonify({"ok": False, "error": "not found"})
    opp = gs.black if gs.white == pid else gs.white
    with gs._lock:
        gs.moves.append(d.get("san","?"))
        gs.fen    = d.get("fen", gs.fen)
        gs.status = d.get("status", "active")
        gs.result = d.get("result")
        gs.ts     = time.time()
        gs._queues[opp].append({
            "type": "move",
            "uci": d.get("uci",""),
            "san": d.get("san","?"),
            "fen": gs.fen,
            "status": gs.status,
            "result": gs.result,
        })
    return jsonify({"ok": True})


@app.route("/api/poll", methods=["POST"])
def api_poll():
    d   = request.json or {}
    gid = d.get("gid"); pid = d.get("pid")
    with _lock:
        gs = _games.get(gid)
    if not gs:
        return jsonify({"events": [{"type": "abandoned"}]})
    evs = gs.drain(pid, timeout=22)
    return jsonify({"events": evs})


@app.route("/api/action", methods=["POST"])
def api_action():
    d   = request.json or {}
    gid = d.get("gid"); pid = d.get("pid")
    act = d.get("action")
    with _lock:
        gs = _games.get(gid)
    if not gs:
        return jsonify({"ok": False})
    opp = gs.black if gs.white == pid else gs.white
    my_color = "w" if gs.white == pid else "b"
    if act == "resign":
        winner = "Black" if my_color == "w" else "White"
        gs.push_both({"type": "resign",
                      "result": winner + " wins by resignation"})
    elif act == "draw_offer":
        gs.push(opp, {"type": "draw_offer"})
    elif act == "draw_accept":
        gs.push_both({"type": "draw", "result": "½ – ½  Draw by agreement"})
    elif act == "draw_decline":
        gs.push(opp, {"type": "draw_declined"})
    elif act == "chat":
        gs.push(opp, {"type": "chat", "msg": d.get("msg","")[:120]})
    return jsonify({"ok": True})


@app.route("/")
def index():
    return render_template_string(_HTML)


# ── HTML ──────────────────────────────────────────────────────────────────────
_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ChessMaster</title>

<link rel="stylesheet"
 href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/stockfish.wasm@0.10.0/stockfish.js"></script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;900&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Design: Dark luxury chess club. Deep walnut + ivory + amber gold.
      Cinzel for headers (classical engraved feel), Crimson Pro for body,
      JetBrains Mono for data / moves. ── */

:root {
  --ink:    #0e0b07;
  --felt:   #121009;
  --table:  #1a1510;
  --rail:   #221d16;
  --rim:    #2e2720;
  --wire:   #3d3529;
  --dim:    #6b5e4a;
  --mid:    #9c8b74;
  --ivory:  #e8dfc8;
  --cream:  #f5efe0;
  --gold:   #c8922a;
  --amber:  #e8a830;
  --shine:  #f0c060;
  --sage:   #5a7a5a;
  --rose:   #9a4040;
  --sky:    #4a7090;
  --r: 4px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%; overflow: hidden;
  background: var(--felt);
  color: var(--ivory);
  font-family: 'Crimson Pro', serif;
  font-size: 15px;
}

/* ── Shell ── */
.app { display: flex; height: 100vh; }

/* ── Sidebar ── */
.side {
  width: 56px; flex-shrink: 0;
  background: var(--ink);
  border-right: 1px solid var(--rim);
  display: flex; flex-direction: column;
  align-items: center; padding: 16px 0; gap: 4px;
}
.wordmark {
  font-family: 'Cinzel', serif; font-weight: 900;
  font-size: .75rem; color: var(--gold);
  letter-spacing: 3px; margin-bottom: 18px;
  writing-mode: vertical-rl; transform: rotate(180deg);
  text-shadow: 0 0 18px rgba(200,146,42,.35);
}
.nav {
  width: 40px; height: 40px; border-radius: var(--r);
  background: transparent; border: 1px solid transparent;
  color: var(--dim); font-size: 1.15rem;
  cursor: pointer; display: flex; align-items: center;
  justify-content: center; transition: all .18s; position: relative;
}
.nav:hover { background: var(--rail); color: var(--ivory); border-color: var(--wire); }
.nav.on { background: rgba(200,146,42,.12); color: var(--amber);
           border-color: rgba(200,146,42,.35);
           box-shadow: 0 0 10px rgba(200,146,42,.1); }
.nav .tooltip {
  position: absolute; left: 52px; top: 50%; transform: translateY(-50%);
  background: var(--rail); border: 1px solid var(--wire);
  color: var(--ivory); font-family: 'JetBrains Mono', monospace;
  font-size: .65rem; padding: 3px 9px; border-radius: 3px;
  white-space: nowrap; pointer-events: none;
  opacity: 0; transition: opacity .15s; z-index: 99;
}
.nav:hover .tooltip { opacity: 1; }

/* ── Main ── */
.main { flex: 1; overflow-y: auto; padding: 22px 24px; }

/* ── Pages ── */
.page { display: none; }
.page.on { display: block; }

/* ── Two-column board layout ── */
.blayout {
  display: grid;
  grid-template-columns: 460px 1fr;
  gap: 18px;
  align-items: start;
}

/* ── Board shell ── */
.bshell {
  background: var(--table);
  border: 1px solid var(--wire);
  border-radius: var(--r);
  padding: 14px;
  position: relative;
}
#board    { width: 432px; }
#aiboard  { width: 432px; }
#rvboard  { width: 400px; }

/* ── Cards ── */
.col { display: flex; flex-direction: column; gap: 10px; }
.card {
  background: var(--table);
  border: 1px solid var(--wire);
  border-radius: var(--r);
  padding: 14px;
}
.card-title {
  font-family: 'Cinzel', serif; font-size: .72rem;
  font-weight: 600; letter-spacing: 3px; text-transform: uppercase;
  color: var(--gold); margin-bottom: 11px; padding-bottom: 9px;
  border-bottom: 1px solid var(--rim);
}

/* ── Status bar ── */
.sbar {
  font-family: 'JetBrains Mono', monospace; font-size: .7rem;
  padding: 7px 11px; border-radius: 3px; margin-bottom: 11px;
  background: rgba(90,122,90,.07); border: 1px solid rgba(90,122,90,.2);
  color: var(--sage); min-height: 30px; line-height: 1.5;
}
.sbar.amber { background: rgba(200,146,42,.07); border-color: rgba(200,146,42,.25); color: var(--amber); }
.sbar.rose  { background: rgba(154,64,64,.07);  border-color: rgba(154,64,64,.25);  color: var(--rose);  }
.sbar.sky   { background: rgba(74,112,144,.07); border-color: rgba(74,112,144,.25); color: var(--sky);   }

/* ── Buttons ── */
.brow { display: flex; gap: 7px; flex-wrap: wrap; }
.btn {
  padding: 7px 14px; border-radius: var(--r); border: 1px solid;
  font-family: 'Cinzel', serif; font-size: .65rem; font-weight: 600;
  letter-spacing: 1.5px; text-transform: uppercase;
  cursor: pointer; transition: all .15s;
}
.btn:disabled { opacity: .3; cursor: not-allowed; }
.b-gold  { background: rgba(200,146,42,.12); color: var(--amber); border-color: rgba(200,146,42,.3); }
.b-gold:hover:not(:disabled)  { background: rgba(200,146,42,.22); }
.b-ghost { background: var(--rim); color: var(--ivory); border-color: var(--wire); }
.b-ghost:hover:not(:disabled) { background: var(--wire); }
.b-rose  { background: rgba(154,64,64,.12); color: var(--rose); border-color: rgba(154,64,64,.3); }
.b-rose:hover:not(:disabled)  { background: rgba(154,64,64,.22); }
.b-sage  { background: rgba(90,122,90,.12); color: var(--sage); border-color: rgba(90,122,90,.3); }
.b-sage:hover:not(:disabled)  { background: rgba(90,122,90,.22); }
.b-sky   { background: rgba(74,112,144,.12); color: var(--sky);  border-color: rgba(74,112,144,.3); }
.b-sky:hover:not(:disabled)   { background: rgba(74,112,144,.22); }
.b-sm { padding: 5px 10px; font-size: .6rem; }

/* ══════════════ ONLINE – LOBBY ══════════════ */
.lobby {
  display: flex; flex-direction: column; align-items: center;
  gap: 18px; padding: 28px 16px; text-align: center;
}
.lobby-crown {
  font-size: 2.8rem;
  filter: drop-shadow(0 0 18px rgba(200,146,42,.4));
  animation: float 3s ease-in-out infinite;
}
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
.lobby-title {
  font-family: 'Cinzel', serif; font-size: 1.5rem; font-weight: 900;
  color: var(--cream); letter-spacing: 4px;
  text-shadow: 0 0 30px rgba(200,146,42,.3);
}
.lobby-sub {
  color: var(--dim); font-size: .88rem; line-height: 1.7;
  max-width: 300px; font-style: italic;
}
.find-btn {
  padding: 13px 36px; border-radius: var(--r);
  background: linear-gradient(135deg, var(--gold), var(--amber));
  color: var(--ink); border: none;
  font-family: 'Cinzel', serif; font-size: .85rem; font-weight: 900;
  letter-spacing: 3px; cursor: pointer; transition: all .2s;
  box-shadow: 0 4px 24px rgba(200,146,42,.25);
}
.find-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 32px rgba(200,146,42,.38); }
.find-btn:disabled { opacity: .45; cursor: not-allowed; transform: none; }
.searching {
  display: none; align-items: center; gap: 10px;
  font-family: 'JetBrains Mono', monospace; font-size: .72rem; color: var(--amber);
}
.searching.on { display: flex; }
.pulse-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--amber);
  animation: pdot 1.1s ease-in-out infinite;
}
@keyframes pdot { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.7);opacity:.4} }

/* ══════════════ ONLINE – IN GAME ══════════════ */
.in-game { display: none; }
.in-game.on { display: block; }

/* Player strips */
.pstrip {
  display: flex; align-items: center; gap: 9px;
  padding: 7px 11px; border-radius: 3px; margin-bottom: 7px;
  background: var(--rail); border: 1px solid var(--wire);
  transition: border-color .2s, background .2s;
}
.pstrip.active { border-color: rgba(200,146,42,.4); background: rgba(200,146,42,.04); }
.pstrip .icon { font-size: 1.2rem; }
.pstrip .name { font-family: 'Cinzel', serif; font-size: .78rem; font-weight: 600; }
.pstrip .tag  { font-size: .6rem; color: var(--dim); font-family: 'JetBrains Mono', monospace; }
.pstrip .clock {
  margin-left: auto; font-family: 'JetBrains Mono', monospace;
  font-size: .95rem; font-weight: 600; color: var(--ivory);
  min-width: 46px; text-align: right;
}
.pstrip .clock.low { color: var(--rose); animation: blink .6s ease infinite alternate; }
@keyframes blink { from{opacity:1} to{opacity:.4} }

/* Result overlay */
.result-ov {
  display: none; position: absolute; inset: 0;
  border-radius: var(--r);
  background: rgba(14,11,7,.88); backdrop-filter: blur(3px);
  z-index: 30; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
}
.result-ov.on { display: flex; }
.result-ov .r-title {
  font-family: 'Cinzel', serif; font-size: 1.6rem; font-weight: 900;
  letter-spacing: 4px; color: var(--cream); text-align: center;
}
.result-ov .r-sub { font-size: .8rem; color: var(--dim); font-family: 'JetBrains Mono', monospace; }

/* Draw toast */
.draw-toast {
  display: none; position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%); z-index: 40;
  background: var(--rail); border: 1px solid var(--gold);
  border-radius: 6px; padding: 16px 20px; text-align: center;
  min-width: 210px; box-shadow: 0 8px 40px rgba(0,0,0,.5);
}
.draw-toast.on { display: block; }
.draw-toast h4 {
  font-family: 'Cinzel', serif; color: var(--gold);
  letter-spacing: 2px; margin-bottom: 10px; font-size: .85rem;
}

/* Chat */
.chatbox {
  max-height: 90px; overflow-y: auto;
  border: 1px solid var(--wire); border-radius: 3px;
  padding: 6px 8px; background: var(--rail); margin-bottom: 6px;
}
.chatbox .cm {
  font-family: 'JetBrains Mono', monospace; font-size: .65rem; line-height: 1.9;
}
.cm.me  { color: var(--amber); }
.cm.opp { color: var(--ivory); }
.cm.sys { color: var(--dim); font-style: italic; }
.chat-row { display: flex; gap: 6px; }
.chat-row input { flex: 1; }

/* ══════════════ LEVEL SLIDER ══════════════ */
.lv-wrap  { display: flex; flex-direction: column; gap: 8px; }
.lv-top   { display: flex; align-items: center; gap: 14px; }
.lv-big   {
  font-family: 'Cinzel', serif; font-size: 2.2rem; font-weight: 900;
  color: var(--amber); line-height: 1;
  text-shadow: 0 0 12px rgba(232,168,48,.3);
}
.lv-name  { font-size: .8rem; color: var(--ivory); font-weight: 600; }
.lv-elo   { font-size: .68rem; color: var(--dim); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
.lv-track {
  position: relative; height: 5px;
  background: var(--wire); border-radius: 3px; cursor: pointer; margin: 3px 0;
}
.lv-fill  {
  position: absolute; left: 0; top: 0; height: 100%;
  background: linear-gradient(90deg,var(--sage),var(--amber),var(--rose));
  border-radius: 3px; pointer-events: none; transition: width .1s;
}
.lv-thumb {
  position: absolute; top: 50%; transform: translate(-50%,-50%);
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--amber); border: 2px solid var(--felt);
  cursor: grab; box-shadow: 0 0 8px rgba(232,168,48,.3);
}
.lv-labs {
  display: flex; justify-content: space-between;
  font-size: .6rem; color: var(--dim); font-family: 'JetBrains Mono', monospace;
}

/* Color picker */
.cpick { display: flex; gap: 8px; }
.copt {
  flex: 1; padding: 7px; border-radius: var(--r);
  border: 1px solid var(--wire); background: var(--rail);
  color: var(--dim); font-size: .68rem; font-weight: 600;
  cursor: pointer; text-align: center; transition: all .14s;
  font-family: 'Cinzel', serif; letter-spacing: 1.5px;
}
.copt:hover { border-color: var(--amber); color: var(--ivory); }
.copt.on { background: rgba(200,146,42,.12); color: var(--amber); border-color: rgba(200,146,42,.4); }

/* Engine bar */
.ebar {
  display: flex; align-items: center; gap: 8px;
  font-family: 'JetBrains Mono', monospace; font-size: .68rem;
  padding: 7px 10px; border-radius: 3px;
  background: rgba(74,112,144,.07); border: 1px solid rgba(74,112,144,.18);
  color: var(--sky); min-height: 30px;
}
.spin {
  width: 10px; height: 10px; border-radius: 50%;
  border: 2px solid rgba(74,112,144,.2); border-top-color: var(--sky);
  animation: sp .65s linear infinite; flex-shrink: 0;
}
@keyframes sp { to { transform: rotate(360deg); } }

/* Move list */
.mlist {
  font-family: 'JetBrains Mono', monospace; font-size: .7rem;
  max-height: 190px; overflow-y: auto;
  line-height: 1.95; color: var(--mid);
}
.mp { display: flex; gap: 5px; }
.mn { color: var(--gold); min-width: 22px; }
.mv { padding: 1px 4px; border-radius: 2px; cursor: pointer; color: var(--ivory); transition: background .1s; }
.mv:hover { background: var(--wire); }
.mv.on { background: var(--gold); color: var(--ink); }

/* Inputs */
input[type=text], textarea, select {
  width: 100%; padding: 6px 9px;
  background: var(--rail); color: var(--ivory);
  border: 1px solid var(--wire); border-radius: var(--r);
  font-family: 'JetBrains Mono', monospace; font-size: .7rem;
  outline: none; transition: border .15s;
}
input:focus, textarea:focus, select:focus { border-color: var(--gold); }
textarea { height: 72px; resize: vertical; }
select { cursor: pointer; }

/* ══════════════ REVIEW ══════════════ */
.rev-area { display: flex; gap: 0; }
.eval-col {
  display: flex; flex-direction: column; align-items: center;
  width: 18px; flex-shrink: 0; margin-right: 8px;
}
.eval-outer {
  flex: 1; width: 100%; background: var(--wire);
  border-radius: 3px; overflow: hidden; position: relative;
}
.eval-w {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: var(--cream); transition: height .3s ease;
}
.eval-score {
  font-family: 'JetBrains Mono', monospace; font-size: .65rem; font-weight: 600;
  padding: 3px 4px; background: var(--rail); border: 1px solid var(--wire);
  border-radius: 3px; margin-top: 3px; color: var(--ivory); white-space: nowrap;
}

.prog-wrap { margin-top: 9px; }
.prog-track { height: 3px; background: var(--wire); border-radius: 2px; overflow: hidden; }
.prog-fill  { height: 100%; background: var(--sky); border-radius: 2px; transition: width .15s; width: 0; }
.prog-lbl   { font-size: .63rem; color: var(--dim); font-family: 'JetBrains Mono', monospace; margin-top: 3px; }

.acc-row { display: flex; gap: 7px; margin-top: 8px; }
.acc-box {
  flex: 1; text-align: center; padding: 8px 4px;
  border-radius: 3px; border: 1px solid var(--wire); background: var(--rail);
}
.acc-num { font-family: 'Cinzel', serif; font-size: 1.6rem; font-weight: 900; color: var(--amber); }
.acc-lbl { font-size: .6rem; color: var(--dim); margin-top: 1px; }

.err-row { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 6px; }
.ep {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 8px; border-radius: 12px;
  font-family: 'JetBrains Mono', monospace; font-size: .63rem;
}
.ep-b { background: rgba(154,64,64,.1); border:1px solid rgba(154,64,64,.25); color:var(--rose); }
.ep-m { background: rgba(200,120,40,.1); border:1px solid rgba(200,120,40,.25); color:#d0824a; }
.ep-i { background: rgba(200,146,42,.1); border:1px solid rgba(200,146,42,.25); color:var(--gold); }

.rmlist { font-family: 'JetBrains Mono', monospace; font-size: .7rem; max-height: 230px; overflow-y: auto; line-height: 2.1; }
.rm { display: inline-block; padding: 1px 5px; border-radius: 2px; cursor: pointer; transition: background .1s; }
.rm:hover { background: var(--wire); }
.rm.on { background: var(--gold); color: var(--ink); }
.rn { color: var(--gold); margin-right: 2px; }
.ann {
  display: inline-block; width: 13px; height: 13px;
  border-radius: 50%; font-size: .56rem; text-align: center;
  line-height: 13px; margin-left: 2px; font-weight: 700; vertical-align: middle;
}
.a-bl { background: var(--rose); color: #fff; }
.a-ms { background: #c87830; color: #fff; }
.a-in { background: var(--gold); color: var(--ink); }
.a-gd { background: var(--sky); color: #fff; }

/* ══════════════ PROMOTION MODAL ══════════════ */
.overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.85); z-index: 200; align-items: center; justify-content: center; }
.overlay.on { display: flex; }
.modal { background: var(--rail); border: 1px solid var(--gold); border-radius: 6px; padding: 22px; text-align: center; box-shadow: 0 8px 40px rgba(0,0,0,.5); }
.modal h3 { font-family: 'Cinzel', serif; font-size: .9rem; letter-spacing: 3px; color: var(--amber); margin-bottom: 14px; }
.prow { display: flex; gap: 10px; justify-content: center; }
.pbtn { font-size: 2rem; cursor: pointer; padding: 8px 12px; border: 1px solid var(--wire); background: var(--table); border-radius: 4px; transition: all .14s; }
.pbtn:hover { border-color: var(--gold); transform: scale(1.08); }

/* ══════════════ HIGHLIGHTS ══════════════ */
.hl-f { box-shadow: inset 0 0 0 3px rgba(200,146,42,.7) !important; }
.hl-t { box-shadow: inset 0 0 0 3px rgba(232,168,48,.95) !important; }

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: var(--felt); }
::-webkit-scrollbar-thumb { background: var(--wire); border-radius: 2px; }
</style>
</head>
<body>
<div class="app">

<!-- ── Sidebar ── -->
<nav class="side">
  <div class="wordmark">CMP</div>
  <button class="nav on" id="nb-online" onclick="goPage('online')">🌐<span class="tooltip">Online — Find Match</span></button>
  <button class="nav"    id="nb-ai"     onclick="goPage('ai')"    >🤖<span class="tooltip">vs Stockfish AI</span></button>
  <button class="nav"    id="nb-review" onclick="goPage('review')">🔍<span class="tooltip">Review &amp; Analyse</span></button>
</nav>

<div class="main">

<!-- ═══════════════════════ ONLINE PAGE ═══════════════════════ -->
<div class="page on" id="pg-online">
  <div class="blayout">

    <!-- Board area -->
    <div class="bshell" id="on-shell">
      <div class="sbar sky" id="on-sbar">Click "Find Match" to be paired with a random opponent</div>

      <!-- Opponent strip (top) -->
      <div class="pstrip" id="opp-strip" style="display:none">
        <span class="icon" id="opp-icon">♚</span>
        <div>
          <div class="name" id="opp-name">Opponent</div>
          <div class="tag">ONLINE</div>
        </div>
        <div class="clock" id="opp-clock">10:00</div>
      </div>

      <div id="board"></div>

      <!-- My strip (bottom) -->
      <div class="pstrip" id="my-strip" style="display:none;margin-top:8px">
        <span class="icon" id="my-icon">♔</span>
        <div>
          <div class="name">You</div>
          <div class="tag" id="my-ctag">WHITE</div>
        </div>
        <div class="clock" id="my-clock">10:00</div>
      </div>

      <!-- Draw offer -->
      <div class="draw-toast" id="draw-toast">
        <h4>♟ DRAW OFFERED</h4>
        <p style="font-size:.75rem;color:var(--dim);margin-bottom:12px;font-style:italic">Your opponent offers a draw</p>
        <div class="brow" style="justify-content:center">
          <button class="btn b-sage b-sm" onclick="acceptDraw()">Accept</button>
          <button class="btn b-rose b-sm" onclick="declineDraw()">Decline</button>
        </div>
      </div>

      <!-- Result overlay -->
      <div class="result-ov" id="on-result">
        <div class="r-title" id="on-rtitle">Game Over</div>
        <div class="r-sub"   id="on-rsub"></div>
        <div class="brow" style="margin-top:12px">
          <button class="btn b-gold"  onclick="newOnlineGame()">New Match</button>
          <button class="btn b-ghost" onclick="onlineToReview()">→ Review</button>
        </div>
      </div>
    </div>

    <!-- Side panel -->
    <div class="col">

      <!-- Lobby card -->
      <div class="card" id="lobby-card">
        <div class="card-title">Quick Match</div>
        <div class="lobby">
          <div class="lobby-crown">♛</div>
          <div class="lobby-title">FIND MATCH</div>
          <div class="lobby-sub">
            One click to join the matchmaking pool.
            You'll be randomly paired with another player — no codes, no invites.
          </div>
          <button class="find-btn" id="find-btn" onclick="findMatch()">⚡ FIND OPPONENT</button>
          <div class="searching" id="searching">
            <div class="pulse-dot"></div>
            <span id="search-txt">Searching for opponent…</span>
          </div>
          <div style="font-size:.65rem;color:var(--dim);font-family:'JetBrains Mono',monospace">
            Time control: 10 + 0  ·  Random colour assignment
          </div>
        </div>
      </div>

      <!-- In-game controls -->
      <div class="card in-game" id="on-ctrl">
        <div class="card-title">Controls</div>
        <div class="brow">
          <button class="btn b-ghost b-sm" onclick="offerDraw()">½ Offer Draw</button>
          <button class="btn b-rose  b-sm" onclick="resignOnline()">Resign</button>
          <button class="btn b-ghost b-sm" onclick="newOnlineGame()">New Game</button>
        </div>
      </div>

      <!-- Move history -->
      <div class="card in-game" id="on-hist">
        <div class="card-title">Move History</div>
        <div class="mlist" id="on-mlist"><span style="color:var(--dim)">No moves yet</span></div>
        <div class="brow" style="margin-top:8px">
          <button class="btn b-ghost b-sm" onclick="onlineToReview()">→ Review</button>
          <button class="btn b-ghost b-sm" onclick="cpyOnPgn()">📋 PGN</button>
        </div>
      </div>

      <!-- Chat -->
      <div class="card in-game" id="on-chat">
        <div class="card-title">Chat</div>
        <div class="chatbox" id="chatbox"></div>
        <div class="chat-row">
          <input type="text" id="chat-in" placeholder="Message…" maxlength="100"
            onkeydown="if(event.key==='Enter')sendChat()">
          <button class="btn b-ghost b-sm" onclick="sendChat()">Send</button>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ═══════════════════════ AI PAGE ═══════════════════════ -->
<div class="page" id="pg-ai">
  <div class="blayout">
    <div class="bshell">
      <div class="sbar" id="ai-sbar">Set level &amp; colour, then press Start</div>
      <div id="aiboard"></div>
    </div>
    <div class="col">

      <div class="card">
        <div class="card-title">Stockfish Level</div>
        <div class="lv-wrap">
          <div class="lv-top">
            <div class="lv-big" id="lv-n">8</div>
            <div>
              <div class="lv-name" id="lv-nm">Club Player</div>
              <div class="lv-elo"  id="lv-el">~1200 Elo</div>
            </div>
          </div>
          <div class="lv-track" id="lvt">
            <div class="lv-fill"  id="lvf"></div>
            <div class="lv-thumb" id="lvth"></div>
          </div>
          <div class="lv-labs">
            <span>1–Beginner</span><span>10–Intermediate</span><span>20–Master</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Play As</div>
        <div class="cpick">
          <div class="copt on" id="pw" onclick="pickC('w')">♔ White</div>
          <div class="copt"    id="pb" onclick="pickC('b')">♚ Black</div>
        </div>
        <div class="brow" style="margin-top:10px">
          <button class="btn b-gold"         onclick="startAI()">▶ Start</button>
          <button class="btn b-ghost"         onclick="flipAI()">⇅ Flip</button>
          <button class="btn b-rose b-sm"    id="ai-res" onclick="resignAI()" disabled>Resign</button>
        </div>
      </div>

      <div class="card" id="ai-ec" style="display:none">
        <div class="card-title">Engine</div>
        <div class="ebar" id="ai-eb"><span style="color:var(--dim)">Idle</span></div>
      </div>

      <div class="card">
        <div class="card-title">Move History</div>
        <div class="mlist" id="ai-mlist"><span style="color:var(--dim)">No moves yet</span></div>
        <div class="brow" style="margin-top:8px">
          <button class="btn b-ghost b-sm" onclick="undoAI()">↩ Undo</button>
          <button class="btn b-ghost b-sm" onclick="aiToReview()">→ Review</button>
          <button class="btn b-ghost b-sm" onclick="cpyAIPgn()">📋 PGN</button>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Set Position (FEN)</div>
        <input type="text" id="ai-fen" placeholder="Paste FEN string…">
        <div class="brow" style="margin-top:7px">
          <button class="btn b-gold b-sm" onclick="loadFen()">Load</button>
          <button class="btn b-ghost b-sm" onclick="cpyFen()">Copy</button>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ═══════════════════════ REVIEW PAGE ═══════════════════════ -->
<div class="page" id="pg-review">
  <div class="blayout">
    <div class="bshell">
      <div class="sbar" id="rv-sbar">Load a PGN to begin Stockfish analysis</div>
      <div class="rev-area">
        <div class="eval-col" style="height:420px">
          <div class="eval-outer" id="ev-outer">
            <div class="eval-w" id="ev-bar" style="height:50%"></div>
          </div>
          <div class="eval-score" id="ev-score">—</div>
        </div>
        <div style="width:7px"></div>
        <div id="rvboard"></div>
      </div>
    </div>
    <div class="col">

      <div class="card">
        <div class="card-title">Load Game (PGN)</div>
        <textarea id="pgn-in" placeholder="Paste PGN here…"></textarea>
        <div class="brow" style="margin-top:7px">
          <button class="btn b-gold"      onclick="loadRv()">Load &amp; Analyse</button>
          <button class="btn b-ghost b-sm" onclick="loadSample()">Sample Game</button>
        </div>
        <div id="rv-prog" class="prog-wrap" style="display:none">
          <div class="prog-track"><div class="prog-fill" id="pf"></div></div>
          <div class="prog-lbl"  id="pl">Analysing…</div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Analysis Settings</div>
        <select id="rv-depth">
          <option value="8">Depth 8 — Fast</option>
          <option value="12" selected>Depth 12 — Balanced</option>
          <option value="16">Depth 16 — Deep</option>
          <option value="20">Depth 20 — Maximum</option>
        </select>
      </div>

      <div class="card">
        <div class="card-title">Navigation</div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <button class="btn b-ghost b-sm" onclick="rvGo(0)">⏮</button>
          <button class="btn b-ghost b-sm" onclick="rvPrev()">◀</button>
          <span id="rvctr" style="font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--amber);min-width:52px;text-align:center">0/0</span>
          <button class="btn b-ghost b-sm" onclick="rvNext()">▶</button>
          <button class="btn b-ghost b-sm" onclick="rvLast()">⏭</button>
          <button class="btn b-ghost b-sm" onclick="rvFlip()">⇅</button>
        </div>
      </div>

      <div class="card" id="acc-card" style="display:none">
        <div class="card-title">Accuracy Report</div>
        <div class="acc-row">
          <div class="acc-box"><div class="acc-num" id="acc-w">—</div><div class="acc-lbl">White</div></div>
          <div class="acc-box"><div class="acc-num" id="acc-b">—</div><div class="acc-lbl">Black</div></div>
        </div>
        <div class="err-row" id="erw"></div>
        <div class="err-row" id="erb"></div>
      </div>

      <div class="card">
        <div class="card-title">Move List</div>
        <div class="rmlist" id="rv-mlist"><span style="color:var(--dim)">No game loaded</span></div>
      </div>

    </div>
  </div>
</div>

</div><!-- /main -->
</div><!-- /app -->

<!-- Promotion modal -->
<div class="overlay" id="promo-ov">
  <div class="modal">
    <h3>PROMOTE PAWN</h3>
    <div class="prow">
      <div class="pbtn" onclick="doPromo('q')">♛</div>
      <div class="pbtn" onclick="doPromo('r')">♜</div>
      <div class="pbtn" onclick="doPromo('b')">♝</div>
      <div class="pbtn" onclick="doPromo('n')">♞</div>
    </div>
  </div>
</div>

<script>
/* ═══════════════════════════════════════════════════════════
   NAVIGATION
═══════════════════════════════════════════════════════════ */
function goPage(p) {
  document.querySelectorAll('.page').forEach(e => e.classList.remove('on'));
  document.querySelectorAll('.nav').forEach(e => e.classList.remove('on'));
  document.getElementById('pg-' + p).classList.add('on');
  document.getElementById('nb-' + p).classList.add('on');
  if (p === 'review' && !rvboard) initRvBoard();
}

/* ═══════════════════════════════════════════════════════════
   STOCKFISH ENGINE  (WASM, runs in browser)
═══════════════════════════════════════════════════════════ */
let sf = null, sfOk = false, sfCbs = [], sfLsn = [];

async function initSF() {
  return new Promise(res => {
    try {
      sf = typeof Stockfish !== 'undefined' ? Stockfish() : null;
      if (!sf) { res(false); return; }
      sf.onmessage = e => { let m = typeof e === 'string' ? e : e.data; _disp(m); };
      _sfOnce('uciok',   () => sf.postMessage('isready'));
      _sfOnce('readyok', () => { sfOk = true; res(true); });
      sf.postMessage('uci');
      setTimeout(() => { if (!sfOk) { sfOk = true; res(true); } }, 3500);
    } catch(e) { res(false); }
  });
}
function _disp(m) { sfCbs.forEach(c => { if (m.includes(c.k)) c.f(m); }); [...sfLsn].forEach(f => f(m)); }
function _sfOnce(k, f) { let w; w = m => { if (m.includes(k)) { sfCbs = sfCbs.filter(c => c.f !== w); f(m); } }; sfCbs.push({k, f:w}); }
function sfAdd(f) { sfLsn.push(f); return f; }
function sfRem(f) { sfLsn = sfLsn.filter(x => x !== f); }
function sfPost(c) { if (sf) sf.postMessage(c); }

const LV_DATA = [null,
  {n:'Total Beginner',    e:'~400 Elo',  mt:60},
  {n:'Absolute Beginner', e:'~500 Elo',  mt:100},
  {n:'Beginner',          e:'~600 Elo',  mt:150},
  {n:'Casual',            e:'~700 Elo',  mt:200},
  {n:'Casual+',           e:'~800 Elo',  mt:300},
  {n:'Developing',        e:'~900 Elo',  mt:400},
  {n:'Developing+',       e:'~1000 Elo', mt:550},
  {n:'Club Player',       e:'~1200 Elo', mt:700},
  {n:'Club Player+',      e:'~1400 Elo', mt:900},
  {n:'Intermediate',      e:'~1600 Elo', mt:1100},
  {n:'Intermediate+',     e:'~1800 Elo', mt:1400},
  {n:'Advanced',          e:'~2000 Elo', mt:1800},
  {n:'Advanced+',         e:'~2100 Elo', mt:2200},
  {n:'Expert',            e:'~2200 Elo', mt:2600},
  {n:'Expert+',           e:'~2300 Elo', mt:3000},
  {n:'Master Candidate',  e:'~2400 Elo', mt:3500},
  {n:'National Master',   e:'~2500 Elo', mt:4500},
  {n:'Intl Master',       e:'~2600 Elo', mt:5500},
  {n:'Grandmaster',       e:'~2700 Elo', mt:7000},
  {n:'Super-GM / MAX',    e:'~3200 Elo', mt:10000},
];

function engineMove(fen, lv, cb) {
  if (!sfOk) { cb(null); return; }
  sfPost('ucinewgame');
  sfPost('setoption name Skill Level value ' + lv);
  sfPost('position fen ' + fen);
  let L = sfAdd(m => {
    if (m.startsWith('bestmove')) {
      sfRem(L);
      let p = m.split(' ');
      cb(p[1] && p[1] !== '(none)' ? p[1] : null);
    }
  });
  sfPost('go movetime ' + (LV_DATA[lv]?.mt || 1000));
}

function engineEval(fen, depth, cb) {
  if (!sfOk) { cb(0); return; }
  sfPost('ucinewgame');
  sfPost('setoption name Skill Level value 20');
  sfPost('position fen ' + fen);
  let last = 0;
  let L = sfAdd(m => {
    let cm = m.match(/score cp (-?\d+)/);   if (cm) last = parseInt(cm[1]);
    let mm = m.match(/score mate (-?\d+)/); if (mm) last = parseInt(mm[1]) > 0 ? 32000 : -32000;
    if (m.startsWith('bestmove')) { sfRem(L); cb(last); }
  });
  sfPost('go depth ' + depth);
}

/* ═══════════════════════════════════════════════════════════
   LEVEL SLIDER
═══════════════════════════════════════════════════════════ */
let curLv = 8;
function setLv(v) {
  curLv = Math.max(1, Math.min(20, v));
  let pct = (curLv - 1) / 19 * 100;
  document.getElementById('lv-n').textContent  = curLv;
  document.getElementById('lv-nm').textContent = LV_DATA[curLv].n;
  document.getElementById('lv-el').textContent = LV_DATA[curLv].e;
  document.getElementById('lvf').style.width   = pct + '%';
  document.getElementById('lvth').style.left   = pct + '%';
}
(function() {
  let tr = document.getElementById('lvt'), drag = false;
  function p2l(x) {
    let r = tr.getBoundingClientRect();
    return Math.round(Math.max(0, Math.min(1, (x - r.left) / r.width)) * 19 + 1);
  }
  tr.addEventListener('mousedown',  e => { drag = true; setLv(p2l(e.clientX)); });
  document.addEventListener('mousemove', e => { if (drag) setLv(p2l(e.clientX)); });
  document.addEventListener('mouseup',   () => { drag = false; });
  tr.addEventListener('touchstart', e => { drag = true; setLv(p2l(e.touches[0].clientX)); }, {passive:true});
  document.addEventListener('touchmove', e => { if (drag) setLv(p2l(e.touches[0].clientX)); }, {passive:true});
  document.addEventListener('touchend',  () => { drag = false; });
  setLv(8);
})();

/* ═══════════════════════════════════════════════════════════
   ONLINE MULTIPLAYER
═══════════════════════════════════════════════════════════ */
let onGame = new Chess(), onBoard = null;
let myPid = (localStorage.getItem('cmp_pid') || (() => {
  let p = 'P' + Math.random().toString(36).slice(2, 12);
  localStorage.setItem('cmp_pid', p); return p;
})());
let onGid = null, myColor = null, onActive = false;
let pendingPromoOn = null, pendingPromoAI = null;
let pollRunning = false, drawOffered = false;
let clockW = 600, clockB = 600, clockTimer = null;
let onMoves = [];       // {san, color}
let searchTimer = null;

$(document).ready(function() {
  onBoard = Chessboard('board', {
    draggable: true, position: 'start',
    onDragStart: onDragStart, onDrop: onDrop,
    onSnapEnd: () => onBoard.position(onGame.fen()),
    pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
  initSF().then(ok => {
    if (!ok) setSbar('rv', '⚠  Stockfish not loaded — analysis unavailable', 'rose');
  });
});

/* ── Matchmaking ── */
function findMatch() {
  let btn = document.getElementById('find-btn');
  btn.disabled = true;
  document.getElementById('searching').classList.add('on');
  setSbar('on', 'Searching for an opponent…', 'sky');
  doQueueRequest();
}

function doQueueRequest() {
  fetch('/api/queue', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({pid: myPid})
  })
  .then(r => r.json())
  .then(d => {
    if (d.status === 'matched') {
      beginOnlineGame(d.gid, d.color, d.pid || myPid);
    } else {
      // still waiting — server returned after 28s with no match, retry
      document.getElementById('search-txt').textContent = 'Still searching…';
      doQueueRequest();
    }
  })
  .catch(() => {
    setSbar('on', 'Connection error — retrying…', 'rose');
    setTimeout(doQueueRequest, 2000);
  });
}

function beginOnlineGame(gid, color, pid) {
  onGid = gid; myColor = color; myPid = pid;
  onGame = new Chess(); onActive = true; drawOffered = false; onMoves = [];
  clockW = 600; clockB = 600;

  document.getElementById('find-btn').disabled = false;
  document.getElementById('searching').classList.remove('on');
  document.getElementById('lobby-card').style.display = 'none';
  document.querySelectorAll('.in-game').forEach(e => e.classList.add('on'));

  let isW = color === 'w';
  document.getElementById('opp-strip').style.display = 'flex';
  document.getElementById('my-strip').style.display  = 'flex';
  document.getElementById('opp-icon').textContent = isW ? '♚' : '♔';
  document.getElementById('my-icon').textContent  = isW ? '♔' : '♚';
  document.getElementById('my-ctag').textContent  = isW ? 'WHITE' : 'BLACK';

  onBoard.orientation(color === 'w' ? 'white' : 'black');
  onBoard.position('start');
  clrOnHL();
  document.getElementById('on-result').classList.remove('on');
  document.getElementById('draw-toast').classList.remove('on');
  document.getElementById('on-mlist').innerHTML = '<span style="color:var(--dim)">No moves yet</span>';
  document.getElementById('chatbox').innerHTML = '';

  addChat('sys', 'Game started! You play ' + (color === 'w' ? 'White' : 'Black'));
  setSbar('on', 'Game on — ' + (color === 'w' ? 'White' : 'Black') + ' to move');
  updateStrips();
  startClock();
  startPoll();
}

/* ── Dragging ── */
function onDragStart(src, piece) {
  if (!onActive || onGame.game_over()) return false;
  if (onGame.turn() !== myColor) return false;
  if (myColor === 'w' && /^b/.test(piece)) return false;
  if (myColor === 'b' && /^w/.test(piece)) return false;
}

function onDrop(src, tgt) {
  if (isPromotion(onGame, src, tgt)) {
    pendingPromoOn = {from: src, to: tgt};
    document.getElementById('promo-ov').classList.add('on');
    return 'snapback';
  }
  let mv = onGame.move({from: src, to: tgt, promotion: 'q'});
  if (!mv) return 'snapback';
  afterOnMove(mv);
}

function isPromotion(g, f, t) {
  let p = g.get(f);
  if (!p || p.type !== 'p') return false;
  return (p.color === 'w' && t[1] === '8') || (p.color === 'b' && t[1] === '1');
}

function doPromo(pc) {
  document.getElementById('promo-ov').classList.remove('on');
  if (pendingPromoOn) {
    let mv = onGame.move({from: pendingPromoOn.from, to: pendingPromoOn.to, promotion: pc});
    pendingPromoOn = null;
    if (mv) { onBoard.position(onGame.fen()); afterOnMove(mv); }
  } else if (pendingPromoAI) {
    let mv = aiGame.move({from: pendingPromoAI.from, to: pendingPromoAI.to, promotion: pc});
    pendingPromoAI = null;
    if (mv) { aiBoard.position(aiGame.fen()); afterAIPlayer(mv); }
  }
}

function afterOnMove(mv) {
  onMoves.push({san: mv.san, color: mv.color});
  clrOnHL(); hlOn(mv.from, mv.to);
  updateOnMlist();
  updateStrips();
  let status = 'active', result = null;
  if      (onGame.in_checkmate())          { status = 'checkmate'; result = (onGame.turn()==='b'?'White':'Black') + ' wins by checkmate'; }
  else if (onGame.in_stalemate())          { status = 'draw';      result = '½ – ½  Stalemate'; }
  else if (onGame.in_threefold_repetition()){ status = 'draw';     result = '½ – ½  Threefold repetition'; }
  else if (onGame.insufficient_material()) { status = 'draw';      result = '½ – ½  Insufficient material'; }
  fetch('/api/move', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({gid: onGid, pid: myPid,
      uci: mv.from + mv.to + (mv.promotion || ''),
      san: mv.san, fen: onGame.fen(), status, result})
  });
  if (status !== 'active') endOnGame(result);
  else setSbar('on', 'Waiting for opponent…');
}

/* ── Long-poll ── */
function startPoll() {
  if (pollRunning) return;
  pollRunning = true;
  function poll() {
    if (!onGid) { pollRunning = false; return; }
    fetch('/api/poll', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({gid: onGid, pid: myPid})
    })
    .then(r => r.json())
    .then(d => {
      (d.events || []).forEach(handleEvent);
      if (onGid) setTimeout(poll, 80);
      else pollRunning = false;
    })
    .catch(() => { if (onGid) setTimeout(poll, 2500); else pollRunning = false; });
  }
  poll();
}

function handleEvent(ev) {
  if (ev.type === 'move') {
    onGame = new Chess(ev.fen);
    onBoard.position(ev.fen);
    if (ev.uci && ev.uci.length >= 4) hlOn(ev.uci.slice(0,2), ev.uci.slice(2,4));
    onMoves.push({san: ev.san, color: myColor === 'w' ? 'b' : 'w'});
    updateOnMlist(); updateStrips();
    setSbar('on', 'Your turn');
    if (ev.status === 'checkmate' || ev.status === 'draw') endOnGame(ev.result);
  }
  else if (ev.type === 'resign')       { endOnGame(ev.result); }
  else if (ev.type === 'draw')         { endOnGame(ev.result); }
  else if (ev.type === 'draw_offer')   { document.getElementById('draw-toast').classList.add('on'); }
  else if (ev.type === 'draw_declined'){ setSbar('on', 'Draw declined — game continues'); }
  else if (ev.type === 'abandoned')    { endOnGame('Opponent disconnected'); }
  else if (ev.type === 'chat')         { addChat('opp', ev.msg); }
}

function endOnGame(result) {
  onActive = false;
  stopClock();
  document.getElementById('on-result').classList.add('on');
  document.getElementById('on-rtitle').textContent = result || 'Game Over';
  document.getElementById('on-rsub').textContent   = 'Click "New Match" to play again';
  setSbar('on', result || 'Game over');
}

/* ── Clocks ── */
function startClock() {
  if (clockTimer) clearInterval(clockTimer);
  clockTimer = setInterval(() => {
    if (!onActive) return;
    if (onGame.turn() === 'w') clockW = Math.max(0, clockW - 1);
    else                       clockB = Math.max(0, clockB - 1);
    renderClocks();
    if (clockW === 0 || clockB === 0)
      endOnGame((clockW === 0 ? 'Black' : 'White') + ' wins on time');
  }, 1000);
}
function stopClock() { if (clockTimer) { clearInterval(clockTimer); clockTimer = null; } }
function fmt(s) { return String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0'); }
function renderClocks() {
  let isW = myColor === 'w';
  document.getElementById('my-clock').textContent  = fmt(isW ? clockW : clockB);
  document.getElementById('opp-clock').textContent = fmt(isW ? clockB : clockW);
  document.getElementById('my-clock').classList.toggle('low', (isW ? clockW : clockB) < 30);
}
function updateStrips() {
  let wt = onGame.turn() === 'w', isW = myColor === 'w';
  document.getElementById('my-strip').classList.toggle('active',  (isW && wt) || (!isW && !wt));
  document.getElementById('opp-strip').classList.toggle('active', (isW && !wt) || (!isW && wt));
}

/* ── Online utils ── */
function updateOnMlist() {
  if (!onMoves.length) {
    document.getElementById('on-mlist').innerHTML = '<span style="color:var(--dim)">No moves yet</span>';
    return;
  }
  let s = '';
  for (let i = 0; i < onMoves.length; i += 2) {
    s += '<div class="mp"><span class="mn">' + (Math.floor(i/2)+1) + '.</span>';
    s += '<span class="mv">' + onMoves[i].san + '</span>';
    if (onMoves[i+1]) s += '<span class="mv">' + onMoves[i+1].san + '</span>';
    s += '</div>';
  }
  let el = document.getElementById('on-mlist');
  el.innerHTML = s; el.scrollTop = el.scrollHeight;
}
function newOnlineGame() {
  onActive = false; onGid = null; myColor = null;
  stopClock(); pollRunning = false;
  document.getElementById('lobby-card').style.display = 'block';
  document.querySelectorAll('.in-game').forEach(e => e.classList.remove('on'));
  document.getElementById('opp-strip').style.display = 'none';
  document.getElementById('my-strip').style.display  = 'none';
  document.getElementById('on-result').classList.remove('on');
  document.getElementById('draw-toast').classList.remove('on');
  document.getElementById('find-btn').disabled = false;
  document.getElementById('searching').classList.remove('on');
  document.getElementById('search-txt').textContent = 'Searching for opponent…';
  onBoard.position('start'); clrOnHL();
  setSbar('on', 'Click "Find Match" to be paired with a random opponent');
}
function offerDraw() {
  postAction({action: 'draw_offer'});
  setSbar('on', 'Draw offer sent…', 'sky');
}
function acceptDraw() {
  document.getElementById('draw-toast').classList.remove('on');
  postAction({action: 'draw_accept'});
}
function declineDraw() {
  document.getElementById('draw-toast').classList.remove('on');
  postAction({action: 'draw_decline'});
}
function resignOnline() {
  if (!onActive) return;
  postAction({action: 'resign'});
}
function postAction(extra) {
  fetch('/api/action', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({gid: onGid, pid: myPid, ...extra})
  });
}
function addChat(type, msg) {
  let el = document.getElementById('chatbox');
  let d = document.createElement('div');
  d.className = 'cm ' + type;
  d.textContent = (type === 'me' ? 'You: ' : type === 'opp' ? 'Opp: ' : '') + msg;
  el.appendChild(d); el.scrollTop = el.scrollHeight;
}
function sendChat() {
  let inp = document.getElementById('chat-in');
  let msg = inp.value.trim(); if (!msg) return;
  addChat('me', msg); inp.value = '';
  postAction({action: 'chat', msg});
}
function cpyOnPgn() {
  let g = new Chess();
  onMoves.forEach(m => { try { g.move(m.san); } catch(e){} });
  navigator.clipboard.writeText(g.pgn()).then(() => {
    let b = event.target; b.textContent = '✓'; setTimeout(() => b.textContent = '📋 PGN', 1400);
  });
}
function onlineToReview() {
  let g = new Chess();
  onMoves.forEach(m => { try { g.move(m.san); } catch(e){} });
  let pgn = g.pgn(); if (!pgn) return;
  document.getElementById('pgn-in').value = pgn;
  goPage('review'); loadRv();
}
function hlOn(f, t) {
  clrOnHL();
  document.querySelectorAll('.square-' + f + ',.square-' + t).forEach((e, i) =>
    e.classList.add(i === 0 ? 'hl-f' : 'hl-t'));
}
function clrOnHL() {
  document.querySelectorAll('.hl-f,.hl-t').forEach(e => e.classList.remove('hl-f','hl-t'));
}
function setSbar(pg, msg, cls='') {
  let map = {on:'on-sbar', ai:'ai-sbar', rv:'rv-sbar'};
  let el = document.getElementById(map[pg]);
  if (!el) return;
  el.className = 'sbar' + (cls ? ' ' + cls : '');
  el.textContent = msg;
}

/* ═══════════════════════════════════════════════════════════
   AI GAME
═══════════════════════════════════════════════════════════ */
let aiGame = new Chess(), aiBoard = null;
let aiColor = 'w', aiActive = false, aiThinking = false;

$(document).ready(function() {
  aiBoard = Chessboard('aiboard', {
    draggable: true, position: 'start',
    onDragStart: aiDragStart, onDrop: aiDrop,
    onSnapEnd: () => aiBoard.position(aiGame.fen()),
    pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
});

function pickC(c) {
  aiColor = c;
  document.getElementById('pw').classList.toggle('on', c === 'w');
  document.getElementById('pb').classList.toggle('on', c === 'b');
}
function startAI() {
  aiGame = new Chess(); aiActive = true; aiThinking = false;
  aiBoard.orientation(aiColor === 'w' ? 'white' : 'black');
  aiBoard.position('start');
  clrAIHL();
  document.getElementById('ai-mlist').innerHTML = '<span style="color:var(--dim)">No moves yet</span>';
  document.getElementById('ai-res').disabled = false;
  document.getElementById('ai-ec').style.display = 'block';
  setAIEB('<span style="color:var(--dim)">Ready</span>');
  setSbar('ai', 'You play ' + (aiColor === 'w' ? 'White' : 'Black') +
    ' vs Stockfish Level ' + curLv + ' — ' + LV_DATA[curLv].n);
  if (aiGame.turn() !== aiColor) setTimeout(() => doAIMove(), 400);
}
function aiDragStart(src, piece) {
  if (!aiActive || aiGame.game_over() || aiThinking) return false;
  if (aiGame.turn() !== aiColor) return false;
  if (aiColor === 'w' && /^b/.test(piece)) return false;
  if (aiColor === 'b' && /^w/.test(piece)) return false;
}
function aiDrop(src, tgt) {
  if (isPromotion(aiGame, src, tgt)) {
    pendingPromoAI = {from: src, to: tgt};
    document.getElementById('promo-ov').classList.add('on');
    return 'snapback';
  }
  let mv = aiGame.move({from: src, to: tgt, promotion: 'q'});
  if (!mv) return 'snapback';
  afterAIPlayer(mv);
}
function afterAIPlayer(mv) {
  clrAIHL(); hlAI(mv.from, mv.to);
  updateAIMlist();
  if (checkAIOver()) return;
  setTimeout(() => doAIMove(), 120);
}
function doAIMove() {
  if (!aiActive || aiGame.game_over()) return;
  aiThinking = true;
  setAIEB('<div class="spin"></div><span>Level ' + curLv + ' — ' + LV_DATA[curLv].n + ' thinking…</span>');
  engineMove(aiGame.fen(), curLv, bm => {
    aiThinking = false;
    if (!bm || !aiActive) { setAIEB('<span style="color:var(--dim)">—</span>'); return; }
    let mv = aiGame.move({from: bm.slice(0,2), to: bm.slice(2,4), promotion: bm[4] || 'q'});
    if (!mv) { setAIEB('<span style="color:var(--dim)">—</span>'); return; }
    aiBoard.position(aiGame.fen()); clrAIHL(); hlAI(mv.from, mv.to);
    updateAIMlist();
    setAIEB('<span>Played <b style="color:var(--amber)">' + mv.san + '</b>  ·  Level ' + curLv + '</span>');
    checkAIOver();
  });
}
function setAIEB(h) { document.getElementById('ai-eb').innerHTML = h; }
function checkAIOver() {
  if (!aiGame.game_over()) return false;
  aiActive = false;
  document.getElementById('ai-res').disabled = true;
  let m = aiGame.in_checkmate()            ? '♛ Checkmate! ' + (aiGame.turn()==='b'?'White':'Black') + ' wins.'
        : aiGame.in_stalemate()            ? '½  Stalemate'
        : aiGame.in_threefold_repetition() ? '½  Threefold repetition'
        : aiGame.insufficient_material()   ? '½  Insufficient material'
        : '½  Draw';
  setSbar('ai', m);
  setAIEB('<span style="color:var(--sage)">' + m + '</span>');
  return true;
}
function updateAIMlist() {
  let h = aiGame.history();
  if (!h.length) { document.getElementById('ai-mlist').innerHTML = '<span style="color:var(--dim)">No moves yet</span>'; return; }
  let s = '';
  for (let i = 0; i < h.length; i += 2) {
    s += '<div class="mp"><span class="mn">' + (Math.floor(i/2)+1) + '.</span>';
    s += '<span class="mv">' + h[i] + '</span>';
    if (h[i+1]) s += '<span class="mv">' + h[i+1] + '</span>';
    s += '</div>';
  }
  let el = document.getElementById('ai-mlist');
  el.innerHTML = s; el.scrollTop = el.scrollHeight;
}
function undoAI()   { if (!aiActive) return; aiGame.undo(); aiGame.undo(); aiBoard.position(aiGame.fen()); clrAIHL(); updateAIMlist(); }
function flipAI()   { aiBoard.flip(); }
function resignAI() {
  if (!aiActive) return; aiActive = false;
  document.getElementById('ai-res').disabled = true;
  setSbar('ai', 'You resigned.'); setAIEB('<span style="color:var(--rose)">Resigned.</span>');
}
function loadFen() {
  let f = document.getElementById('ai-fen').value.trim(); if (!f) return;
  let t = new Chess(); if (!t.load(f)) { alert('Invalid FEN!'); return; }
  aiGame = t; aiActive = false; aiBoard.position(f); clrAIHL(); updateAIMlist();
  setSbar('ai', 'Position loaded — press ▶ Start.');
}
function cpyFen() {
  navigator.clipboard.writeText(aiGame.fen()).then(() => {
    let b = event.target; b.textContent = '✓'; setTimeout(() => b.textContent = 'Copy', 1400);
  });
}
function cpyAIPgn() {
  navigator.clipboard.writeText(aiGame.pgn()).then(() => {
    let b = event.target; b.textContent = '✓'; setTimeout(() => b.textContent = '📋 PGN', 1400);
  });
}
function aiToReview() {
  let pgn = aiGame.pgn(); if (!pgn) return;
  document.getElementById('pgn-in').value = pgn;
  goPage('review'); loadRv();
}
function hlAI(f, t) {
  clrAIHL();
  document.querySelectorAll('.square-' + f + ',.square-' + t).forEach((e,i) =>
    e.classList.add(i===0?'hl-f':'hl-t'));
}
function clrAIHL() { document.querySelectorAll('.hl-f,.hl-t').forEach(e => e.classList.remove('hl-f','hl-t')); }

/* ═══════════════════════════════════════════════════════════
   REVIEW  +  STOCKFISH ANALYSIS
═══════════════════════════════════════════════════════════ */
let rvboard = null, rvSt = [], rvEv = [], rvIdx = 0, rvAna = false;

function initRvBoard() {
  rvboard = Chessboard('rvboard', {
    draggable: false, position: 'start',
    pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
}
function rvFlip() { if (rvboard) rvboard.flip(); }

function loadSample() {
  document.getElementById('pgn-in').value =
`[Event "The Immortal Game"][White "Adolf Anderssen"][Black "Lionel Kieseritzky"][Result "1-0"]

1. e4 e5 2. f4 exf4 3. Bc4 Qh4+ 4. Kf1 b5 5. Bxb5 Nf6 6. Nf3 Qh6 7. d3 Nh5
8. Nh4 Qg5 9. Nf5 c6 10. g4 Nf6 11. Rg1 cxb5 12. h4 Qg6 13. h5 Qg5 14. Qf3 Ng8
15. Bxf4 Qf6 16. Nc3 Bc5 17. Nd5 Qxb2 18. Bd6 Bxg1 19. e5 Qxa1+ 20. Ke2 Na6
21. Nxg7+ Kd8 22. Qf6+ Nxf6 23. Be7# 1-0`;
  loadRv();
}

function loadRv() {
  let pgn = document.getElementById('pgn-in').value.trim();
  if (!pgn) return;
  let tmp = new Chess();
  if (!tmp.load_pgn(pgn)) { alert('Invalid PGN!'); return; }
  let hist = tmp.history({verbose: true}), g2 = new Chess();
  rvSt = [{fen: g2.fen(), san: null, color: null, moveNum: 0, ann: null}];
  hist.forEach((m, i) => {
    g2.move(m.san);
    rvSt.push({fen: g2.fen(), san: m.san, color: m.color, moveNum: Math.floor(i/2)+1, ann: null});
  });
  rvEv = new Array(rvSt.length).fill(null);
  document.getElementById('acc-card').style.display = 'none';
  rvGo(0); renderRvMoves(); runAnalysis();
}

function runAnalysis() {
  if (rvAna) return;
  rvAna = true;
  let depth = parseInt(document.getElementById('rv-depth').value);
  let tot = rvSt.length;
  let pw = document.getElementById('rv-prog');
  let pf = document.getElementById('pf'), pl = document.getElementById('pl');
  pw.style.display = 'block';
  let i = 0;
  function step() {
    if (i >= tot) {
      rvAna = false; pw.style.display = 'none';
      computeAccuracy(); renderRvMoves(); updateEvBar(); return;
    }
    pl.textContent = 'Analysing move ' + i + ' / ' + (tot - 1) + '…';
    pf.style.width = (i / (tot - 1) * 100) + '%';
    engineEval(rvSt[i].fen, depth, score => {
      let g = new Chess(rvSt[i].fen);
      rvEv[i] = g.turn() === 'w' ? score : -score;   // normalise to white POV
      if (i === rvIdx) updateEvBar();
      i++; step();
    });
  }
  step();
}

function cpToWinPct(cp) { return 1 / (1 + Math.exp(-0.004 * cp)); }

function computeAccuracy() {
  let wA = [], bA = [], wB=0, wM=0, wI=0, bB=0, bM=0, bI=0;
  for (let i = 1; i < rvSt.length; i++) {
    let before = rvEv[i-1], after = rvEv[i];
    if (before === null || after === null) continue;
    let col = rvSt[i].color;
    let wpB = col === 'w' ? cpToWinPct(before) : cpToWinPct(-before);
    let wpA = col === 'w' ? cpToWinPct(after)  : cpToWinPct(-after);
    let loss = Math.max(0, wpB - wpA);
    let acc  = Math.max(0, 100 - 150 * loss);
    let ann  = loss > 0.20 ? 'blunder' : loss > 0.10 ? 'mistake' : loss > 0.05 ? 'inaccuracy' : loss > 0.02 ? 'good' : 'best';
    rvSt[i].ann = ann; rvSt[i].acc = acc;
    if (col === 'w') { wA.push(acc); if(ann==='blunder')wB++; else if(ann==='mistake')wM++; else if(ann==='inaccuracy')wI++; }
    else             { bA.push(acc); if(ann==='blunder')bB++; else if(ann==='mistake')bM++; else if(ann==='inaccuracy')bI++; }
  }
  let avgW = wA.length ? Math.round(wA.reduce((a,b)=>a+b,0)/wA.length) : 0;
  let avgB = bA.length ? Math.round(bA.reduce((a,b)=>a+b,0)/bA.length) : 0;
  document.getElementById('acc-w').textContent = avgW + '%';
  document.getElementById('acc-b').textContent = avgB + '%';
  document.getElementById('acc-card').style.display = 'block';
  document.getElementById('erw').innerHTML =
    `<div class="ep ep-b">?? ${wB} Blunders</div><div class="ep ep-m">? ${wM} Mistakes</div><div class="ep ep-i">⁈ ${wI} Inaccuracies</div>`;
  document.getElementById('erb').innerHTML =
    `<div class="ep ep-b">?? ${bB} Blunders</div><div class="ep ep-m">? ${bM} Mistakes</div><div class="ep ep-i">⁈ ${bI} Inaccuracies</div>`;
}

function annBadge(ann) {
  if (!ann || ann === 'best') return '';
  if (ann === 'blunder')     return '<span class="ann a-bl">?!</span>';
  if (ann === 'mistake')     return '<span class="ann a-ms">?</span>';
  if (ann === 'inaccuracy')  return '<span class="ann a-in">⁈</span>';
  if (ann === 'good')        return '<span class="ann a-gd">!</span>';
  return '';
}

function renderRvMoves() {
  if (!rvSt.length) return;
  let s = '';
  for (let i = 1; i < rvSt.length; i++) {
    let st = rvSt[i];
    if (st.color === 'w') s += '<span class="rn">' + st.moveNum + '.</span>';
    s += '<span class="rm' + (i===rvIdx?' on':'') + '" id="rm' + i + '" onclick="rvGo(' + i + ')">' +
         st.san + annBadge(st.ann) + '</span> ';
    if (st.color === 'b') s += '<br>';
  }
  document.getElementById('rv-mlist').innerHTML = s || '<span style="color:var(--dim)">No game loaded</span>';
}

function rvGo(idx) {
  if (!rvSt.length) return;
  rvIdx = Math.max(0, Math.min(idx, rvSt.length - 1));
  let st = rvSt[rvIdx];
  rvboard.position(st.fen);
  document.getElementById('rvctr').textContent = rvIdx + ' / ' + (rvSt.length - 1);
  let who  = st.color === 'w' ? 'White' : st.color === 'b' ? 'Black' : '';
  let desc = rvIdx === 0
    ? 'Starting position'
    : 'Move ' + st.moveNum + ' — ' + who + ' played ' + st.san +
      (st.ann && st.ann !== 'best' ? '  [' + st.ann + ']' : '');
  setSbar('rv', desc);
  updateEvBar();
  document.querySelectorAll('.rm').forEach(e => e.classList.remove('on'));
  let el = document.getElementById('rm' + rvIdx);
  if (el) { el.classList.add('on'); el.scrollIntoView({block:'nearest'}); }
}

function updateEvBar() {
  let sc = rvEv[rvIdx];
  if (sc === null) { document.getElementById('ev-score').textContent = '…'; return; }
  let cap  = Math.max(-1000, Math.min(1000, sc));
  let pct  = Math.max(4, Math.min(96, 50 + cap / 20));
  document.getElementById('ev-bar').style.height = pct + '%';
  let txt = sc >= 30000 ? 'M+' : sc <= -30000 ? 'M−' : (sc > 0 ? '+' : '') + (sc / 100).toFixed(2);
  document.getElementById('ev-score').textContent = txt;
}

function rvPrev() { rvGo(rvIdx - 1); }
function rvNext() { rvGo(rvIdx + 1); }
function rvLast() { rvGo(rvSt.length - 1); }

document.addEventListener('keydown', e => {
  if (!document.getElementById('pg-review').classList.contains('on')) return;
  if (e.key === 'ArrowRight') rvNext();
  if (e.key === 'ArrowLeft')  rvPrev();
  if (e.key === 'Home') rvGo(0);
  if (e.key === 'End')  rvLast();
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║              ChessMaster Pro  —  v3.0                     ║
╠═══════════════════════════════════════════════════════════╣
║  Open →  http://localhost:5000                            ║
╠═══════════════════════════════════════════════════════════╣
║  🌐  ONLINE  Random matchmaking — no codes needed!        ║
║       Two players open the same URL, both click           ║
║       ⚡ FIND OPPONENT → instantly auto-paired.           ║
║       10-min clocks  ·  Draw offers  ·  Resign            ║
║       Chat  ·  → Review any finished game                 ║
║                                                           ║
║  🤖  AI PLAY  Stockfish WASM, all 20 levels               ║
║       Level 1  →  ~400 Elo  (Total Beginner)              ║
║       Level 10 →  ~1600 Elo (Intermediate)                ║
║       Level 20 →  ~3200 Elo (Super-GM)                    ║
║                                                           ║
║  🔍  REVIEW  Full Stockfish analysis of any PGN           ║
║       Vertical eval bar  ·  Accuracy %                    ║
║       Blunder / Mistake / Inaccuracy detection            ║
║       ← → arrow keys for navigation                       ║
║                                                           ║
║  To play online from two devices on the same network:     ║
║       Both open  http://YOUR_LOCAL_IP:5000                ║
╚═══════════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
