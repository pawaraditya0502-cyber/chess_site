"""
╔══════════════════════════════════════════════════════════╗
║           GRANDMASTER CHESS  —  Full Platform            ║
╠══════════════════════════════════════════════════════════╣
║  Install : pip install flask                             ║
║  Run     : python chess_app.py                          ║
║  Open    : http://localhost:5000                         ║
╠══════════════════════════════════════════════════════════╣
║  Features:                                               ║
║  🌐  Online multiplayer — random matchmaking             ║
║      (Two players open the URL → click Find Match        ║
║       → instantly auto-paired, no codes needed)          ║
║  🤖  vs Stockfish — Level 1-20 (400→3200 Elo)           ║
║  🔍  Game review — full Stockfish analysis               ║
║      eval bar · accuracy % · blunder detection           ║
╚══════════════════════════════════════════════════════════╝
"""

from flask import Flask, request, jsonify, render_template_string
import threading, uuid, time, random, os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────
#  SERVER-SIDE MATCHMAKING + GAME STATE
# ─────────────────────────────────────────────────────────
_lobby_lock = threading.Lock()
_waiting    = None          # {pid, evt, ts}
_games      = {}            # gid → GameState
_games_lock = threading.Lock()


class _Evt:
    """Simple threading event that carries a payload."""
    def __init__(self):
        self._e = threading.Event()
        self._d = None
    def set(self, d):
        self._d = d; self._e.set()
    def wait(self, t=28):
        self._e.wait(t); return self._d


class GameState:
    def __init__(self, gid, white, black):
        self.gid    = gid
        self.white  = white
        self.black  = black
        self.moves  = []          # SAN list
        self.fen    = "start"
        self.status = "active"
        self.result = None
        self.ts     = time.time()
        self._lock  = threading.Lock()
        self._q     = {white: [], black: []}   # per-player event queues

    def push(self, pid, ev):
        with self._lock:
            if pid in self._q: self._q[pid].append(ev)

    def push_both(self, ev):
        with self._lock:
            for q in self._q.values(): q.append(ev)

    def drain(self, pid, timeout=22):
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self._q.get(pid):
                    out = self._q[pid][:]
                    self._q[pid] = []
                    return out
            time.sleep(0.1)
        return []


def _gc():
    """Garbage-collect games older than 1 hour."""
    while True:
        time.sleep(120)
        cut = time.time() - 3600
        with _games_lock:
            dead = [g for g, s in _games.items() if s.ts < cut]
            for g in dead: del _games[g]

threading.Thread(target=_gc, daemon=True).start()


# ─────────────────────────────────────────────────────────
#  API  ROUTES
# ─────────────────────────────────────────────────────────
@app.route("/api/queue", methods=["POST"])
def api_queue():
    global _waiting
    pid = (request.json or {}).get("pid") or str(uuid.uuid4())

    with _lobby_lock:
        if _waiting and _waiting["pid"] != pid:
            opp   = _waiting; _waiting = None
            flip  = random.random() < 0.5
            w, b  = (pid, opp["pid"]) if flip else (opp["pid"], pid)
            gid   = uuid.uuid4().hex[:10]
            gs    = GameState(gid, w, b)
            with _games_lock: _games[gid] = gs
            my_c  = "w" if w == pid else "b"
            opp["evt"].set({"status":"matched","gid":gid,"color":"b" if my_c=="w" else "w","pid":opp["pid"]})
            return jsonify({"status":"matched","gid":gid,"color":my_c,"pid":pid})
        else:
            ev = _Evt()
            _waiting = {"pid":pid,"evt":ev,"ts":time.time()}

    result = ev.wait(28)
    with _lobby_lock:
        if _waiting and _waiting["pid"] == pid: _waiting = None
    return jsonify(result if result else {"status":"waiting","pid":pid})


@app.route("/api/move", methods=["POST"])
def api_move():
    d   = request.json or {}
    gid = d.get("gid"); pid = d.get("pid")
    with _games_lock: gs = _games.get(gid)
    if not gs: return jsonify({"ok":False})
    opp = gs.black if gs.white == pid else gs.white
    with gs._lock:
        gs.moves.append(d.get("san","?"))
        gs.fen    = d.get("fen", gs.fen)
        gs.status = d.get("status","active")
        gs.result = d.get("result")
        gs.ts     = time.time()
        gs._q[opp].append({"type":"move","uci":d.get("uci",""),
                            "san":d.get("san"),"fen":gs.fen,
                            "status":gs.status,"result":gs.result})
    return jsonify({"ok":True})


@app.route("/api/poll", methods=["POST"])
def api_poll():
    d   = request.json or {}
    gid = d.get("gid"); pid = d.get("pid")
    with _games_lock: gs = _games.get(gid)
    if not gs: return jsonify({"events":[{"type":"abandoned"}]})
    return jsonify({"events": gs.drain(pid, 22)})


@app.route("/api/action", methods=["POST"])
def api_action():
    d   = request.json or {}
    gid = d.get("gid"); pid = d.get("pid"); act = d.get("action")
    with _games_lock: gs = _games.get(gid)
    if not gs: return jsonify({"ok":False})
    opp  = gs.black if gs.white == pid else gs.white
    col  = "w" if gs.white == pid else "b"
    win  = "Black" if col=="w" else "White"
    if   act == "resign":       gs.push_both({"type":"end","result":win+" wins by resignation"})
    elif act == "draw_offer":   gs.push(opp, {"type":"draw_offer"})
    elif act == "draw_accept":  gs.push_both({"type":"end","result":"½–½ Draw by agreement"})
    elif act == "draw_decline": gs.push(opp, {"type":"draw_declined"})
    elif act == "chat":         gs.push(opp, {"type":"chat","msg":d.get("msg","")[:120]})
    return jsonify({"ok":True})


@app.route("/")
def index():
    return render_template_string(_PAGE)


# ─────────────────────────────────────────────────────────
#  FULL SINGLE-PAGE APPLICATION
# ─────────────────────────────────────────────────────────
_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grandmaster Chess</title>

<!-- Chess libraries -->
<link rel="stylesheet"
  href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
<!-- Stockfish Level 20 WASM — runs entirely in the browser -->
<script src="https://cdn.jsdelivr.net/npm/stockfish.wasm@0.10.0/stockfish.js"></script>

<style>
/* ── FONT ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Code+Pro:wght@400;600&display=swap');

/* ── COLOUR PALETTE  (deep mahogany + gold + cream) ── */
:root{
  --bg:    #0c0a08;
  --ink:   #110e0a;
  --felt:  #181410;
  --rail:  #221d17;
  --rim:   #2d2620;
  --wire:  #3e3428;
  --dim:   #7a6a55;
  --mid:   #a08060;
  --cream: #f0e6d0;
  --ivory: #e8dcc4;
  --gold:  #c8902a;
  --amber: #e8a830;
  --shine: #f8d060;
  --sage:  #4a7a50;
  --rose:  #8a3838;
  --sky:   #3a6888;
  --r:4px;
}

*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--ivory);
  font-family:'Libre Baskerville',serif;font-size:14px;overflow:hidden}

/* ── SHELL ── */
.shell{display:flex;height:100vh}

/* ── SIDEBAR ── */
.sidebar{
  width:54px;flex-shrink:0;background:var(--ink);
  border-right:1px solid var(--rim);
  display:flex;flex-direction:column;align-items:center;
  padding:14px 0;gap:4px;
}
.logo{
  font-family:'Playfair Display',serif;font-weight:900;
  font-size:.8rem;color:var(--gold);letter-spacing:3px;
  writing-mode:vertical-rl;transform:rotate(180deg);
  margin-bottom:18px;text-shadow:0 0 20px rgba(200,144,42,.4);
}
.sbtn{
  width:38px;height:38px;border-radius:var(--r);
  border:1px solid transparent;background:transparent;
  color:var(--dim);font-size:1.1rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:all .16s;position:relative;
}
.sbtn:hover{background:var(--rail);color:var(--ivory);border-color:var(--wire)}
.sbtn.on{background:rgba(200,144,42,.14);color:var(--amber);
         border-color:rgba(200,144,42,.4);box-shadow:0 0 10px rgba(200,144,42,.12)}
