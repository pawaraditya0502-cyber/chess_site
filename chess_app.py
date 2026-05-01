"""
Chess Learning Platform
Run with: pip install flask && python chess_app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChessMaster — Learn & Play</title>

<!-- Chess libraries -->
<link rel="stylesheet"
  href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Code+Pro:wght@400;600&family=Lato:wght@300;400;700&display=swap');

  :root {
    --bg:        #0d0f0e;
    --panel:     #141817;
    --border:    #2a2f2c;
    --accent:    #c8a96e;
    --accent2:   #5e9e6e;
    --text:      #e8e4dc;
    --muted:     #7a8078;
    --danger:    #c06060;
    --light-sq:  #f0d9b5;
    --dark-sq:   #b58863;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Lato', sans-serif;
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 40px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .logo {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem; font-weight: 900;
    color: var(--accent);
    letter-spacing: 2px;
  }
  .logo span { color: var(--accent2); }
  nav { display: flex; gap: 6px; }
  .nav-btn {
    padding: 8px 20px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--muted);
    font-family: 'Lato', sans-serif;
    font-size: 0.85rem; letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer; border-radius: 3px;
    transition: all .2s;
  }
  .nav-btn:hover, .nav-btn.active {
    background: var(--accent);
    color: var(--bg);
    border-color: var(--accent);
  }

  /* ── Views ── */
  .view { display: none; padding: 30px 40px; }
  .view.active { display: block; }

  /* ── Layout grid ── */
  .board-layout {
    display: grid;
    grid-template-columns: 480px 1fr;
    gap: 30px;
    align-items: start;
  }

  /* ── Board wrapper ── */
  .board-wrap {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px;
  }
  #board, #review-board { width: 440px; }

  /* ── Side panel ── */
  .side-panel {
    display: flex; flex-direction: column; gap: 16px;
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px;
  }
  .card h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem; color: var(--accent);
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }

  /* ── Status / info ── */
  #status-bar {
    font-family: 'Source Code Pro', monospace;
    font-size: 0.85rem; color: var(--accent2);
    padding: 10px 14px;
    background: rgba(94,158,110,0.08);
    border: 1px solid rgba(94,158,110,0.2);
    border-radius: 4px;
    margin-bottom: 14px;
  }

  /* ── Move history ── */
  #move-list {
    font-family: 'Source Code Pro', monospace;
    font-size: 0.82rem;
    max-height: 260px; overflow-y: auto;
    line-height: 1.8;
    color: var(--muted);
  }
  #move-list span { color: var(--text); }
  #move-list .move-pair { display: flex; gap: 8px; margin-bottom: 2px; }
  #move-list .mn { color: var(--accent); min-width: 28px; }

  /* ── Buttons ── */
  .btn-row { display: flex; gap: 10px; flex-wrap: wrap; }
  .btn {
    padding: 9px 18px;
    border-radius: 4px;
    font-family: 'Lato', sans-serif;
    font-size: 0.83rem; font-weight: 700;
    letter-spacing: .8px; text-transform: uppercase;
    cursor: pointer; border: none; transition: all .18s;
  }
  .btn-primary { background: var(--accent); color: var(--bg); }
  .btn-primary:hover { background: #dfc080; }
  .btn-secondary { background: var(--border); color: var(--text); }
  .btn-secondary:hover { background: #3a3f3c; }
  .btn-danger { background: var(--danger); color: #fff; }
  .btn-danger:hover { background: #d07070; }
  .btn-green { background: var(--accent2); color: #fff; }
  .btn-green:hover { background: #6eb07e; }

  /* ── Promotion modal ── */
  .modal-overlay {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,.75); z-index: 100;
    align-items: center; justify-content: center;
  }
  .modal-overlay.open { display: flex; }
  .modal {
    background: var(--panel);
    border: 1px solid var(--accent);
    border-radius: 8px; padding: 30px;
    text-align: center;
  }
  .modal h3 { font-family: 'Playfair Display', serif; color: var(--accent); margin-bottom: 18px; }
  .promo-btns { display: flex; gap: 12px; justify-content: center; }
  .promo-btn {
    font-size: 2rem; cursor: pointer;
    padding: 10px 16px;
    border: 1px solid var(--border);
    background: var(--bg); border-radius: 4px;
    transition: all .15s;
  }
  .promo-btn:hover { border-color: var(--accent); background: #1f2420; }

  /* ── FEN input ── */
  input[type=text] {
    width: 100%; padding: 9px 12px;
    background: var(--bg); color: var(--text);
    border: 1px solid var(--border); border-radius: 4px;
    font-family: 'Source Code Pro', monospace; font-size: 0.82rem;
    outline: none; transition: border .2s;
  }
  input[type=text]:focus { border-color: var(--accent); }

  /* ── Review controls ── */
  #pgn-input {
    width: 100%; height: 90px;
    background: var(--bg); color: var(--text);
    border: 1px solid var(--border); border-radius: 4px;
    padding: 10px 12px;
    font-family: 'Source Code Pro', monospace; font-size: 0.8rem;
    outline: none; resize: vertical; transition: border .2s;
  }
  #pgn-input:focus { border-color: var(--accent); }

  .review-nav { display: flex; gap: 8px; align-items: center; }
  .review-nav .btn { padding: 8px 14px; font-size: 1rem; }
  #move-counter {
    font-family: 'Source Code Pro', monospace;
    font-size: 0.85rem; color: var(--accent);
    min-width: 70px; text-align: center;
  }

  /* ── Review move list ── */
  #review-moves {
    font-family: 'Source Code Pro', monospace;
    font-size: 0.82rem;
    max-height: 200px; overflow-y: auto;
    color: var(--muted); line-height: 1.9;
  }
  .rmove {
    display: inline-block; padding: 1px 6px;
    border-radius: 3px; cursor: pointer;
    transition: background .12s;
  }
  .rmove:hover { background: var(--border); color: var(--text); }
  .rmove.current { background: var(--accent); color: var(--bg); }

  /* ── Learn page ── */
  .learn-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 10px;
  }
  .topic-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px; padding: 24px;
    cursor: pointer; transition: all .2s;
    position: relative; overflow: hidden;
  }
  .topic-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent);
    transform: scaleX(0); transition: transform .2s;
    transform-origin: left;
  }
  .topic-card:hover { border-color: var(--accent); transform: translateY(-2px); }
  .topic-card:hover::before { transform: scaleX(1); }
  .topic-icon { font-size: 2.2rem; margin-bottom: 12px; }
  .topic-card h3 {
    font-family: 'Playfair Display', serif;
    color: var(--accent); font-size: 1.1rem; margin-bottom: 8px;
  }
  .topic-card p { color: var(--muted); font-size: 0.88rem; line-height: 1.6; }

  /* ── Article modal ── */
  #article-modal .modal { max-width: 680px; width: 90%; text-align: left; max-height: 80vh; overflow-y: auto; }
  #article-modal .modal h2 {
    font-family: 'Playfair Display', serif;
    color: var(--accent); font-size: 1.5rem; margin-bottom: 16px;
  }
  #article-modal .modal p { color: var(--text); font-size: 0.92rem; line-height: 1.8; margin-bottom: 14px; }
  #article-modal .modal ul { padding-left: 20px; color: var(--text); font-size: 0.9rem; line-height: 2; }
  #article-modal .modal .close-btn {
    float: right; cursor: pointer;
    color: var(--muted); font-size: 1.4rem; line-height: 1;
  }
  #article-modal .modal .close-btn:hover { color: var(--accent); }

  /* ── Page title ── */
  .page-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem; color: var(--text);
    margin-bottom: 24px; font-weight: 700;
  }
  .page-title span { color: var(--accent); }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<header>
  <div class="logo">Chess<span>Master</span></div>
  <nav>
    <button class="nav-btn active" onclick="showView('play')">♟ Play</button>
    <button class="nav-btn"        onclick="showView('review')">🔍 Review</button>
    <button class="nav-btn"        onclick="showView('learn')">📚 Learn</button>
  </nav>
</header>

<!-- ═══════════════ PLAY VIEW ═══════════════ -->
<div id="view-play" class="view active">
  <div class="board-layout">
    <div class="board-wrap">
      <div id="status-bar">White to move</div>
      <div id="board"></div>
    </div>
    <div class="side-panel">
      <div class="card">
        <h3>Game Controls</h3>
        <div class="btn-row">
          <button class="btn btn-primary"   onclick="newGame()">New Game</button>
          <button class="btn btn-secondary" onclick="undoMove()">↩ Undo</button>
          <button class="btn btn-secondary" onclick="flipBoard()">⇅ Flip</button>
          <button class="btn btn-danger"    onclick="resignGame()">Resign</button>
        </div>
      </div>

      <div class="card">
        <h3>Set Position (FEN)</h3>
        <input type="text" id="fen-input" placeholder="Paste FEN string…">
        <div class="btn-row" style="margin-top:10px">
          <button class="btn btn-green" onclick="loadFen()">Load FEN</button>
          <button class="btn btn-secondary" onclick="copyFen()">Copy FEN</button>
        </div>
      </div>

      <div class="card">
        <h3>Move History</h3>
        <div id="move-list"><span style="color:var(--muted)">No moves yet…</span></div>
      </div>

      <div class="card">
        <h3>Export PGN</h3>
        <button class="btn btn-secondary" onclick="copyPgn()">📋 Copy PGN</button>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════ REVIEW VIEW ═══════════════ -->
<div id="view-review" class="view">
  <div class="board-layout">
    <div class="board-wrap">
      <div id="review-status" style="font-family:'Source Code Pro',monospace;font-size:.85rem;color:var(--accent2);padding:10px 14px;background:rgba(94,158,110,.08);border:1px solid rgba(94,158,110,.2);border-radius:4px;margin-bottom:14px;">
        Load a PGN to start reviewing
      </div>
      <div id="review-board"></div>
    </div>
    <div class="side-panel">
      <div class="card">
        <h3>Load PGN</h3>
        <textarea id="pgn-input" placeholder="Paste PGN here…"></textarea>
        <div class="btn-row" style="margin-top:10px">
          <button class="btn btn-primary" onclick="loadPgn()">Load Game</button>
          <button class="btn btn-secondary" onclick="loadSamplePgn()">Load Sample</button>
        </div>
      </div>

      <div class="card">
        <h3>Navigation</h3>
        <div class="review-nav">
          <button class="btn btn-secondary" onclick="reviewGo(0)">⏮</button>
          <button class="btn btn-secondary" onclick="reviewPrev()">◀</button>
          <span id="move-counter">0 / 0</span>
          <button class="btn btn-secondary" onclick="reviewNext()">▶</button>
          <button class="btn btn-secondary" onclick="reviewGoLast()">⏭</button>
        </div>
      </div>

      <div class="card">
        <h3>Moves</h3>
        <div id="review-moves"><span style="color:var(--muted)">No game loaded…</span></div>
      </div>

      <div class="card">
        <h3>Position FEN</h3>
        <input type="text" id="review-fen" readonly style="cursor:pointer" onclick="this.select()" placeholder="—">
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════ LEARN VIEW ═══════════════ -->
<div id="view-learn" class="view">
  <div class="page-title">Chess <span>Academy</span></div>
  <div class="learn-grid" id="learn-grid"></div>
</div>

<!-- Promotion modal -->
<div class="modal-overlay" id="promo-modal">
  <div class="modal">
    <h3>Choose Promotion Piece</h3>
    <div class="promo-btns">
      <div class="promo-btn" onclick="promote('q')">♛</div>
      <div class="promo-btn" onclick="promote('r')">♜</div>
      <div class="promo-btn" onclick="promote('b')">♝</div>
      <div class="promo-btn" onclick="promote('n')">♞</div>
    </div>
  </div>
</div>

<!-- Article modal -->
<div class="modal-overlay" id="article-modal">
  <div class="modal">
    <span class="close-btn" onclick="closeArticle()">✕</span>
    <h2 id="article-title"></h2>
    <div id="article-body"></div>
  </div>
</div>

<script>
/* ═══════════════════════════════════════════
   NAV
═══════════════════════════════════════════ */
function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  event.target.classList.add('active');

  if (name === 'review' && !reviewBoard) initReviewBoard();
  if (name === 'learn') renderLearnCards();
}

/* ═══════════════════════════════════════════
   PLAY
═══════════════════════════════════════════ */
let game = new Chess();
let board = null;
let pendingPromo = null;
let gameOver = false;

function onDragStart(source, piece) {
  if (gameOver) return false;
  if (game.game_over()) return false;
  if (piece.search(/^b/) !== -1 && game.turn() === 'w') return false;
  if (piece.search(/^w/) !== -1 && game.turn() === 'b') return false;
}

function onDrop(source, target) {
  if (isPromotion(source, target)) {
    pendingPromo = { from: source, to: target };
    document.getElementById('promo-modal').classList.add('open');
    return 'snapback';
  }
  let move = game.move({ from: source, to: target, promotion: 'q' });
  if (!move) return 'snapback';
  afterMove();
}

function isPromotion(from, to) {
  let piece = game.get(from);
  if (!piece || piece.type !== 'p') return false;
  if (piece.color === 'w' && to[1] === '8') return true;
  if (piece.color === 'b' && to[1] === '1') return true;
  return false;
}

function promote(piece) {
  document.getElementById('promo-modal').classList.remove('open');
  if (!pendingPromo) return;
  let move = game.move({ from: pendingPromo.from, to: pendingPromo.to, promotion: piece });
  pendingPromo = null;
  if (!move) return;
  board.position(game.fen());
  afterMove();
}

function afterMove() {
  board.position(game.fen());
  updateStatus();
  updateMoveList();
  document.getElementById('fen-input').value = '';
}

function updateStatus() {
  let s = '';
  if (game.in_checkmate()) {
    let winner = game.turn() === 'b' ? 'White' : 'Black';
    s = '♛ Checkmate! ' + winner + ' wins.';
    gameOver = true;
  } else if (game.in_stalemate()) {
    s = '½ Stalemate — Draw!'; gameOver = true;
  } else if (game.in_draw()) {
    s = '½ Draw!'; gameOver = true;
  } else if (game.in_check()) {
    s = (game.turn() === 'w' ? 'White' : 'Black') + ' is in check!';
  } else {
    s = (game.turn() === 'w' ? 'White' : 'Black') + ' to move';
  }
  document.getElementById('status-bar').textContent = s;
}

function updateMoveList() {
  let history = game.history();
  if (!history.length) {
    document.getElementById('move-list').innerHTML = '<span style="color:var(--muted)">No moves yet…</span>';
    return;
  }
  let html = '';
  for (let i = 0; i < history.length; i += 2) {
    html += '<div class="move-pair"><span class="mn">' + (Math.floor(i/2)+1) + '.</span>';
    html += '<span>' + history[i] + '</span>';
    if (history[i+1]) html += '<span>' + history[i+1] + '</span>';
    html += '</div>';
  }
  let el = document.getElementById('move-list');
  el.innerHTML = html;
  el.scrollTop = el.scrollHeight;
}

function newGame() {
  game = new Chess();
  gameOver = false;
  board.position('start');
  document.getElementById('status-bar').textContent = 'White to move';
  document.getElementById('move-list').innerHTML = '<span style="color:var(--muted)">No moves yet…</span>';
  document.getElementById('fen-input').value = '';
}

function undoMove() {
  game.undo(); game.undo();
  board.position(game.fen());
  updateStatus();
  updateMoveList();
}

function flipBoard() { board.flip(); }

function resignGame() {
  if (gameOver) return;
  let who = game.turn() === 'w' ? 'White' : 'Black';
  document.getElementById('status-bar').textContent = who + ' resigned. Game over.';
  gameOver = true;
}

function loadFen() {
  let fen = document.getElementById('fen-input').value.trim();
  if (!fen) return;
  let tmp = new Chess();
  if (!tmp.load(fen)) { alert('Invalid FEN!'); return; }
  game = tmp;
  gameOver = false;
  board.position(fen);
  updateStatus();
  updateMoveList();
}

function copyFen() {
  navigator.clipboard.writeText(game.fen()).then(() => {
    let btn = event.target;
    btn.textContent = '✓ Copied!';
    setTimeout(() => btn.textContent = 'Copy FEN', 1500);
  });
}

function copyPgn() {
  navigator.clipboard.writeText(game.pgn()).then(() => {
    let btn = event.target;
    btn.textContent = '✓ Copied!';
    setTimeout(() => btn.textContent = '📋 Copy PGN', 1500);
  });
}

function onSnapEnd() { board.position(game.fen()); }

$(document).ready(function() {
  board = Chessboard('board', {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
});

/* ═══════════════════════════════════════════
   REVIEW
═══════════════════════════════════════════ */
let reviewBoard = null;
let reviewGame = null;
let reviewMoves = [];
let reviewIndex = 0;

function initReviewBoard() {
  reviewBoard = Chessboard('review-board', {
    draggable: false,
    position: 'start',
    pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
  });
}

function loadPgn() {
  let pgn = document.getElementById('pgn-input').value.trim();
  if (!pgn) return;
  let tmp = new Chess();
  if (!tmp.load_pgn(pgn)) { alert('Invalid PGN!'); return; }
  reviewGame = tmp;
  rebuildReview();
}

function loadSamplePgn() {
  let sample = `[Event "Immortal Game"]
[White "Anderssen"]
[Black "Kieseritzky"]
[Result "1-0"]

1. e4 e5 2. f4 exf4 3. Bc4 Qh4+ 4. Kf1 b5 5. Bxb5 Nf6 6. Nf3 Qh6 7. d3 Nh5
8. Nh4 Qg5 9. Nf5 c6 10. g4 Nf6 11. Rg1 cxb5 12. h4 Qg6 13. h5 Qg5 14. Qf3
Ng8 15. Bxf4 Qf6 16. Nc3 Bc5 17. Nd5 Qxb2 18. Bd6 Bxg1 19. e5 Qxa1+ 20. Ke2
Na6 21. Nxg7+ Kd8 22. Qf6+ Nxf6 23. Be7# 1-0`;
  document.getElementById('pgn-input').value = sample;
  loadPgn();
}

function rebuildReview() {
  let tmp = new Chess();
  let hist = reviewGame.history({ verbose: true });
  reviewMoves = [];

  // push start state
  reviewMoves.push({ fen: tmp.fen(), san: null, moveNum: 0, color: null });

  hist.forEach((m, i) => {
    tmp.move(m.san);
    reviewMoves.push({ fen: tmp.fen(), san: m.san, moveNum: Math.floor(i/2)+1, color: m.color });
  });

  reviewIndex = 0;
  reviewGo(0);
  renderReviewMoves();
}

function reviewGo(idx) {
  if (!reviewMoves.length) return;
  reviewIndex = Math.max(0, Math.min(idx, reviewMoves.length - 1));
  let state = reviewMoves[reviewIndex];
  reviewBoard.position(state.fen);
  document.getElementById('review-fen').value = state.fen;
  document.getElementById('move-counter').textContent = reviewIndex + ' / ' + (reviewMoves.length - 1);
  updateReviewStatus(state);
  highlightReviewMove();
}

function reviewNext()   { reviewGo(reviewIndex + 1); }
function reviewPrev()   { reviewGo(reviewIndex - 1); }
function reviewGoLast() { reviewGo(reviewMoves.length - 1); }

function updateReviewStatus(state) {
  let el = document.getElementById('review-status');
  if (reviewIndex === 0) { el.textContent = 'Starting position'; return; }
  let who = state.color === 'w' ? 'White' : 'Black';
  el.textContent = 'Move ' + state.moveNum + ': ' + who + ' played ' + state.san;
}

function renderReviewMoves() {
  if (!reviewMoves.length) return;
  let html = '';
  for (let i = 1; i < reviewMoves.length; i++) {
    let m = reviewMoves[i];
    if (m.color === 'w') html += '<span style="color:var(--accent);margin-right:4px">' + m.moveNum + '.</span>';
    html += '<span class="rmove" id="rm-' + i + '" onclick="reviewGo(' + i + ')">' + m.san + '</span> ';
    if (m.color === 'b') html += '<br>';
  }
  document.getElementById('review-moves').innerHTML = html;
}

function highlightReviewMove() {
  document.querySelectorAll('.rmove').forEach(e => e.classList.remove('current'));
  let el = document.getElementById('rm-' + reviewIndex);
  if (el) { el.classList.add('current'); el.scrollIntoView({ block: 'nearest' }); }
}

// Keyboard nav for review
document.addEventListener('keydown', function(e) {
  if (!document.getElementById('view-review').classList.contains('active')) return;
  if (e.key === 'ArrowRight') reviewNext();
  if (e.key === 'ArrowLeft')  reviewPrev();
  if (e.key === 'Home') reviewGo(0);
  if (e.key === 'End')  reviewGoLast();
});

/* ═══════════════════════════════════════════
   LEARN
═══════════════════════════════════════════ */
const topics = [
  {
    icon: '♟', title: 'Chess Basics',
    desc: 'Learn how each piece moves, the objective of the game, and fundamental rules like castling and en passant.',
    content: `
      <p>Chess is a two-player strategy game played on an 8×8 board. Each player starts with 16 pieces: 1 king, 1 queen, 2 rooks, 2 bishops, 2 knights, and 8 pawns.</p>
      <p><strong style="color:var(--accent)">Objective:</strong> Checkmate your opponent's king — put it under attack with no legal escape.</p>
      <p><strong style="color:var(--accent)">How pieces move:</strong></p>
      <ul>
        <li><b>King</b> — One square in any direction</li>
        <li><b>Queen</b> — Any number of squares in any direction (most powerful)</li>
        <li><b>Rook</b> — Any number of squares horizontally or vertically</li>
        <li><b>Bishop</b> — Any number of squares diagonally (stays on one color)</li>
        <li><b>Knight</b> — L-shape: 2 squares + 1 square perpendicular; can jump over pieces</li>
        <li><b>Pawn</b> — One square forward (two from starting square); captures diagonally</li>
      </ul>
      <p><strong style="color:var(--accent)">Special moves:</strong> Castling (king + rook swap), En passant (pawn capture), Promotion (pawn reaches the last rank and becomes any piece).</p>
    `
  },
  {
    icon: '🏁', title: 'Opening Principles',
    desc: 'Master the fundamental principles of chess openings: control the center, develop pieces, and castle early.',
    content: `
      <p>The opening is the first phase of chess. Your goal is to build a strong position before the tactics begin.</p>
      <p><strong style="color:var(--accent)">The Golden Rules:</strong></p>
      <ul>
        <li><b>Control the Center</b> — Place pawns and pieces on e4, d4, e5, d5. Central pieces have more mobility.</li>
        <li><b>Develop Your Pieces</b> — Get knights and bishops out before moving the same piece twice.</li>
        <li><b>Castle Early</b> — Tuck your king away safely on the kingside or queenside.</li>
        <li><b>Connect Your Rooks</b> — Once all minor pieces are developed, put rooks on open files.</li>
        <li><b>Don't Move Pawns Unnecessarily</b> — Each pawn move is permanent and can create weaknesses.</li>
      </ul>
      <p><strong style="color:var(--accent)">Popular Openings:</strong></p>
      <ul>
        <li><b>Italian Game (1.e4 e5 2.Nf3 Nc6 3.Bc4)</b> — Classic, solid, great for beginners</li>
        <li><b>Ruy López (1.e4 e5 2.Nf3 Nc6 3.Bb5)</b> — One of the oldest and most respected openings</li>
        <li><b>Queen's Gambit (1.d4 d5 2.c4)</b> — Fighting for central control from a distance</li>
        <li><b>Sicilian Defense (1.e4 c5)</b> — Black fights back asymmetrically — the most played response to 1.e4</li>
      </ul>
    `
  },
  {
    icon: '⚔️', title: 'Middle Game Tactics',
    desc: 'Discover powerful tactical patterns: forks, pins, skewers, discovered attacks, and combinations.',
    content: `
      <p>The middle game is where most games are decided. Tactics are short, forcing sequences that win material or deliver checkmate.</p>
      <p><strong style="color:var(--accent)">Core Tactical Motifs:</strong></p>
      <ul>
        <li><b>Fork</b> — One piece attacks two or more enemy pieces simultaneously (knights are notorious forkers)</li>
        <li><b>Pin</b> — A piece is immobilized because moving it would expose a more valuable piece behind it</li>
        <li><b>Skewer</b> — Like a pin in reverse — a valuable piece is attacked and forced to move, exposing a lesser piece</li>
        <li><b>Discovered Attack</b> — Moving one piece reveals an attack by another piece behind it</li>
        <li><b>Double Check</b> — Two pieces check the king at once; the king must move</li>
        <li><b>Deflection / Decoy</b> — Force a defending piece away from its post</li>
        <li><b>Back-rank Mate</b> — Rook or queen delivers checkmate on the 1st/8th rank</li>
      </ul>
      <p><strong style="color:var(--accent)">Calculation Tips:</strong> Always look for checks, captures, and threats first (CCT). Visualize the position at least 2-3 moves ahead before committing.</p>
    `
  },
  {
    icon: '🏰', title: 'Strategic Play',
    desc: 'Understand long-term planning: pawn structure, piece activity, weak squares, and positional concepts.',
    content: `
      <p>Strategy is about making long-term plans based on the position's permanent features. Unlike tactics, strategy unfolds over many moves.</p>
      <p><strong style="color:var(--accent)">Key Strategic Concepts:</strong></p>
      <ul>
        <li><b>Pawn Structure</b> — Avoid isolated, doubled, or backward pawns. Passed pawns are powerful assets.</li>
        <li><b>Piece Activity</b> — Place pieces on their optimal squares. A knight on the rim is dim!</li>
        <li><b>Open Files</b> — Rooks belong on open (no pawns) or semi-open files.</li>
        <li><b>Outpost Squares</b> — Stable squares (especially in the opponent's half) that enemy pawns can't attack</li>
        <li><b>The Bishop Pair</b> — Two bishops working together in open positions are very powerful</li>
        <li><b>King Safety</b> — Always be mindful of your king. An unsafe king can nullify all material advantages.</li>
        <li><b>Space Advantage</b> — More space = more mobility for your pieces</li>
      </ul>
      <p><strong style="color:var(--accent)">Imbalances:</strong> Strong players look for and create imbalances — asymmetrical features that favor them (e.g., knight vs bishop, pawn majority on one side).</p>
    `
  },
  {
    icon: '♔', title: 'Endgame Mastery',
    desc: 'Learn essential endgame techniques: king activity, pawn promotion, Lucena & Philidor positions.',
    content: `
      <p>The endgame begins when most pieces have been traded off. Endgame skill often determines the winner in evenly matched games.</p>
      <p><strong style="color:var(--accent)">Essential Endgames to Know:</strong></p>
      <ul>
        <li><b>King + Pawn vs King</b> — Learn the "opposition" concept and the key square method</li>
        <li><b>Rook Endgames</b> — Most common endgame type. Learn Lucena (winning) and Philidor (drawing) positions</li>
        <li><b>Queen vs Pawn</b> — Usually winning, but tricky with rook pawns on the 7th rank</li>
        <li><b>King + 2 Bishops vs King</b> — Forced checkmate in under 19 moves</li>
        <li><b>Knight + Bishop vs King</b> — Rare but mandatory to know — requires driving the king to the "right corner"</li>
      </ul>
      <p><strong style="color:var(--accent)">Endgame Principles:</strong></p>
      <ul>
        <li>Activate your king — it becomes a fighting piece in the endgame</li>
        <li>Create a passed pawn and advance it</li>
        <li>Rooks belong behind passed pawns (yours or the opponent's)</li>
        <li>Trade pieces (not pawns) when ahead in material</li>
        <li>Know your theoretical draws — don't play on in lost positions</li>
      </ul>
    `
  },
  {
    icon: '📈', title: 'How to Improve',
    desc: 'A structured training plan covering puzzles, game analysis, openings study, and endgame practice.',
    content: `
      <p>Improving at chess requires deliberate practice across multiple areas. Here is a proven training framework:</p>
      <p><strong style="color:var(--accent)">Daily Practice Routine:</strong></p>
      <ul>
        <li><b>Tactics Puzzles (30 min)</b> — Solve 10-20 puzzles daily on Lichess or Chess.com. Pattern recognition is the fastest way to improve.</li>
        <li><b>Play Slow Games (30-60 min)</b> — 10+5 or 15+10 time controls. Avoid bullet chess — it builds bad habits.</li>
        <li><b>Analyze Your Games (20 min)</b> — Review your games with an engine. Find where you went wrong.</li>
        <li><b>Endgame Study (15 min)</b> — Learn one new fundamental endgame per week</li>
        <li><b>Opening Preparation (15 min)</b> — Build a small, solid repertoire rather than memorizing 20 moves deep</li>
      </ul>
      <p><strong style="color:var(--accent)">Rating Milestones:</strong></p>
      <ul>
        <li><b>Under 1000</b> — Focus on piece safety. Don't hang pieces!</li>
        <li><b>1000–1500</b> — Learn basic tactics. Solve puzzles every day.</li>
        <li><b>1500–1800</b> — Study strategy and pawn structures</li>
        <li><b>1800+</b> — Deep opening preparation, endgame mastery, and positional nuance</li>
      </ul>
      <p><strong style="color:var(--accent)">Recommended Resources:</strong> "My System" by Nimzowitsch, "Silman's Complete Endgame Course," Lichess.org (free), Chessable courses.</p>
    `
  },
  {
    icon: '🎯', title: 'Famous Games',
    desc: 'Study legendary chess games: the Immortal Game, the Evergreen Game, and games from world champions.',
    content: `
      <p>Studying great games is one of the most enjoyable ways to improve. These masterpieces show chess at its most creative.</p>
      <p><strong style="color:var(--accent)">Must-Study Games:</strong></p>
      <ul>
        <li><b>The Immortal Game (Anderssen vs Kieseritzky, 1851)</b> — Adolf Anderssen sacrificed both rooks and the queen to deliver a stunning checkmate. Load the sample PGN in the Review tab!</li>
        <li><b>The Evergreen Game (Anderssen vs Dufresne, 1852)</b> — Another dazzling attack with two queen sacrifices</li>
        <li><b>Morphy's Opera Game (Morphy vs Duke of Brunswick, 1858)</b> — Paul Morphy shows how rapid development and king safety lead to a brilliant attack</li>
        <li><b>Deep Blue vs Kasparov, Game 2 (1997)</b> — The famous computer win that shocked the world</li>
        <li><b>Kasparov vs Topalov (1999)</b> — "Kasparov's Immortal" — a rook sacrifice followed by a king march</li>
        <li><b>Magnus Carlsen vs Vishy Anand (2013 WCC)</b> — Endgame mastery at the highest level</li>
      </ul>
      <p>Use the <strong style="color:var(--accent)">Review</strong> tab to load and step through any of these games in PGN format!</p>
    `
  },
  {
    icon: '🧠', title: 'Chess Psychology',
    desc: 'Mental game tips: handling pressure, time management, avoiding tilt, and tournament preparation.',
    content: `
      <p>Chess is as much a mental battle as it is a board game. Strong psychological habits separate good players from great ones.</p>
      <p><strong style="color:var(--accent)">During the Game:</strong></p>
      <ul>
        <li><b>Manage your clock wisely</b> — Don't spend 20 minutes on move 5. Save time for complex positions.</li>
        <li><b>Don't play on emotions</b> — After losing a piece, calm down and find the best defense. Many games are saved from hopeless positions.</li>
        <li><b>Respect all opponents</b> — Underestimating a weaker player leads to careless play and upsets.</li>
        <li><b>Always look for your opponent's threat</b> — Before making any move, ask "what is my opponent threatening?"</li>
        <li><b>Trust your preparation</b> — Don't second-guess your opening in the first 10 moves if you've studied it.</li>
      </ul>
      <p><strong style="color:var(--accent)">After the Game:</strong></p>
      <ul>
        <li>Analyze losses without ego — every loss is a lesson</li>
        <li>Don't play too many games in a row when on a losing streak ("tilt")</li>
        <li>Take breaks — chess improvement is a long-term journey</li>
      </ul>
    `
  }
];

function renderLearnCards() {
  let html = '';
  topics.forEach((t, i) => {
    html += `<div class="topic-card" onclick="openArticle(${i})">
      <div class="topic-icon">${t.icon}</div>
      <h3>${t.title}</h3>
      <p>${t.desc}</p>
    </div>`;
  });
  document.getElementById('learn-grid').innerHTML = html;
}

function openArticle(i) {
  let t = topics[i];
  document.getElementById('article-title').textContent = t.icon + '  ' + t.title;
  document.getElementById('article-body').innerHTML = t.content;
  document.getElementById('article-modal').classList.add('open');
}

function closeArticle() {
  document.getElementById('article-modal').classList.remove('open');
}

// Close modal on overlay click
document.getElementById('article-modal').addEventListener('click', function(e) {
  if (e.target === this) closeArticle();
});
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    print("\n♟  ChessMaster is running!")
    print("   Open your browser at:  http://localhost:5000\n")
    app.run(debug=True, port=5000)
