import streamlit as st

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chess Academy",
    page_icon="♚",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
    background-color: #0a0a0a;
    color: #ede8df;
}
.main { background-color: #0a0a0a; }
.block-container { padding: 2rem 2rem; max-width: 1100px; }

h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    color: #ede8df !important;
}

/* Hero */
.hero-box {
    background: linear-gradient(135deg, #111 0%, #1a1a1a 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid #c9922e;
    padding: 2.5rem 2rem;
    border-radius: 4px;
    margin-bottom: 2rem;
    text-align: center;
}
.hero-title {
    font-family: 'Cinzel', serif;
    font-size: 2.8rem;
    color: #e8b84b !important;
    margin-bottom: 0.5rem;
}
.hero-sub {
    color: rgba(237,232,223,0.6);
    font-size: 1rem;
    margin-top: 0.5rem;
}

/* Module cards */
.mod-card {
    background: #111;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    cursor: pointer;
    transition: all 0.2s;
}
.mod-card:hover { background: #181818; }
.mod-icon { font-size: 2rem; }
.mod-title {
    font-family: 'Cinzel', serif;
    font-size: 1.2rem;
    color: #e8b84b;
    margin: 0.3rem 0;
}
.mod-tagline { color: rgba(237,232,223,0.5); font-size: 0.85rem; font-style: italic; }

/* Topic cards */
.topic-card {
    background: #111;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}
.topic-name {
    font-family: 'Cinzel', serif;
    font-size: 1rem;
    color: #ede8df;
}
.topic-moves { color: #c9922e; font-size: 0.8rem; margin: 0.3rem 0; }
.topic-desc { color: rgba(237,232,223,0.6); font-size: 0.85rem; line-height: 1.6; }

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 3px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    float: right;
}
.beginner    { background: rgba(42,122,96,.25);  color: #3db890; }
.intermediate{ background: rgba(201,146,46,.25); color: #e8b84b; }
.advanced    { background: rgba(184,56,32,.25);  color: #e07050; }

/* Principle */
.principle {
    background: #181818;
    border-left: 3px solid #c9922e;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0 4px 4px 0;
    font-size: 0.88rem;
    color: rgba(237,232,223,0.8);
}

/* Stats */
.stat-box {
    background: #111;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px;
    padding: 1.2rem;
    text-align: center;
}
.stat-num {
    font-family: 'Cinzel', serif;
    font-size: 2.2rem;
    color: #e8b84b;
}
.stat-lbl { color: rgba(237,232,223,0.45); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; }

/* Divider */
.gold-line { border: none; border-top: 1px solid rgba(201,146,46,0.3); margin: 1.5rem 0; }

/* Section header */
.sec-header {
    background: linear-gradient(90deg, #181818, #111);
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 4px solid;
    padding: 1.5rem 1.8rem;
    border-radius: 4px;
    margin-bottom: 1.5rem;
}
.sec-eyebrow { font-size: 0.7rem; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.4rem; }
.sec-title-text { font-family: 'Cinzel', serif; font-size: 2rem; margin-bottom: 0.3rem; }
.sec-tagline-text { font-style: italic; font-size: 0.9rem; opacity: 0.6; margin-bottom: 0.8rem; }
.sec-intro-text { font-size: 0.88rem; line-height: 1.8; opacity: 0.75; }

div[data-testid="stButton"] button {
    background: #c9922e !important;
    color: #0a0a0a !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
    border-radius: 3px !important;
}
div[data-testid="stButton"] button:hover {
    background: #e8b84b !important;
}
</style>
""", unsafe_allow_html=True)

# ── Chess Content ─────────────────────────────────────────────────────────────
SECTIONS = {
    "openings": {
        "title": "Openings", "icon": "♟", "color": "#c9922e",
        "tagline": "Control the center, develop pieces, castle early.",
        "intro": "The opening sets the tone for the entire game. Your three main goals are to control the center, develop all your minor pieces, and get your king to safety by castling. Understanding WHY these principles exist matters far more than memorising long lines.",
        "principles": [
            "Fight for the center with pawns (e4/d4 or e5/d5)",
            "Develop knights before bishops",
            "Castle early — your king is not safe in the center",
            "Don't move the same piece twice in the opening",
            "Connect your rooks before starting active play",
        ],
        "topics": [
            {"name": "Italian Game",        "moves": "1.e4 e5  2.Nf3 Nc6  3.Bc4",     "level": "Beginner",     "type": "Open Game",      "desc": "One of the oldest openings. White develops rapidly and eyes the f7 pawn. Great for beginners who want active, principled play."},
            {"name": "Ruy López",           "moves": "1.e4 e5  2.Nf3 Nc6  3.Bb5",     "level": "Intermediate", "type": "Open Game",      "desc": "The 'Spanish Torture'. Deep strategic play with long-term pressure — a favourite of world champions for centuries."},
            {"name": "Sicilian Defense",    "moves": "1.e4 c5",                         "level": "Intermediate", "type": "Semi-Open",      "desc": "Black's most popular reply to 1.e4. Creates asymmetry from move one and gives Black excellent winning chances."},
            {"name": "Queen's Gambit",      "moves": "1.d4 d5  2.c4",                  "level": "Intermediate", "type": "Closed Game",    "desc": "White offers a pawn to gain central control. Not a true gambit — Black usually can't hold the extra pawn safely."},
            {"name": "King's Indian",       "moves": "1.d4 Nf6  2.c4 g6",             "level": "Advanced",     "type": "Indian Defense", "desc": "Black lets White build a large center, then attacks it with pieces. Dynamic counterplay and wild complications."},
            {"name": "French Defense",      "moves": "1.e4 e6",                         "level": "Beginner",     "type": "Semi-Open",      "desc": "A solid, counterattacking system. Black builds a solid pawn structure and prepares to challenge White's center."},
            {"name": "Caro-Kann Defense",   "moves": "1.e4 c6",                         "level": "Beginner",     "type": "Semi-Open",      "desc": "Similar to the French but without the bad bishop. Solid and positionally sound — great for beginners."},
            {"name": "English Opening",     "moves": "1.c4",                            "level": "Advanced",     "type": "Flank Opening",  "desc": "A flexible flank opening. White controls d5 from the side and keeps all options open."},
        ],
    },
    "middlegame": {
        "title": "Middlegame", "icon": "⚔", "color": "#b83820",
        "tagline": "Where plans collide and battles are decided.",
        "intro": "The middlegame is the most complex phase. Pieces are developed, the center is contested, and now you must form a plan. Tactical awareness, positional understanding, and king safety all come into play at once.",
        "principles": [
            "Always look for tactics before making a quiet move",
            "Identify the worst piece on the board and improve it",
            "Attack where you have more space or piece activity",
            "Identify your opponent's plan — then stop it",
            "Create imbalances to generate winning chances",
        ],
        "topics": [
            {"name": "Forks",               "moves": "One piece attacks two at once",       "level": "Beginner",     "type": "Tactics",   "desc": "A fork attacks two enemy pieces simultaneously. Knights are the best forking pieces. Train yourself to spot them instantly."},
            {"name": "Pins & Skewers",      "moves": "Bishops, Rooks & Queens",            "level": "Beginner",     "type": "Tactics",   "desc": "A pin immobilizes a piece protecting something valuable. A skewer is the reverse. Both exploit alignment on ranks, files and diagonals."},
            {"name": "Discovered Attacks",  "moves": "Move one piece, reveal another",     "level": "Intermediate", "type": "Tactics",   "desc": "Moving one piece unveils an attack by a piece behind it. If the moving piece also attacks, it's a discovered check — devastating."},
            {"name": "Pawn Structure",      "moves": "Isolated · Passed · Doubled",        "level": "Intermediate", "type": "Strategy",  "desc": "Your pawn structure defines your long-term plan. Isolated pawns are weak, passed pawns are powerful, doubled pawns restrict mobility."},
            {"name": "King Safety",         "moves": "Attack the uncastled king",           "level": "Intermediate", "type": "Strategy",  "desc": "An uncastled king is a target. Open files toward it, sacrifice material to break open the position, and attack before it escapes."},
            {"name": "Piece Coordination",  "moves": "Rooks · Bishops · Knights",          "level": "Advanced",     "type": "Strategy",  "desc": "Pieces work best together. Double rooks on open files, use bishop pairs to control both colors, place knights on outpost squares."},
            {"name": "Sacrifices",          "moves": "Material for initiative",             "level": "Advanced",     "type": "Tactics",   "desc": "Sometimes giving up material gains a decisive advantage. Calculating sacrifices precisely is the hardest skill to master."},
            {"name": "Zwischenzug",         "moves": "The in-between move",                 "level": "Intermediate", "type": "Tactics",   "desc": "Before making the expected recapture, insert a strong intermediate move that changes the evaluation. Failing to see these causes blunders."},
        ],
    },
    "endgame": {
        "title": "Endgame", "icon": "♔", "color": "#2a7a60",
        "tagline": "Technique turns a small edge into victory.",
        "intro": "Endgames are the most neglected phase, yet many games are decided here. With fewer pieces, the king becomes a powerful fighting piece, passed pawns become queens, and one tempo can decide everything.",
        "principles": [
            "Activate your king — it is a fighting piece in the endgame",
            "A passed pawn must be pushed relentlessly",
            "Rooks belong behind passed pawns, yours or the opponent's",
            "Master the opposition in king-and-pawn endings",
            "Know all basic mating patterns by heart",
        ],
        "topics": [
            {"name": "King & Pawn Endings", "moves": "Opposition · Key squares",           "level": "Beginner",     "type": "Pawn Endings",  "desc": "The foundation of all endgame theory. Master the opposition, key squares, and the rule of the square to convert any pawn advantage."},
            {"name": "Basic Checkmates",    "moves": "K+Q vs K  ·  K+R vs K",             "level": "Beginner",     "type": "Checkmates",    "desc": "Every player must deliver checkmate with queen or rook against a lone king confidently. Practice until it takes fewer than 20 moves."},
            {"name": "Rook Endings",        "moves": "Lucena · Philidor positions",        "level": "Intermediate", "type": "Rook Endings",  "desc": "Rook endings are the most common type. The Lucena (winning) and Philidor (drawing) positions are the most important to know."},
            {"name": "Bishop vs Knight",    "moves": "Good bishop · Bad bishop",           "level": "Intermediate", "type": "Minor Pieces",  "desc": "Bishops shine in open positions; knights excel in closed ones. A bishop blocked by its own pawns is practically worthless."},
            {"name": "Zugzwang",            "moves": "Being forced to move loses",         "level": "Intermediate", "type": "Concepts",      "desc": "Zugzwang is when any move the player makes worsens their position. It appears most often in king-and-pawn endings."},
            {"name": "Queen Endings",       "moves": "Q vs advanced pawn",                 "level": "Advanced",     "type": "Queen Endings", "desc": "Queen endings are rich with perpetual check resources and stalemate tricks. Knowing when a queen beats a passed pawn saves half-points."},
            {"name": "Triangulation",       "moves": "Losing a tempo with the king",       "level": "Advanced",     "type": "Concepts",      "desc": "Using three king moves to achieve what two would if you had the move. Forces zugzwang and is key in many king-and-pawn positions."},
            {"name": "Pawn Promotion",      "moves": "Queening · Underpromotion",          "level": "Beginner",     "type": "Pawn Endings",  "desc": "Promoting a pawn to a queen is the ultimate endgame goal. Occasionally promoting to a knight (underpromotion) avoids stalemate."},
        ],
    },
    "strategy": {
        "title": "Strategy", "icon": "🧠", "color": "#5848b0",
        "tagline": "Long-term thinking separates masters from amateurs.",
        "intro": "Tactics are the servants of strategy. While tactics are concrete, strategy is about long-term plans — exploiting weaknesses that cannot be fixed, placing pieces on ideal squares, and slowly squeezing the opponent.",
        "principles": [
            "Target fixed weaknesses — pawns that cannot be defended",
            "Good piece vs bad piece: always identify piece quality",
            "Occupy outposts — squares the opponent cannot attack with pawns",
            "Use prophylaxis to prevent your opponent's best plans",
            "Improve your worst-placed piece before starting an attack",
        ],
        "topics": [
            {"name": "Weak Squares",        "moves": "Color complexes · Outposts",         "level": "Intermediate", "type": "Positional", "desc": "Squares that can no longer be defended by pawns become permanent homes for enemy pieces. Recognizing color weaknesses is critical."},
            {"name": "Open Files",          "moves": "Rooks on the 7th rank",              "level": "Beginner",     "type": "Positional", "desc": "Open files are highways for rooks. A rook on the seventh rank devours pawns and cuts off the king. Double rooks to maximize power."},
            {"name": "Prophylaxis",         "moves": "Stop the opponent's plan first",     "level": "Advanced",     "type": "Concepts",   "desc": "Before executing your own plan, ask: what does my opponent want to do? Then prevent it. Petrosian was the grandmaster of this art."},
            {"name": "Pawn Breaks",         "moves": "Shattering the pawn chain",          "level": "Intermediate", "type": "Pawn Play",  "desc": "A pawn break opens files, destroys the opponent's structure, or activates pieces. Timing the break correctly is everything."},
            {"name": "Space Advantage",     "moves": "Cramping the enemy pieces",          "level": "Intermediate", "type": "Positional", "desc": "More space means more room for your pieces to maneuver and fewer squares for your opponent's. Convert space into threats."},
            {"name": "Minority Attack",     "moves": "Two pawns vs three",                 "level": "Advanced",     "type": "Pawn Play",  "desc": "Advance two pawns against the opponent's three to create a fixed weakness — usually a backward or isolated pawn. Common in QGD positions."},
        ],
    },
    "classics": {
        "title": "Classic Games", "icon": "🏆", "color": "#1a6898",
        "tagline": "Study the immortal games — absorb ideas worth 1000 moves.",
        "intro": "The greatest games ever played are a masterclass in every concept. Studying annotated masterpieces builds pattern recognition faster than any other method. Pause at every critical moment and find the best move yourself.",
        "principles": [
            "Study annotations deeply — understand every move's purpose",
            "Pause at critical positions and calculate before looking",
            "Identify the strategic theme before the concrete tactics",
            "Replay each game multiple times — new insights appear every time",
            "Ask yourself: why didn't the loser defend differently?",
        ],
        "topics": [
            {"name": "The Immortal Game",           "moves": "Anderssen vs Kieseritzky  1851",   "level": "Intermediate", "type": "Romantic Era",         "desc": "Anderssen sacrificed both rooks, a bishop, and his queen to deliver checkmate. The most famous attacking game of the 19th century."},
            {"name": "Game of the Century",         "moves": "Byrne vs Fischer  1956",           "level": "Intermediate", "type": "Tactical Masterpiece", "desc": "13-year-old Bobby Fischer sacrificed his queen on move 17 and produced one of the greatest games ever played."},
            {"name": "The Opera Game",              "moves": "Morphy vs Duke of Brunswick 1858", "level": "Beginner",     "type": "Development Classic",  "desc": "Played during an opera performance, Morphy demolishes opponents with textbook development and a final back-rank mate."},
            {"name": "Kasparov vs Topalov",         "moves": "Wijk aan Zee  1999",               "level": "Advanced",     "type": "Modern Masterpiece",   "desc": "Called the greatest game of the 20th century. Kasparov conducts a stunning king march across the entire board to win brilliantly."},
            {"name": "Fischer vs Spassky — Game 6", "moves": "World Championship  1972",         "level": "Advanced",     "type": "Positional Classic",   "desc": "Fischer called this his best game. A stunning positional masterpiece — his bishop on h3 is a monument to strategic thinking."},
            {"name": "Deep Blue vs Kasparov",       "moves": "Philadelphia  1997",               "level": "Advanced",     "type": "Historic Match",       "desc": "The game that shook the world. IBM's computer defeated the world champion with apparently human-like creativity."},
        ],
    },
}

# ── Session State ─────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"
if "section" not in st.session_state:
    st.session_state.section = None

def go_home():
    st.session_state.page = "home"
    st.session_state.section = None

def go_section(sid):
    st.session_state.page = "section"
    st.session_state.section = sid

# ── HOME PAGE ─────────────────────────────────────────────────────────────────
if st.session_state.page == "home":

    # Hero
    st.markdown("""
    <div class='hero-box'>
        <div class='hero-title'>♚ Chess Academy</div>
        <div style='color:#c9922e;font-size:0.8rem;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:0.5rem'>Complete Chess Learning System</div>
        <div class='hero-sub'>Opening theory · Middlegame tactics · Endgame technique · Grandmaster classics</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='stat-box'><div class='stat-num'>5</div><div class='stat-lbl'>Modules</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='stat-box'><div class='stat-num'>38</div><div class='stat-lbl'>Topics</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='stat-box'><div class='stat-num'>∞</div><div class='stat-lbl'>Depth</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;font-size:1.5rem;margin-bottom:1.5rem'>Choose Your Module</h2>", unsafe_allow_html=True)

    # Module cards
    col1, col2 = st.columns(2)
    keys = list(SECTIONS.keys())

    for i, sid in enumerate(keys):
        sec = SECTIONS[sid]
        col = col1 if i % 2 == 0 else col2
        with col:
            st.markdown(f"""
            <div class='mod-card'>
                <div class='mod-icon'>{sec['icon']}</div>
                <div class='mod-title'>{sec['title']}</div>
                <div class='mod-tagline'>{sec['tagline']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open {sec['title']} →", key=f"btn_{sid}"):
                go_section(sid)
                st.rerun()

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;color:rgba(237,232,223,0.35);font-size:0.78rem;padding:1rem 0'>
        ♚ Chess Academy — Built with Python 3 (64-bit) &amp; Streamlit
    </div>
    """, unsafe_allow_html=True)

# ── SECTION PAGE ──────────────────────────────────────────────────────────────
elif st.session_state.page == "section":
    sid = st.session_state.section
    sec = SECTIONS[sid]

    if st.button("← Back to Home"):
        go_home()
        st.rerun()

    # Section header
    st.markdown(f"""
    <div class='sec-header' style='border-color:{sec["color"]}'>
        <div class='sec-eyebrow' style='color:{sec["color"]}'>Chess Academy · {sec["title"]}</div>
        <div class='sec-title-text'>{sec["icon"]} {sec["title"]}</div>
        <div class='sec-tagline-text'>{sec["tagline"]}</div>
        <div style='width:40px;height:2px;background:{sec["color"]};margin:0.8rem 0'></div>
        <div class='sec-intro-text'>{sec["intro"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Principles
    st.markdown(f"<div style='font-size:0.68rem;letter-spacing:0.2em;text-transform:uppercase;color:{sec['color']};margin-bottom:0.8rem'>Core Principles</div>", unsafe_allow_html=True)
    for i, p in enumerate(sec["principles"], 1):
        st.markdown(f"<div class='principle'><b style='color:{sec['color']}'>{i}.</b> {p}</div>", unsafe_allow_html=True)

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

    # Topics
    st.markdown(f"<div style='font-size:0.68rem;letter-spacing:0.2em;text-transform:uppercase;color:{sec['color']};margin-bottom:0.8rem'>Topics in This Module</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    for i, t in enumerate(sec["topics"]):
        col = col1 if i % 2 == 0 else col2
        with col:
            badge_class = t["level"].lower()
            st.markdown(f"""
            <div class='topic-card'>
                <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                    <div class='topic-name'>{t["name"]}</div>
                    <span class='badge {badge_class}'>{t["level"]}</span>
                </div>
                <div class='topic-moves'>{t["moves"]}</div>
                <div class='topic-desc'>{t["desc"]}</div>
                <div style='font-size:0.65rem;color:rgba(237,232,223,0.2);text-transform:uppercase;letter-spacing:0.1em;margin-top:0.6rem'>{t["type"]}</div>
            </div>
            """, unsafe_allow_html=True)

    # Bottom nav
    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    keys = list(SECTIONS.keys())
    idx = keys.index(sid)

    c1, c2, c3 = st.columns(3)
    with c1:
        if idx > 0:
            prev = SECTIONS[keys[idx-1]]
            if st.button(f"← {prev['title']}"):
                go_section(keys[idx-1])
                st.rerun()
    with c2:
        if st.button("🏠 All Modules"):
            go_home()
            st.rerun()
    with c3:
        if idx < len(keys)-1:
            nxt = SECTIONS[keys[idx+1]]
            if st.button(f"{nxt['title']} →"):
                go_section(keys[idx+1])
                st.rerun()