.sbtn .tip{
  position:absolute;left:46px;top:50%;transform:translateY(-50%);
  background:var(--rail);border:1px solid var(--wire);
  color:var(--ivory);font-family:'Source Code Pro',monospace;
  font-size:.62rem;padding:3px 8px;border-radius:3px;
  white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .14s;z-index:99;
}
.sbtn:hover .tip{opacity:1}

/* ── MAIN ── */
.main{flex:1;overflow-y:auto;padding:20px 24px}

/* ── PAGES ── */
.page{display:none}.page.on{display:block}

/* ── TWO-COL BOARD LAYOUT ── */
.lay{display:grid;grid-template-columns:462px 1fr;gap:18px;align-items:start}

/* ── BOARD SHELL ── */
.bsh{
  background:var(--felt);border:1px solid var(--rim);
  border-radius:var(--r);padding:14px;position:relative;
}
#on-board{width:434px}
#ai-board{width:434px}
#rv-board{width:400px}

/* ── CARDS / COLUMN ── */
.col{display:flex;flex-direction:column;gap:10px}
.card{background:var(--felt);border:1px solid var(--wire);border-radius:var(--r);padding:14px}
.ctitle{
  font-family:'Playfair Display',serif;font-size:.72rem;font-weight:700;
  letter-spacing:3px;text-transform:uppercase;color:var(--gold);
  margin-bottom:11px;padding-bottom:8px;border-bottom:1px solid var(--rim);
}

/* ── STATUS BAR ── */
.sbar{
  font-family:'Source Code Pro',monospace;font-size:.68rem;
  padding:7px 11px;border-radius:3px;margin-bottom:11px;
  background:rgba(74,122,80,.07);border:1px solid rgba(74,122,80,.2);
  color:var(--sage);min-height:30px;line-height:1.5;
}
.sbar.amber{background:rgba(200,144,42,.07);border-color:rgba(200,144,42,.25);color:var(--amber)}
.sbar.rose {background:rgba(138,56,56,.07); border-color:rgba(138,56,56,.25); color:var(--rose)}
.sbar.sky  {background:rgba(58,104,136,.07);border-color:rgba(58,104,136,.25);color:var(--sky)}

/* ── BUTTONS ── */
.brow{display:flex;gap:6px;flex-wrap:wrap}
.btn{
  padding:7px 13px;border-radius:var(--r);
  font-family:'Playfair Display',serif;font-size:.65rem;
  font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  cursor:pointer;transition:all .14s;border:1px solid;
}
.btn:disabled{opacity:.3;cursor:not-allowed}
.bg {background:rgba(200,144,42,.12);color:var(--amber);border-color:rgba(200,144,42,.3)}
.bg:hover:not(:disabled){background:rgba(200,144,42,.22)}
.bk {background:var(--rim);color:var(--ivory);border-color:var(--wire)}
.bk:hover:not(:disabled){background:var(--wire)}
.br {background:rgba(138,56,56,.12);color:var(--rose);border-color:rgba(138,56,56,.3)}
.br:hover:not(:disabled){background:rgba(138,56,56,.22)}
.bs {background:rgba(74,122,80,.12);color:var(--sage);border-color:rgba(74,122,80,.3)}
.bs:hover:not(:disabled){background:rgba(74,122,80,.22)}
.by {background:rgba(58,104,136,.12);color:var(--sky);border-color:rgba(58,104,136,.3)}
.by:hover:not(:disabled){background:rgba(58,104,136,.22)}
.bsm{padding:5px 9px;font-size:.6rem}

/* ── ONLINE LOBBY ── */
.lobby{
  display:flex;flex-direction:column;align-items:center;
  gap:16px;padding:26px 14px;text-align:center;
}
.lob-king{
  font-size:3.5rem;
  animation:float 3.5s ease-in-out infinite;
  filter:drop-shadow(0 0 22px rgba(200,144,42,.45));
}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.lob-title{
  font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:900;
  color:var(--cream);letter-spacing:4px;
  text-shadow:0 0 30px rgba(200,144,42,.25);
}
.lob-sub{color:var(--dim);font-size:.82rem;line-height:1.7;max-width:280px;font-style:italic}
.find-btn{
  padding:12px 34px;border-radius:var(--r);border:none;
  background:linear-gradient(135deg,var(--gold),var(--amber));
  color:var(--ink);font-family:'Playfair Display',serif;
  font-size:.82rem;font-weight:900;letter-spacing:3px;
  cursor:pointer;transition:all .2s;
  box-shadow:0 4px 22px rgba(200,144,42,.28);
}
.find-btn:hover{transform:translateY(-2px);box-shadow:0 6px 30px rgba(200,144,42,.42)}
.find-btn:disabled{opacity:.4;cursor:not-allowed;transform:none}
.searching{
  display:none;align-items:center;gap:10px;
  font-family:'Source Code Pro',monospace;font-size:.68rem;color:var(--amber);
}
.searching.on{display:flex}
.pdot{
  width:8px;height:8px;border-radius:50%;background:var(--amber);
  animation:pd 1.1s ease-in-out infinite;
}
@keyframes pd{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.8);opacity:.35}}

/* ── PLAYER STRIPS ── */
.strip{
  display:flex;align-items:center;gap:9px;
  padding:7px 11px;border-radius:3px;margin-bottom:7px;
  background:var(--rail);border:1px solid var(--wire);
  transition:border-color .2s,background .2s;
}
.strip.active{border-color:rgba(200,144,42,.4);background:rgba(200,144,42,.04)}
.strip .ico{font-size:1.2rem}
.strip .nm{font-family:'Playfair Display',serif;font-size:.78rem;font-weight:700}
.strip .tg{font-size:.58rem;color:var(--dim);font-family:'Source Code Pro',monospace}
.strip .clk{
  margin-left:auto;font-family:'Source Code Pro',monospace;
  font-size:.9rem;font-weight:600;min-width:44px;text-align:right;
}
.strip .clk.low{color:var(--rose);animation:blink .55s ease infinite alternate}
@keyframes blink{from{opacity:1}to{opacity:.3}}

/* ── RESULT OVERLAY ── */
.res-ov{
  display:none;position:absolute;inset:0;border-radius:var(--r);
  background:rgba(12,10,8,.88);backdrop-filter:blur(3px);
  z-index:30;flex-direction:column;
  align-items:center;justify-content:center;gap:12px;
}
.res-ov.on{display:flex}
.res-t{
  font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:900;
  letter-spacing:4px;color:var(--cream);text-align:center;line-height:1.3;
}
.res-s{font-size:.72rem;color:var(--dim);font-family:'Source Code Pro',monospace}

/* ── DRAW TOAST ── */
.dtost{
  display:none;position:absolute;top:50%;left:50%;
  transform:translate(-50%,-50%);z-index:40;
  background:var(--rail);border:1px solid var(--gold);
  border-radius:6px;padding:16px 18px;text-align:center;
  min-width:200px;box-shadow:0 8px 38px rgba(0,0,0,.55);
}
.dtost.on{display:block}
.dtost h4{font-family:'Playfair Display',serif;color:var(--gold);letter-spacing:2px;margin-bottom:10px}

/* ── LEVEL SLIDER ── */
.lv-wrap{display:flex;flex-direction:column;gap:7px}
.lv-top {display:flex;align-items:center;gap:13px}
.lv-big {font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:900;
         color:var(--amber);line-height:1;text-shadow:0 0 14px rgba(232,168,48,.3)}
.lv-name{font-size:.76rem;color:var(--ivory);font-weight:700}
.lv-elo {font-size:.64rem;color:var(--dim);font-family:'Source Code Pro',monospace;margin-top:2px}
.lv-trk {position:relative;height:5px;background:var(--wire);border-radius:3px;cursor:pointer;margin:3px 0}
.lv-fil {position:absolute;left:0;top:0;height:100%;
         background:linear-gradient(90deg,var(--sage),var(--amber),var(--rose));
         border-radius:3px;pointer-events:none;transition:width .1s}
.lv-thu {position:absolute;top:50%;transform:translate(-50%,-50%);
         width:14px;height:14px;border-radius:50%;
         background:var(--amber);border:2px solid var(--bg);
         cursor:grab;box-shadow:0 0 8px rgba(232,168,48,.35)}
.lv-lbs{display:flex;justify-content:space-between;
        font-size:.6rem;color:var(--dim);font-family:'Source Code Pro',monospace}

/* ── COLOR PICK ── */
.cpick{display:flex;gap:7px}
.copt{
  flex:1;padding:7px;border-radius:var(--r);border:1px solid var(--wire);
  background:var(--rail);color:var(--dim);font-size:.66rem;font-weight:700;
  cursor:pointer;text-align:center;transition:all .14s;
  font-family:'Playfair Display',serif;letter-spacing:1.5px;
}
.copt:hover{border-color:var(--amber);color:var(--ivory)}
.copt.on{background:rgba(200,144,42,.13);color:var(--amber);border-color:rgba(200,144,42,.42)}

/* ── ENGINE BAR ── */
.ebar{
  display:flex;align-items:center;gap:8px;
  font-family:'Source Code Pro',monospace;font-size:.66rem;
  padding:7px 10px;border-radius:3px;
  background:rgba(58,104,136,.06);border:1px solid rgba(58,104,136,.18);
  color:var(--sky);min-height:30px;
}
.spin{width:10px;height:10px;border-radius:50%;flex-shrink:0;
      border:2px solid rgba(58,104,136,.2);border-top-color:var(--sky);
      animation:sp .6s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}

/* ── MOVE LIST ── */
.mlist{
  font-family:'Source Code Pro',monospace;font-size:.68rem;
  max-height:190px;overflow-y:auto;line-height:2;color:var(--mid);
}
.mp{display:flex;gap:4px}
.mn{color:var(--gold);min-width:22px}
.mv{padding:1px 4px;border-radius:2px;cursor:pointer;color:var(--ivory);transition:background .1s}
.mv:hover{background:var(--wire)}
.mv.on{background:var(--gold);color:var(--ink)}

/* ── INPUTS ── */
input[type=text],textarea,select{
  width:100%;padding:6px 9px;
  background:var(--rail);color:var(--ivory);
  border:1px solid var(--wire);border-radius:var(--r);
  font-family:'Source Code Pro',monospace;font-size:.68rem;
  outline:none;transition:border .14s;
}
input:focus,textarea:focus,select:focus{border-color:var(--gold)}
textarea{height:70px;resize:vertical}
select{cursor:pointer}

/* ── CHAT ── */
.chatbox{
  max-height:88px;overflow-y:auto;border:1px solid var(--wire);
  border-radius:3px;padding:6px 8px;background:var(--rail);margin-bottom:6px;
}
.cm{font-family:'Source Code Pro',monospace;font-size:.63rem;line-height:1.9}
.cm.me {color:var(--amber)}.cm.opp{color:var(--ivory)}.cm.sys{color:var(--dim);font-style:italic}
.chat-row{display:flex;gap:6px}.chat-row input{flex:1}

/* ── REVIEW EVAL BAR ── */
.rev-row{display:flex;gap:0}
.ev-col{display:flex;flex-direction:column;align-items:center;width:18px;flex-shrink:0;margin-right:8px}
.ev-out{flex:1;width:100%;background:var(--wire);border-radius:3px;overflow:hidden;position:relative}
.ev-w  {position:absolute;bottom:0;left:0;right:0;background:var(--cream);transition:height .3s ease}
.ev-num{
  font-family:'Source Code Pro',monospace;font-size:.64rem;font-weight:600;
  padding:3px 4px;background:var(--rail);border:1px solid var(--wire);
  border-radius:3px;margin-top:3px;color:var(--ivory);white-space:nowrap;
}

/* ── ANALYSIS PROGRESS ── */
.prog-wrap{margin-top:8px}
.prog-trk{height:3px;background:var(--wire);border-radius:2px;overflow:hidden}
.prog-fil{height:100%;background:var(--sky);border-radius:2px;transition:width .15s;width:0}
.prog-lbl{font-size:.62rem;color:var(--dim);font-family:'Source Code Pro',monospace;margin-top:3px}

/* ── ACCURACY ── */
.acc-row{display:flex;gap:7px;margin-top:8px}
.acc-box{flex:1;text-align:center;padding:8px 4px;border-radius:3px;
         border:1px solid var(--wire);background:var(--rail)}
.acc-num{font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:900;color:var(--amber)}
.acc-lbl{font-size:.6rem;color:var(--dim);margin-top:1px}
.err-row{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}
.ep{display:flex;align-items:center;gap:4px;padding:3px 8px;border-radius:12px;
    font-family:'Source Code Pro',monospace;font-size:.62rem}
.epb{background:rgba(138,56,56,.1);border:1px solid rgba(138,56,56,.25);color:var(--rose)}
.epm{background:rgba(200,120,40,.1);border:1px solid rgba(200,120,40,.25);color:#c87030}
.epi{background:rgba(200,144,42,.1);border:1px solid rgba(200,144,42,.25);color:var(--gold)}

/* ── REVIEW MOVE LIST ── */
.rmlist{font-family:'Source Code Pro',monospace;font-size:.68rem;max-height:230px;overflow-y:auto;line-height:2.1}
.rm{display:inline-block;padding:1px 5px;border-radius:2px;cursor:pointer;transition:background .1s}
.rm:hover{background:var(--wire)}
.rm.on{background:var(--gold);color:var(--ink)}
.rn{color:var(--gold);margin-right:2px}
.ann{display:inline-block;width:13px;height:13px;border-radius:50%;font-size:.55rem;
     text-align:center;line-height:13px;margin-left:2px;font-weight:700;vertical-align:middle}
.abl{background:var(--rose);color:#fff}
.ams{background:#c87030;color:#fff}
.ain{background:var(--gold);color:var(--ink)}
.agd{background:var(--sky);color:#fff}

/* ── PROMOTION MODAL ── */
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.86);
         z-index:200;align-items:center;justify-content:center}
.overlay.on{display:flex}
.modal{background:var(--rail);border:1px solid var(--gold);border-radius:6px;
       padding:22px;text-align:center;box-shadow:0 8px 40px rgba(0,0,0,.5)}
.modal h3{font-family:'Playfair Display',serif;font-size:.88rem;letter-spacing:3px;
          color:var(--amber);margin-bottom:14px}
.prow{display:flex;gap:10px;justify-content:center}
.pbtn{font-size:2rem;cursor:pointer;padding:8px 12px;border:1px solid var(--wire);
      background:var(--felt);border-radius:4px;transition:all .13s}
.pbtn:hover{border-color:var(--gold);transform:scale(1.1)}

/* ── HIGHLIGHTS ── */
.hf{box-shadow:inset 0 0 0 3px rgba(200,144,42,.72)!important}
.ht{box-shadow:inset 0 0 0 3px rgba(232,168,48,.96)!important}

::-webkit-scrollbar{width:3px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--wire);border-radius:2px}
</style>
</head>
<body>
<div class="shell">

<!-- ══ SIDEBAR ══ -->
<nav class="sidebar">
  <div class="logo">GM</div>
  <button class="sbtn on" id="nb-on" onclick="goPage('on')">🌐<span class="tip">Online — Random Match</span></button>
  <button class="sbtn"    id="nb-ai" onclick="goPage('ai')">🤖<span class="tip">vs Stockfish AI</span></button>
  <button class="sbtn"    id="nb-rv" onclick="goPage('rv')">🔍<span class="tip">Review &amp; Analyse</span></button>
</nav>

<div class="main">

<!-- ════════════════════════════ ONLINE PAGE ════════════════════════════ -->
<div class="page on" id="pg-on">
  <div class="lay">

    <div class="bsh" id="on-bsh">
      <div class="sbar sky" id="on-sb">Click ⚡ Find Match to be paired with a random opponent instantly</div>

      <!-- Opponent strip (top of board) -->
      <div class="strip" id="opp-strip" style="display:none">
        <span class="ico" id="opp-ico">♚</span>
        <div><div class="nm">Opponent</div><div class="tg">ONLINE</div></div>
        <div class="clk" id="opp-clk">10:00</div>
      </div>

      <div id="on-board"></div>

      <!-- My strip (bottom of board) -->
      <div class="strip" id="my-strip" style="display:none;margin-top:8px">
        <span class="ico" id="my-ico">♔</span>
        <div><div class="nm">You</div><div class="tg" id="my-ctag">WHITE</div></div>
        <div class="clk" id="my-clk">10:00</div>
      </div>

      <!-- Draw offer toast -->
      <div class="dtost" id="dtost">
        <h4>♟ DRAW OFFERED</h4>
        <p style="font-size:.73rem;color:var(--dim);margin-bottom:11px;font-style:italic">Your opponent offers a draw</p>
        <div class="brow" style="justify-content:center;gap:8px">
          <button class="btn bs bsm" onclick="acceptDraw()">Accept</button>
          <button class="btn br bsm" onclick="declineDraw()">Decline</button>
        </div>
      </div>

      <!-- Result overlay -->
      <div class="res-ov" id="on-res">
        <div class="res-t" id="on-res-t">Game Over</div>
        <div class="res-s" id="on-res-s"></div>
        <div class="brow" style="margin-top:12px;justify-content:center;gap:8px">
          <button class="btn bg" onclick="resetOnline()">New Match</button>
          <button class="btn bk" onclick="onToReview()">→ Review</button>
        </div>
      </div>
    </div>

    <div class="col">

      <!-- Lobby card -->
      <div class="card" id="lobby-card">
        <div class="ctitle">Quick Match</div>
        <div class="lobby">
          <div class="lob-king">♛</div>
          <div class="lob-title">FIND MATCH</div>
          <div class="lob-sub">
            One click — you'll be instantly paired with a random player.
            No codes, no invites, no waiting rooms.
          </div>
          <button class="find-btn" id="find-btn" onclick="findMatch()">⚡ FIND OPPONENT</button>
          <div class="searching" id="searching">
            <div class="pdot"></div>
            <span id="srch-txt">Searching for opponent…</span>
          </div>
          <div style="font-size:.62rem;color:var(--dim);font-family:'Source Code Pro',monospace">
            Time control: 10 + 0 · Colours assigned randomly
          </div>
        </div>
      </div>

      <!-- In-game controls (shown when game active) -->
      <div class="card" id="on-ctrl" style="display:none">
        <div class="ctitle">Controls</div>
        <div class="brow">
          <button class="btn bk bsm" onclick="offerDraw()">½ Offer Draw</button>
          <button class="btn br bsm" onclick="resignOnline()">Resign</button>
          <button class="btn bk bsm" onclick="resetOnline()">New Game</button>
        </div>
      </div>

      <!-- Move history (online) -->
      <div class="card" id="on-hist" style="display:none">
        <div class="ctitle">Move History</div>
        <div class="mlist" id="on-ml"><span style="color:var(--dim)">No moves yet</span></div>
        <div class="brow" style="margin-top:8px">
          <button class="btn bk bsm" onclick="onToReview()">→ Review</button>
          <button class="btn bk bsm" onclick="cpyOnPgn()">📋 PGN</button>
        </div>
      </div>

      <!-- Chat -->
      <div class="card" id="on-chat-card" style="display:none">
        <div class="ctitle">Chat</div>
        <div class="chatbox" id="chatbox"></div>
        <div class="chat-row">
          <input type="text" id="chat-inp" placeholder="Message…" maxlength="100"
            onkeydown="if(event.key==='Enter')sendChat()">
          <button class="btn bk bsm" onclick="sendChat()">Send</button>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ════════════════════════════ AI PAGE ════════════════════════════ -->
<div class="page" id="pg-ai">
  <div class="lay">
    <div class="bsh">
      <div class="sbar" id="ai-sb">Set Stockfish level &amp; colour, then press ▶ Start</div>
      <div id="ai-board"></div>
    </div>
    <div class="col">

      <div class="card">
        <div class="ctitle">Stockfish Level</div>
        <div class="lv-wrap">
          <div class="lv-top">
            <div class="lv-big" id="lv-n">20</div>
            <div>
              <div class="lv-name" id="lv-nm">Super-GM / Maximum</div>
              <div class="lv-elo"  id="lv-el">~3200 Elo</div>
            </div>
          </div>
          <div class="lv-trk" id="lvt">
            <div class="lv-fil" id="lvf"></div>
            <div class="lv-thu" id="lvth"></div>
          </div>
          <div class="lv-lbs">
            <span>1–Beginner</span><span>10–Intermediate</span><span>20–Master</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="ctitle">Play As</div>
        <div class="cpick">
          <div class="copt on" id="pw" onclick="pickC('w')">♔ White</div>
          <div class="copt"    id="pb" onclick="pickC('b')">♚ Black</div>
        </div>
        <div class="brow" style="margin-top:10px">
          <button class="btn bg"       onclick="startAI()">▶ Start</button>
          <button class="btn bk"       onclick="flipAI()">⇅ Flip</button>
          <button class="btn br bsm" id="ai-res" onclick="resignAI()" disabled>Resign</button>
        </div>
      </div>

      <div class="card" id="ai-ec" style="display:none">
        <div class="ctitle">Engine</div>
        <div class="ebar" id="ai-eb"><span style="color:var(--dim)">Idle</span></div>
      </div>

      <div class="card">
        <div class="ctitle">Move History</div>
        <div class="mlist" id="ai-ml"><span style="color:var(--dim)">No moves yet</span></div>
        <div class="brow" style="margin-top:8px">
          <button class="btn bk bsm" onclick="undoAI()">↩ Undo</button>
          <button class="btn bk bsm" onclick="aiToReview()">→ Review</button>
          <button class="btn bk bsm" onclick="cpyAIPgn()">📋 PGN</button>
        </div>
      </div>

      <div class="card">
        <div class="ctitle">Load FEN Position</div>
        <input type="text" id="ai-fen" placeholder="Paste FEN string here…">
        <div class="brow" style="margin-top:7px">
          <button class="btn bg bsm" onclick="loadFen()">Load</button>
          <button class="btn bk bsm" onclick="cpyFen()">Copy FEN</button>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ════════════════════════════ REVIEW PAGE ════════════════════════════ -->
<div class="page" id="pg-rv">
  <div class="lay">
    <div class="bsh">
      <div class="sbar" id="rv-sb">Paste a PGN and click Load &amp; Analyse</div>
      <div class="rev-row">
        <div class="ev-col" style="height:422px">
          <div class="ev-out" id="ev-out">
            <div class="ev-w" id="ev-bar" style="height:50%"></div>
          </div>
          <div class="ev-num" id="ev-num">—</div>
        </div>
        <div style="width:7px"></div>
        <div id="rv-board"></div>
      </div>
    </div>
    <div class="col">

      <div class="card">
        <div class="ctitle">Load Game (PGN)</div>
        <textarea id="pgn-in" placeholder="Paste PGN here…"></textarea>
        <div class="brow" style="margin-top:7px">
          <button class="btn bg"       onclick="loadRv()">Load &amp; Analyse</button>
          <button class="btn bk bsm"   onclick="loadSample()">Sample Game</button>
        </div>
        <div id="rv-prog" class="prog-wrap" style="display:none">
          <div class="prog-trk"><div class="prog-fil" id="pf"></div></div>
          <div class="prog-lbl" id="pl">Analysing…</div>
        </div>
      </div>

      <div class="card">
        <div class="ctitle">Analysis Depth</div>
        <select id="rv-dep">
          <option value="8">Depth 8 — Fast</option>
          <option value="12" selected>Depth 12 — Balanced</option>
          <option value="16">Depth 16 — Deep</option>
          <option value="20">Depth 20 — Maximum (Stockfish Full Power)</option>
        </select>
      </div>

      <div class="card">
        <div class="ctitle">Navigation</div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <button class="btn bk bsm" onclick="rvGo(0)">⏮</button>
          <button class="btn bk bsm" onclick="rvPrev()">◀</button>
          <span id="rvctr" style="font-family:'Source Code Pro',monospace;font-size:.7rem;
                color:var(--amber);min-width:50px;text-align:center">0/0</span>
          <button class="btn bk bsm" onclick="rvNext()">▶</button>
          <button class="btn bk bsm" onclick="rvLast()">⏭</button>
          <button class="btn bk bsm" onclick="if(rvB)rvB.flip()">⇅</button>
        </div>
      </div>

      <div class="card" id="acc-card" style="display:none">
        <div class="ctitle">Accuracy Report</div>
        <div class="acc-row">
          <div class="acc-box"><div class="acc-num" id="acc-w">—</div><div class="acc-lbl">White %</div></div>
          <div class="acc-box"><div class="acc-num" id="acc-b">—</div><div class="acc-lbl">Black %</div></div>
        </div>
        <div class="err-row" id="erw"></div>
        <div class="err-row" id="erb"></div>
      </div>

      <div class="card">
        <div class="ctitle">Move List</div>
        <div class="rmlist" id="rv-ml"><span style="color:var(--dim)">No game loaded</span></div>
      </div>

    </div>
  </div>
</div>

</div><!-- /main -->
</div><!-- /shell -->

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

<!-- ══════════════════════════════════════════════════════════
     JAVASCRIPT
══════════════════════════════════════════════════════════ -->
<script>
/* ── Page navigation ── */
function goPage(p){
  document.querySelectorAll('.page').forEach(e=>e.classList.remove('on'));
  document.querySelectorAll('.sbtn').forEach(e=>e.classList.remove('on'));
  document.getElementById('pg-'+p).classList.add('on');
  document.getElementById('nb-'+p).classList.add('on');
  if(p==='rv'&&!rvB) initRvBoard();
}

/* ══════════════════════════════════════════════════════════
   STOCKFISH  — Level 20 (maximum strength) for review,
               selectable level for AI play
══════════════════════════════════════════════════════════ */
let sf=null, sfOk=false;
let _sfCbs=[], _sfLsn=[];

async function initSF(){
  return new Promise(res=>{
    try{
      sf = typeof Stockfish!=='undefined' ? Stockfish() : null;
      if(!sf){res(false);return;}
      sf.onmessage = e=>{
        let m = typeof e==='string'?e:e.data;
        _sfCbs.forEach(c=>{ if(m.includes(c.k)) c.f(m); });
        [..._sfLsn].forEach(f=>f(m));
      };
      _sfOnce('uciok',  ()=>sf.postMessage('isready'));
      _sfOnce('readyok',()=>{sfOk=true;res(true);});
      sf.postMessage('uci');
      setTimeout(()=>{if(!sfOk){sfOk=true;res(true);}},4000);
    }catch(e){res(false);}
  });
}
function sfPost(c){ if(sf) sf.postMessage(c); }
function _sfOnce(k,f){
  let w; w=m=>{ if(m.includes(k)){ _sfCbs=_sfCbs.filter(c=>c.f!==w); f(m); } };
  _sfCbs.push({k,f:w});
}
function sfAdd(f){_sfLsn.push(f);return f;}
function sfRem(f){_sfLsn=_sfLsn.filter(x=>x!==f);}

/* Level data (1–20) */
const LV=[null,
  {n:'Total Beginner',    e:'~400',  t:60},
  {n:'Absolute Beginner', e:'~500',  t:100},
  {n:'Beginner',          e:'~600',  t:160},
  {n:'Casual',            e:'~700',  t:220},
  {n:'Casual+',           e:'~800',  t:300},
  {n:'Developing',        e:'~900',  t:420},
  {n:'Developing+',       e:'~1000', t:560},
  {n:'Club Player',       e:'~1200', t:720},
  {n:'Club Player+',      e:'~1400', t:920},
  {n:'Intermediate',      e:'~1600', t:1150},
  {n:'Intermediate+',     e:'~1800', t:1450},
  {n:'Advanced',          e:'~2000', t:1800},
  {n:'Advanced+',         e:'~2100', t:2200},
  {n:'Expert',            e:'~2200', t:2700},
  {n:'Expert+',           e:'~2300', t:3200},
  {n:'Master Candidate',  e:'~2400', t:3800},
  {n:'National Master',   e:'~2500', t:4800},
  {n:'Intl Master',       e:'~2600', t:6000},
  {n:'Grandmaster',       e:'~2700', t:8000},
  {n:'Super-GM / MAX',    e:'~3200', t:12000},
];

/* Get best move at given skill level */
function sfBestMove(fen, lv, cb){
  if(!sfOk){cb(null);return;}
  sfPost('ucinewgame');
  sfPost('setoption name Skill Level value '+lv);
  sfPost('position fen '+fen);
  let L=sfAdd(m=>{
    if(m.startsWith('bestmove')){
      sfRem(L);
      let p=m.split(' ');
      cb(p[1]&&p[1]!=='(none)'?p[1]:null);
    }
  });
  sfPost('go movetime '+(LV[lv]?.t||1000));
}

/* Evaluate position at depth (always level 20 for accuracy) */
function sfEval(fen, depth, cb){
  if(!sfOk){cb(0);return;}
  sfPost('ucinewgame');
  sfPost('setoption name Skill Level value 20');
  sfPost('position fen '+fen);
  let last=0;
  let L=sfAdd(m=>{
    let cm=m.match(/score cp (-?\d+)/);   if(cm) last=parseInt(cm[1]);
    let mm=m.match(/score mate (-?\d+)/); if(mm) last=parseInt(mm[1])>0?32000:-32000;
    if(m.startsWith('bestmove')){sfRem(L);cb(last);}
  });
  sfPost('go depth '+depth);
}

/* ══════════════════════════════════════════════════════════
   LEVEL SLIDER
══════════════════════════════════════════════════════════ */
let curLv=20;
function setLv(v){
  curLv=Math.max(1,Math.min(20,v));
  let p=(curLv-1)/19*100;
  document.getElementById('lv-n').textContent  = curLv;
  document.getElementById('lv-nm').textContent = LV[curLv].n;
  document.getElementById('lv-el').textContent = LV[curLv].e+' Elo';
  document.getElementById('lvf').style.width   = p+'%';
  document.getElementById('lvth').style.left   = p+'%';
}
(function(){
  let tr=document.getElementById('lvt'), drag=false;
  function p2l(x){
    let r=tr.getBoundingClientRect();
    return Math.round(Math.max(0,Math.min(1,(x-r.left)/r.width))*19+1);
  }
  tr.addEventListener('mousedown', e=>{drag=true;setLv(p2l(e.clientX));});
  document.addEventListener('mousemove', e=>{if(drag)setLv(p2l(e.clientX));});
  document.addEventListener('mouseup', ()=>drag=false);
  tr.addEventListener('touchstart', e=>{drag=true;setLv(p2l(e.touches[0].clientX));},{passive:true});
  document.addEventListener('touchmove', e=>{if(drag)setLv(p2l(e.touches[0].clientX));},{passive:true});
  document.addEventListener('touchend', ()=>drag=false);
  setLv(20);
})();

/* ══════════════════════════════════════════════════════════
   ONLINE MULTIPLAYER — random matchmaking via long-poll
══════════════════════════════════════════════════════════ */
let onGame=new Chess(), onB=null;
let myPid=(localStorage.getItem('gm_pid')||function(){
  let p='P'+Math.random().toString(36).slice(2,12);
  localStorage.setItem('gm_pid',p);return p;
}());
let onGid=null, myCol=null, onActive=false;
let pendOn=null, pendAI=null;
let polling=false;
let cwW=600, cwB=600, cwTimer=null;
let onMoves=[];  // {san,color}

$(document).ready(function(){
  onB=Chessboard('on-board',{
    draggable:true, position:'start',
    onDragStart:onDragS, onDrop:onDrop,
    onSnapEnd:()=>onB.position(onGame.fen()),
    pieceTheme:'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
  initSF().then(ok=>{
    if(!ok) setSbar('rv','⚠ Stockfish engine failed to load','rose');
    else    setSbar('rv','Stockfish Level 20 ready — paste a PGN and click Load & Analyse');
  });
});

/* ── Matchmaking ── */
function findMatch(){
  document.getElementById('find-btn').disabled=true;
  document.getElementById('searching').classList.add('on');
  setSbar('on','Searching for an opponent…','sky');
  doQueue();
}
function doQueue(){
  fetch('/api/queue',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pid:myPid})
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.status==='matched') beginGame(d.gid,d.color,d.pid||myPid);
    else{ document.getElementById('srch-txt').textContent='Still searching…'; doQueue(); }
  })
  .catch(()=>{ setSbar('on','Connection error — retrying…','rose'); setTimeout(doQueue,2200); });
}

/* ── Begin online game ── */
function beginGame(gid,color,pid){
  onGid=gid; myCol=color; myPid=pid;
  onGame=new Chess(); onActive=true; onMoves=[];
  cwW=600; cwB=600;

  document.getElementById('find-btn').disabled=false;
  document.getElementById('searching').classList.remove('on');
  document.getElementById('lobby-card').style.display='none';
  ['on-ctrl','on-hist','on-chat-card'].forEach(id=>document.getElementById(id).style.display='block');

  let isW=color==='w';
  document.getElementById('opp-strip').style.display='flex';
  document.getElementById('my-strip').style.display='flex';
  document.getElementById('opp-ico').textContent=isW?'♚':'♔';
  document.getElementById('my-ico').textContent=isW?'♔':'♚';
  document.getElementById('my-ctag').textContent=isW?'WHITE':'BLACK';

  onB.orientation(color==='w'?'white':'black');
  onB.position('start');
  clrHL(onB);
  document.getElementById('on-res').classList.remove('on');
  document.getElementById('dtost').classList.remove('on');
  document.getElementById('on-ml').innerHTML='<span style="color:var(--dim)">No moves yet</span>';
  document.getElementById('chatbox').innerHTML='';
  addChat('sys','Game started — you play '+(color==='w'?'White':'Black'));
  setSbar('on','Game started — '+(color==='w'?'White':'Black')+' to move');
  updateStrips();
  startClock();
  startPoll();
}

/* ── Drag & Drop ── */
function onDragS(src,piece){
  if(!onActive||onGame.game_over()) return false;
  if(onGame.turn()!==myCol) return false;
  if(myCol==='w'&&/^b/.test(piece)) return false;
  if(myCol==='b'&&/^w/.test(piece)) return false;
}
function onDrop(src,tgt){
  if(isPromo(onGame,src,tgt)){
    pendOn={from:src,to:tgt};
    document.getElementById('promo-ov').classList.add('on');
    return 'snapback';
  }
  let mv=onGame.move({from:src,to:tgt,promotion:'q'});
  if(!mv) return 'snapback';
  afterOnMove(mv);
}
function isPromo(g,f,t){
  let p=g.get(f); if(!p||p.type!=='p') return false;
  return(p.color==='w'&&t[1]==='8')||(p.color==='b'&&t[1]==='1');
}
function doPromo(pc){
  document.getElementById('promo-ov').classList.remove('on');
  if(pendOn){
    let mv=onGame.move({from:pendOn.from,to:pendOn.to,promotion:pc});
    pendOn=null; if(mv){onB.position(onGame.fen());afterOnMove(mv);}
  } else if(pendAI){
    let mv=aiGame.move({from:pendAI.from,to:pendAI.to,promotion:pc});
    pendAI=null; if(mv){aiB.position(aiGame.fen());afterAIPlayer(mv);}
  }
}

function afterOnMove(mv){
  onMoves.push({san:mv.san,color:mv.color});
  clrHL(onB); hlSq(onB,mv.from,mv.to);
  updateOnML(); updateStrips();
  let status='active', result=null;
  if(onGame.in_checkmate()){
    status='checkmate';
    result=(onGame.turn()==='b'?'White':'Black')+' wins by checkmate';
  } else if(onGame.game_over()){
    status='draw'; result='½–½ Draw';
  }
  fetch('/api/move',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      gid:onGid,pid:myPid,
      uci:mv.from+mv.to+(mv.promotion||''),
      san:mv.san,fen:onGame.fen(),status,result
    })
  });
  if(status!=='active') endOnGame(result);
  else setSbar('on','Waiting for opponent…');
}

/* ── Long-poll loop ── */
function startPoll(){
  if(polling) return;
  polling=true;
  function poll(){
    if(!onGid){polling=false;return;}
    fetch('/api/poll',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({gid:onGid,pid:myPid})
    })
    .then(r=>r.json())
    .then(d=>{
      (d.events||[]).forEach(handleEv);
      if(onGid) setTimeout(poll,80); else polling=false;
    })
    .catch(()=>{ if(onGid) setTimeout(poll,2500); else polling=false; });
  }
  poll();
}
function handleEv(ev){
  if(ev.type==='move'){
    onGame=new Chess(ev.fen);
    onB.position(ev.fen);
    if(ev.uci&&ev.uci.length>=4) hlSq(onB,ev.uci.slice(0,2),ev.uci.slice(2,4));
    onMoves.push({san:ev.san,color:myCol==='w'?'b':'w'});
    updateOnML(); updateStrips();
    setSbar('on','Your turn');
    if(ev.status==='checkmate'||ev.status==='draw') endOnGame(ev.result);
  }
  else if(ev.type==='end')         endOnGame(ev.result);
  else if(ev.type==='draw_offer')  document.getElementById('dtost').classList.add('on');
  else if(ev.type==='draw_declined') setSbar('on','Draw declined — game continues','amber');
  else if(ev.type==='abandoned')   endOnGame('Opponent disconnected');
  else if(ev.type==='chat')        addChat('opp',ev.msg);
}

/* ── End game ── */
function endOnGame(result){
  onActive=false; stopClock();
  document.getElementById('on-res').classList.add('on');
  document.getElementById('on-res-t').textContent=result||'Game Over';
  document.getElementById('on-res-s').textContent='Click "New Match" to play again';
  setSbar('on',result||'Game over');
}

/* ── Clocks ── */
function startClock(){
  if(cwTimer) clearInterval(cwTimer);
  cwTimer=setInterval(()=>{
    if(!onActive) return;
    if(onGame.turn()==='w') cwW=Math.max(0,cwW-1);
    else cwB=Math.max(0,cwB-1);
    renderClocks();
    if(cwW===0||cwB===0) endOnGame((cwW===0?'Black':'White')+' wins on time');
  },1000);
}
function stopClock(){if(cwTimer){clearInterval(cwTimer);cwTimer=null;}}
function fmt(s){return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');}
function renderClocks(){
  let isW=myCol==='w';
  document.getElementById('my-clk').textContent  =fmt(isW?cwW:cwB);
  document.getElementById('opp-clk').textContent =fmt(isW?cwB:cwW);
  document.getElementById('my-clk').classList.toggle('low',(isW?cwW:cwB)<30);
}
function updateStrips(){
  let wt=onGame.turn()==='w', isW=myCol==='w';
  document.getElementById('my-strip').classList.toggle('active',(isW&&wt)||(!isW&&!wt));
  document.getElementById('opp-strip').classList.toggle('active',(isW&&!wt)||(!isW&&wt));
}

/* ── Online helpers ── */
function updateOnML(){
  if(!onMoves.length){
    document.getElementById('on-ml').innerHTML='<span style="color:var(--dim)">No moves yet</span>';
    return;
  }
  let s='';
  for(let i=0;i<onMoves.length;i+=2){
    s+='<div class="mp"><span class="mn">'+(Math.floor(i/2)+1)+'.</span>';
    s+='<span class="mv">'+onMoves[i].san+'</span>';
    if(onMoves[i+1]) s+='<span class="mv">'+onMoves[i+1].san+'</span>';
    s+='</div>';
  }
  let el=document.getElementById('on-ml');
  el.innerHTML=s; el.scrollTop=el.scrollHeight;
}
function resetOnline(){
  onActive=false; onGid=null; myCol=null; polling=false;
  stopClock(); onMoves=[];
  document.getElementById('lobby-card').style.display='block';
  ['on-ctrl','on-hist','on-chat-card'].forEach(id=>document.getElementById(id).style.display='none');
  document.getElementById('opp-strip').style.display='none';
  document.getElementById('my-strip').style.display='none';
  document.getElementById('on-res').classList.remove('on');
  document.getElementById('dtost').classList.remove('on');
  document.getElementById('find-btn').disabled=false;
  document.getElementById('searching').classList.remove('on');
  document.getElementById('srch-txt').textContent='Searching for opponent…';
  onB.position('start'); clrHL(onB);
  setSbar('on','Click ⚡ Find Match to be paired with a random opponent instantly');
}
function offerDraw(){
  doAction({action:'draw_offer'});
  setSbar('on','Draw offer sent — waiting for response…','amber');
}
function acceptDraw(){
  document.getElementById('dtost').classList.remove('on');
  doAction({action:'draw_accept'});
}
function declineDraw(){
  document.getElementById('dtost').classList.remove('on');
  doAction({action:'draw_decline'});
}
function resignOnline(){ if(!onActive) return; doAction({action:'resign'}); }
function doAction(extra){
  fetch('/api/action',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({gid:onGid,pid:myPid,...extra})
  });
}
function addChat(type,msg){
  let el=document.getElementById('chatbox');
  let d=document.createElement('div');
  d.className='cm '+type;
  d.textContent=(type==='me'?'You: ':type==='opp'?'Opp: ':'')+msg;
  el.appendChild(d); el.scrollTop=el.scrollHeight;
}
function sendChat(){
  let inp=document.getElementById('chat-inp');
  let m=inp.value.trim(); if(!m) return;
  addChat('me',m); inp.value='';
  doAction({action:'chat',msg:m});
}
function cpyOnPgn(){
  let g=new Chess();
  onMoves.forEach(m=>{try{g.move(m.san);}catch(e){}});
  navigator.clipboard.writeText(g.pgn()).then(()=>{
    let b=event.target; b.textContent='✓'; setTimeout(()=>b.textContent='📋 PGN',1500);
  });
}
function onToReview(){
  let g=new Chess();
  onMoves.forEach(m=>{try{g.move(m.san);}catch(e){}});
  let pgn=g.pgn(); if(!pgn) return;
  document.getElementById('pgn-in').value=pgn;
  goPage('rv'); loadRv();
}

/* ══════════════════════════════════════════════════════════
   AI GAME  — vs Stockfish, selectable level
══════════════════════════════════════════════════════════ */
let aiGame=new Chess(), aiB=null;
let aiCol='w', aiActive=false, aiThinking=false;

$(document).ready(function(){
  aiB=Chessboard('ai-board',{
    draggable:true, position:'start',
    onDragStart:aiDragS, onDrop:aiDropF,
    onSnapEnd:()=>aiB.position(aiGame.fen()),
    pieceTheme:'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
});

function pickC(c){
  aiCol=c;
  document.getElementById('pw').classList.toggle('on',c==='w');
  document.getElementById('pb').classList.toggle('on',c==='b');
}
function startAI(){
  aiGame=new Chess(); aiActive=true; aiThinking=false;
  aiB.orientation(aiCol==='w'?'white':'black');
  aiB.position('start'); clrHL(aiB);
  document.getElementById('ai-ml').innerHTML='<span style="color:var(--dim)">No moves yet</span>';
  document.getElementById('ai-res').disabled=false;
  document.getElementById('ai-ec').style.display='block';
  setEB('<span style="color:var(--dim)">Ready</span>');
  setSbar('ai','You play '+(aiCol==='w'?'White':'Black')+
    ' vs Stockfish Level '+curLv+' — '+LV[curLv].n+' ('+LV[curLv].e+' Elo)');
  if(aiGame.turn()!==aiCol) setTimeout(doAIMove,400);
}
function aiDragS(src,piece){
  if(!aiActive||aiGame.game_over()||aiThinking) return false;
  if(aiGame.turn()!==aiCol) return false;
  if(aiCol==='w'&&/^b/.test(piece)) return false;
  if(aiCol==='b'&&/^w/.test(piece)) return false;
}
function aiDropF(src,tgt){
  if(isPromo(aiGame,src,tgt)){
    pendAI={from:src,to:tgt};
    document.getElementById('promo-ov').classList.add('on');
    return 'snapback';
  }
  let mv=aiGame.move({from:src,to:tgt,promotion:'q'});
  if(!mv) return 'snapback';
  afterAIPlayer(mv);
}
function afterAIPlayer(mv){
  clrHL(aiB); hlSq(aiB,mv.from,mv.to);
  updateAIML(); if(checkAIOver()) return;
  setTimeout(doAIMove,130);
}
function doAIMove(){
  if(!aiActive||aiGame.game_over()) return;
  aiThinking=true;
  setEB('<div class="spin"></div><span>Level '+curLv+' — '+LV[curLv].n+' thinking…</span>');
  sfBestMove(aiGame.fen(),curLv,bm=>{
    aiThinking=false;
    if(!bm||!aiActive){setEB('<span style="color:var(--dim)">—</span>');return;}
    let mv=aiGame.move({from:bm.slice(0,2),to:bm.slice(2,4),promotion:bm[4]||'q'});
    if(!mv){setEB('<span style="color:var(--dim)">—</span>');return;}
    aiB.position(aiGame.fen()); clrHL(aiB); hlSq(aiB,mv.from,mv.to);
    updateAIML();
    setEB('<span>Played <b style="color:var(--amber)">'+mv.san+'</b>  ·  Level '+curLv+' '+LV[curLv].n+'</span>');
    checkAIOver();
  });
}
function setEB(h){document.getElementById('ai-eb').innerHTML=h;}
function checkAIOver(){
  if(!aiGame.game_over()) return false;
  aiActive=false;
  document.getElementById('ai-res').disabled=true;
  let m=aiGame.in_checkmate()?'♛ Checkmate! '+(aiGame.turn()==='b'?'White':'Black')+' wins.':
        aiGame.in_stalemate()?'½ Stalemate':
        aiGame.in_threefold_repetition()?'½ Threefold repetition':
        aiGame.insufficient_material()?'½ Insufficient material':'½ Draw';
  setSbar('ai',m);
  setEB('<span style="color:var(--sage)">'+m+'</span>');
  return true;
}
function updateAIML(){
  let h=aiGame.history();
  if(!h.length){document.getElementById('ai-ml').innerHTML='<span style="color:var(--dim)">No moves yet</span>';return;}
  let s='';
  for(let i=0;i<h.length;i+=2){
    s+='<div class="mp"><span class="mn">'+(Math.floor(i/2)+1)+'.</span>';
    s+='<span class="mv">'+h[i]+'</span>';
    if(h[i+1]) s+='<span class="mv">'+h[i+1]+'</span>';
    s+='</div>';
  }
  let el=document.getElementById('ai-ml');
  el.innerHTML=s; el.scrollTop=el.scrollHeight;
}
function undoAI(){
  if(!aiActive) return;
  aiGame.undo(); aiGame.undo();
  aiB.position(aiGame.fen()); clrHL(aiB); updateAIML();
}
function flipAI(){aiB.flip();}
function resignAI(){
  if(!aiActive) return;
  aiActive=false;
  document.getElementById('ai-res').disabled=true;
  setSbar('ai','You resigned.');
  setEB('<span style="color:var(--rose)">Resigned.</span>');
}
function loadFen(){
  let f=document.getElementById('ai-fen').value.trim(); if(!f) return;
  let t=new Chess(); if(!t.load(f)){alert('Invalid FEN!');return;}
  aiGame=t; aiActive=false;
  aiB.position(f); clrHL(aiB); updateAIML();
  setSbar('ai','Position loaded. Press ▶ Start to play.');
}
function cpyFen(){
  navigator.clipboard.writeText(aiGame.fen()).then(()=>{
    let b=event.target; b.textContent='✓'; setTimeout(()=>b.textContent='Copy FEN',1400);
  });
}
function cpyAIPgn(){
  navigator.clipboard.writeText(aiGame.pgn()).then(()=>{
    let b=event.target; b.textContent='✓'; setTimeout(()=>b.textContent='📋 PGN',1400);
  });
}
function aiToReview(){
  let pgn=aiGame.pgn(); if(!pgn) return;
  document.getElementById('pgn-in').value=pgn;
  goPage('rv'); loadRv();
}

/* ══════════════════════════════════════════════════════════
   GAME REVIEW  — Stockfish Level 20 (maximum)
══════════════════════════════════════════════════════════ */
let rvB=null, rvSt=[], rvEv=[], rvIdx=0, rvAna=false;

function initRvBoard(){
  rvB=Chessboard('rv-board',{
    draggable:false, position:'start',
    pieceTheme:'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
}

function loadSample(){
  document.getElementById('pgn-in').value=
`[Event "The Immortal Game"]
[White "Adolf Anderssen"]
[Black "Lionel Kieseritzky"]
[Result "1-0"]

1. e4 e5 2. f4 exf4 3. Bc4 Qh4+ 4. Kf1 b5 5. Bxb5 Nf6 6. Nf3 Qh6 7. d3 Nh5
8. Nh4 Qg5 9. Nf5 c6 10. g4 Nf6 11. Rg1 cxb5 12. h4 Qg6 13. h5 Qg5 14. Qf3 Ng8
15. Bxf4 Qf6 16. Nc3 Bc5 17. Nd5 Qxb2 18. Bd6 Bxg1 19. e5 Qxa1+ 20. Ke2 Na6
21. Nxg7+ Kd8 22. Qf6+ Nxf6 23. Be7# 1-0`;
  loadRv();
}

function loadRv(){
  let pgn=document.getElementById('pgn-in').value.trim();
  if(!pgn) return;
  let tmp=new Chess();
  if(!tmp.load_pgn(pgn)){alert('Invalid PGN!');return;}
  let hist=tmp.history({verbose:true}), g2=new Chess();
  rvSt=[{fen:g2.fen(),san:null,color:null,moveNum:0,ann:null}];
  hist.forEach((m,i)=>{
    g2.move(m.san);
    rvSt.push({fen:g2.fen(),san:m.san,color:m.color,moveNum:Math.floor(i/2)+1,ann:null});
  });
  rvEv=new Array(rvSt.length).fill(null);
  document.getElementById('acc-card').style.display='none';
  rvGo(0); renderRvML(); runAnalysis();
}

function runAnalysis(){
  if(rvAna) return;
  rvAna=true;
  let depth=parseInt(document.getElementById('rv-dep').value);
  let tot=rvSt.length;
  let pw=document.getElementById('rv-prog');
  let pf=document.getElementById('pf'), pl=document.getElementById('pl');
  pw.style.display='block';
  let i=0;
  function step(){
    if(i>=tot){
      rvAna=false; pw.style.display='none';
      computeAcc(); renderRvML(); updateEvBar(); return;
    }
    pl.textContent='Analysing move '+i+' / '+(tot-1)+'…';
    pf.style.width=(i/(tot-1)*100)+'%';
    sfEval(rvSt[i].fen, depth, sc=>{
      let g=new Chess(rvSt[i].fen);
      rvEv[i]=g.turn()==='w'?sc:-sc;   // normalise → white POV
      if(i===rvIdx) updateEvBar();
      i++; step();
    });
  }
  step();
}

function cpToWP(cp){ return 1/(1+Math.exp(-0.004*cp)); }

function computeAcc(){
  let wA=[],bA=[],wB=0,wM=0,wI=0,bB=0,bM=0,bI=0;
  for(let i=1;i<rvSt.length;i++){
    let bef=rvEv[i-1], aft=rvEv[i];
    if(bef===null||aft===null) continue;
    let col=rvSt[i].color;
    let wpB=col==='w'?cpToWP(bef):cpToWP(-bef);
    let wpA=col==='w'?cpToWP(aft):cpToWP(-aft);
    let loss=Math.max(0,wpB-wpA);
    let acc=Math.max(0,100-150*loss);
    let ann=loss>0.20?'blunder':loss>0.10?'mistake':loss>0.05?'inaccuracy':loss>0.02?'good':'best';
    rvSt[i].ann=ann; rvSt[i].acc=acc;
    if(col==='w'){
      wA.push(acc);
      if(ann==='blunder')wB++; else if(ann==='mistake')wM++; else if(ann==='inaccuracy')wI++;
    } else {
      bA.push(acc);
      if(ann==='blunder')bB++; else if(ann==='mistake')bM++; else if(ann==='inaccuracy')bI++;
    }
  }
  let avgW=wA.length?Math.round(wA.reduce((a,b)=>a+b,0)/wA.length):0;
  let avgB=bA.length?Math.round(bA.reduce((a,b)=>a+b,0)/bA.length):0;
  document.getElementById('acc-w').textContent=avgW+'%';
  document.getElementById('acc-b').textContent=avgB+'%';
  document.getElementById('acc-card').style.display='block';
  document.getElementById('erw').innerHTML=
    `<div class="ep epb">?? ${wB} Blunders</div><div class="ep epm">? ${wM} Mistakes</div><div class="ep epi">⁈ ${wI} Inaccuracies</div>`;
  document.getElementById('erb').innerHTML=
    `<div class="ep epb">?? ${bB} Blunders</div><div class="ep epm">? ${bM} Mistakes</div><div class="ep epi">⁈ ${bI} Inaccuracies</div>`;
}

function annBadge(ann){
  if(!ann||ann==='best') return '';
  if(ann==='blunder')    return '<span class="ann abl">?!</span>';
  if(ann==='mistake')    return '<span class="ann ams">?</span>';
  if(ann==='inaccuracy') return '<span class="ann ain">⁈</span>';
  if(ann==='good')       return '<span class="ann agd">!</span>';
  return '';
}

function renderRvML(){
  if(!rvSt.length) return;
  let s='';
  for(let i=1;i<rvSt.length;i++){
    let st=rvSt[i];
    if(st.color==='w') s+='<span class="rn">'+st.moveNum+'.</span>';
    s+='<span class="rm'+(i===rvIdx?' on':'')+'" id="rm'+i+'" onclick="rvGo('+i+')">'+
       st.san+annBadge(st.ann)+'</span> ';
    if(st.color==='b') s+='<br>';
  }
  document.getElementById('rv-ml').innerHTML=s||'<span style="color:var(--dim)">No game loaded</span>';
}

function rvGo(idx){
  if(!rvSt.length) return;
  rvIdx=Math.max(0,Math.min(idx,rvSt.length-1));
  let st=rvSt[rvIdx];
  rvB.position(st.fen);
  document.getElementById('rvctr').textContent=rvIdx+'/'+(rvSt.length-1);
  let who=st.color==='w'?'White':st.color==='b'?'Black':'';
  let desc=rvIdx===0?'Starting position':
    'Move '+st.moveNum+' — '+who+' played '+st.san+
    (st.ann&&st.ann!=='best'?'  ['+st.ann+']':'');
  setSbar('rv',desc);
  updateEvBar();
  document.querySelectorAll('.rm').forEach(e=>e.classList.remove('on'));
  let el=document.getElementById('rm'+rvIdx);
  if(el){el.classList.add('on');el.scrollIntoView({block:'nearest'});}
}

function updateEvBar(){
  let sc=rvEv[rvIdx];
  if(sc===null){document.getElementById('ev-num').textContent='…';return;}
  let cap=Math.max(-1000,Math.min(1000,sc));
  let pct=Math.max(4,Math.min(96,50+cap/20));
  document.getElementById('ev-bar').style.height=pct+'%';
  let txt=sc>=30000?'M+':sc<=-30000?'M−':(sc>0?'+':'')+(sc/100).toFixed(2);
  document.getElementById('ev-num').textContent=txt;
}

function rvNext(){rvGo(rvIdx+1);}
function rvPrev(){rvGo(rvIdx-1);}
function rvLast(){rvGo(rvSt.length-1);}

document.addEventListener('keydown',e=>{
  if(!document.getElementById('pg-rv').classList.contains('on')) return;
  if(e.key==='ArrowRight') rvNext();
  if(e.key==='ArrowLeft')  rvPrev();
  if(e.key==='Home') rvGo(0);
  if(e.key==='End')  rvLast();
});

/* ══════════════════════════════════════════════════════════
   SHARED HELPERS
══════════════════════════════════════════════════════════ */
function setSbar(pg,msg,cls=''){
  let map={on:'on-sb',ai:'ai-sb',rv:'rv-sb'};
  let el=document.getElementById(map[pg]); if(!el) return;
  el.className='sbar'+(cls?' '+cls:'');
  el.textContent=msg;
}
function hlSq(bd,f,t){
  document.querySelectorAll('.square-'+f+',.square-'+t)
    .forEach((e,i)=>e.classList.add(i===0?'hf':'ht'));
}
function clrHL(){
  document.querySelectorAll('.hf,.ht').forEach(e=>e.classList.remove('hf','ht'));
}
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"""
╔══════════════════════════════════════════════════════════╗
║            GRANDMASTER CHESS  —  Full Platform           ║
╠══════════════════════════════════════════════════════════╣
║  Open → http://localhost:{port:<29}   ║
╠══════════════════════════════════════════════════════════╣
║  🌐  ONLINE MULTIPLAYER                                  ║
║      Both players open the same URL                      ║
║      → click ⚡ FIND OPPONENT                            ║
║      → auto-paired instantly (random colours)            ║
║      10-min clocks · Draw offers · Chat · Resign         ║
║      "→ Review" sends any finished game to analysis      ║
║                                                          ║
║  🤖  vs STOCKFISH AI  (Levels 1–20)                     ║
║      Level 1  ~400 Elo   Total Beginner                  ║
║      Level 10 ~1600 Elo  Intermediate                    ║
║      Level 20 ~3200 Elo  Super-GM (greatest)             ║
║      Undo · Load FEN · Export PGN                        ║
║                                                          ║
║  🔍  GAME REVIEW  (Stockfish Level 20 analysis)          ║
║      Paste any PGN → full engine analysis                ║
║      Eval bar · Accuracy % · Blunder/Mistake/Inaccuracy  ║
║      ← → arrow keys to navigate                         ║
╠══════════════════════════════════════════════════════════╣
║  Online between two devices on same network:             ║
║      Both open http://YOUR_LOCAL_IP:{port:<20}║
╚══════════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
