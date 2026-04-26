import streamlit as st
import hashlib
import json
import os

st.set_page_config(page_title="Chess Academy", page_icon="♚", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Lato:wght@300;400;700&display=swap');
html,body,[class*="css"]{font-family:'Lato',sans-serif;background-color:#0a0a0a;color:#ede8df}
.main{background-color:#0a0a0a}
.block-container{padding:2rem;max-width:550px}
h1,h2,h3{font-family:'Cinzel',serif!important;color:#ede8df!important}
.hero-box{background:linear-gradient(135deg,#111,#1a1a1a);border-left:4px solid #c9922e;
  border:1px solid rgba(255,255,255,0.07);padding:2rem;border-radius:6px;
  margin-bottom:1.5rem;text-align:center}
.hero-title{font-family:'Cinzel',serif;font-size:2rem;color:#e8b84b}
.hero-sub{color:rgba(237,232,223,0.5);font-size:0.85rem;margin-top:0.4rem}
.section-card{background:#111;border:1px solid rgba(255,255,255,0.07);
  border-radius:8px;padding:1.3rem 1.5rem;margin-bottom:0.5rem}
.section-title{font-family:'Cinzel',serif;font-size:1.05rem;color:#e8b84b;margin-bottom:0.2rem}
.section-sub{color:rgba(237,232,223,0.45);font-size:0.8rem;font-style:italic}
.topic-card{background:#0d0d0d;border:1px solid rgba(255,255,255,0.06);
  border-radius:6px;padding:1.1rem 1.3rem;margin-bottom:0.5rem}
.topic-name{font-family:'Cinzel',serif;font-size:0.95rem;color:#e8b84b;margin-bottom:0.2rem}
.topic-moves{color:#c9922e;font-size:0.75rem;margin-bottom:0.4rem;letter-spacing:0.03em}
.topic-desc{color:rgba(237,232,223,0.55);font-size:0.82rem;line-height:1.6}
.badge{display:inline-block;padding:2px 8px;border-radius:2px;font-size:0.63rem;
  font-weight:700;letter-spacing:0.08em;text-transform:uppercase;float:right}
.beginner{background:rgba(42,122,96,.25);color:#3db890}
.intermediate{background:rgba(201,146,46,.25);color:#e8b84b}
.advanced{background:rgba(184,56,32,.25);color:#e07050}
.principle{background:#181818;border-left:3px solid #c9922e;padding:0.6rem 1rem;
  margin-bottom:0.4rem;border-radius:0 4px 4px 0;font-size:0.83rem;
  color:rgba(237,232,223,0.78)}
.gold-line{border:none;border-top:1px solid rgba(201,146,46,0.2);margin:1.2rem 0}
.error-box{background:rgba(184,56,32,0.15);border:1px solid rgba(184,56,32,0.4);
  border-radius:6px;padding:0.8rem;color:#e07050;font-size:0.85rem;text-align:center;margin-bottom:0.8rem}
.success-box{background:rgba(42,122,96,0.15);border:1px solid rgba(42,122,96,0.4);
  border-radius:6px;padding:0.8rem;color:#3db890;font-size:0.85rem;text-align:center;margin-bottom:0.8rem}
div[data-testid="stTextInput"] input{background:#1a1a1a!important;
  border:1px solid rgba(255,255,255,0.12)!important;border-radius:4px!important;
  color:#ede8df!important;padding:0.6rem 1rem!important}
div[data-testid="stButton"] button{background:#c9922e!important;color:#0a0a0a!important;
  border:none!important;font-weight:700!important;border-radius:4px!important;
  width:100%!important;padding:0.6rem!important;font-size:0.88rem!important}
div[data-testid="stButton"] button:hover{background:#e8b84b!important}
</style>
""", unsafe_allow_html=True)

# ── Chess Content ─────────────────────────────────────────────────────────────
SECTIONS = {
    "♟ Openings": {
        "color": "#c9922e",
        "tagline": "Control the center, develop pieces, castle early.",
        "intro": "The opening sets the tone for the entire game. Control the center, develop all minor pieces, and castle early. Understanding WHY these principles exist matters more than memorising moves.",
        "principles": [
            "Fight for the center with pawns (e4/d4)",
            "Develop knights before bishops",
            "Castle early — keep your king safe",
            "Don't move the same piece twice",
            "Connect your rooks on the back rank",
        ],
        "topics": [
            {"name": "Italian Game",       "moves": "1.e4 e5  2.Nf3 Nc6  3.Bc4",  "level": "Beginner",     "desc": "One of the oldest openings. White develops rapidly and eyes f7. Perfect for beginners learning principled play."},
            {"name": "Ruy López",          "moves": "1.e4 e5  2.Nf3 Nc6  3.Bb5",  "level": "Intermediate", "desc": "The Spanish Torture. Deep strategic pressure — a favourite of world champions for centuries."},
            {"name": "Sicilian Defense",   "moves": "1.e4 c5",                      "level": "Intermediate", "desc": "Black's most popular reply to 1.e4. Creates sharp asymmetric positions with excellent winning chances."},
            {"name": "Queen's Gambit",     "moves": "1.d4 d5  2.c4",               "level": "Intermediate", "desc": "White offers a pawn to gain central control. Not a true gambit — Black can rarely keep the extra pawn."},
            {"name": "King's Indian",      "moves": "1.d4 Nf6  2.c4 g6",           "level": "Advanced",     "desc": "Black lets White build a big center, then attacks it. Dynamic counterplay and kingside attacks."},
            {"name": "French Defense",     "moves": "1.e4 e6",                      "level": "Beginner",     "desc": "Solid and counterattacking. Black builds a strong pawn structure and challenges the center."},
            {"name": "Caro-Kann",          "moves": "1.e4 c6",                      "level": "Beginner",     "desc": "Like the French but without the bad bishop. Solid, reliable, and positionally sound."},
            {"name": "English Opening",    "moves": "1.c4",                         "level": "Advanced",     "desc": "Flexible flank opening. White controls d5 from the side and keeps all options open."},
        ],
    },
    "⚔ Middlegame": {
        "color": "#b83820",
        "tagline": "Where plans collide and battles are decided.",
        "intro": "The middlegame is the most complex phase. Pieces are out, the center is contested, and you must form a plan. Tactics, strategy, and king safety all come into play at once.",
        "principles": [
            "Look for tactics before every quiet move",
            "Find your worst piece and improve it",
            "Attack where you have more space",
            "Identify your opponent's plan — stop it",
            "Create imbalances to generate winning chances",
        ],
        "topics": [
            {"name": "Forks",              "moves": "One piece attacks two at once",    "level": "Beginner",     "desc": "A fork attacks two enemy pieces simultaneously. Knights are the best forking pieces — spot them instantly."},
            {"name": "Pins & Skewers",     "moves": "Bishops, Rooks & Queens",         "level": "Beginner",     "desc": "A pin immobilizes a piece protecting something valuable. A skewer is the reverse. Both exploit alignment."},
            {"name": "Discovered Attacks", "moves": "Move one piece, reveal another",  "level": "Intermediate", "desc": "Moving one piece unveils an attack by a piece behind it. One of the most powerful tactical weapons."},
            {"name": "Pawn Structure",     "moves": "Isolated · Passed · Doubled",     "level": "Intermediate", "desc": "Your pawn structure defines your plan. Isolated pawns are weak, passed pawns are powerful."},
            {"name": "King Safety",        "moves": "Attack the uncastled king",        "level": "Intermediate", "desc": "An uncastled king is a target. Open files toward it and attack before it finds shelter."},
            {"name": "Piece Coordination", "moves": "Rooks · Bishops · Knights",       "level": "Advanced",     "desc": "Pieces work best together. Double rooks on open files, use bishop pairs, place knights on outposts."},
            {"name": "Sacrifices",         "moves": "Material for initiative",          "level": "Advanced",     "desc": "Sometimes giving up material gains a decisive advantage. The hardest skill to master."},
            {"name": "Zwischenzug",        "moves": "The in-between move",             "level": "Intermediate", "desc": "Before recapturing, insert a strong intermediate move. Failing to see these causes many blunders."},
        ],
    },
    "♔ Endgame": {
        "color": "#2a7a60",
        "tagline": "Technique turns a small edge into victory.",
        "intro": "Endgames are the most neglected phase, yet many games are decided here. The king becomes a fighting piece, passed pawns become queens, and one tempo can decide everything.",
        "principles": [
            "Activate your king — it is powerful in endgames",
            "A passed pawn must be pushed relentlessly",
            "Rooks belong behind passed pawns",
            "Master the opposition in king-pawn endings",
            "Know all basic mating patterns cold",
        ],
        "topics": [
            {"name": "King & Pawn Endings", "moves": "Opposition · Key squares",       "level": "Beginner",     "desc": "The foundation of all endgame theory. Master the opposition and key squares to convert any pawn advantage."},
            {"name": "Basic Checkmates",    "moves": "K+Q vs K  ·  K+R vs K",         "level": "Beginner",     "desc": "Every player must deliver checkmate with queen or rook against a lone king confidently."},
            {"name": "Rook Endings",        "moves": "Lucena · Philidor positions",    "level": "Intermediate", "desc": "The most common endgame type. Lucena (winning) and Philidor (drawing) are essential knowledge."},
            {"name": "Bishop vs Knight",    "moves": "Good bishop · Bad bishop",       "level": "Intermediate", "desc": "Bishops shine in open positions, knights in closed ones. Know when to trade and when to keep."},
            {"name": "Zugzwang",            "moves": "Forced to move, forced to lose", "level": "Intermediate", "desc": "Any move the player makes worsens their position. Most common and decisive in king-pawn endings."},
            {"name": "Queen Endings",       "moves": "Q vs advanced pawn",            "level": "Advanced",     "desc": "Rich with perpetual check and stalemate tricks. Know when a queen beats a passed pawn."},
            {"name": "Triangulation",       "moves": "Losing a tempo with the king",  "level": "Advanced",     "desc": "Use three king moves to achieve what two would with the move. Forces zugzwang on the opponent."},
            {"name": "Pawn Promotion",      "moves": "Queening · Underpromotion",     "level": "Beginner",     "desc": "Promoting a pawn is the ultimate endgame goal. Underpromotion to a knight sometimes avoids stalemate."},
        ],
    },
    "🧠 Strategy": {
        "color": "#5848b0",
        "tagline": "Long-term thinking separates masters from amateurs.",
        "intro": "Tactics are the servants of strategy. Strategy is about long-term plans — exploiting fixed weaknesses, placing pieces on ideal squares, and slowly squeezing the opponent until their position collapses.",
        "principles": [
            "Target fixed weaknesses that can't be defended",
            "Good piece vs bad piece — always check quality",
            "Occupy outposts your opponent can't attack",
            "Use prophylaxis to stop opponent's plans",
            "Improve your worst piece before attacking",
        ],
        "topics": [
            {"name": "Weak Squares",      "moves": "Color complexes · Outposts",       "level": "Intermediate", "desc": "Squares that can't be defended by pawns become permanent homes for enemy pieces."},
            {"name": "Open Files",        "moves": "Rooks on the 7th rank",            "level": "Beginner",     "desc": "Open files are highways for rooks. A rook on the 7th rank devours pawns and cuts off the king."},
            {"name": "Prophylaxis",       "moves": "Stop the opponent's plan first",   "level": "Advanced",     "desc": "Before your own plan, ask what your opponent wants to do — then prevent it. Petrosian mastered this."},
            {"name": "Pawn Breaks",       "moves": "Shattering the pawn chain",        "level": "Intermediate", "desc": "A pawn break opens files, destroys structure, or activates pieces. Timing is everything."},
            {"name": "Space Advantage",   "moves": "Cramping the enemy pieces",        "level": "Intermediate", "desc": "More space means more room for your pieces and fewer squares for your opponent's."},
            {"name": "Minority Attack",   "moves": "Two pawns vs three",               "level": "Advanced",     "desc": "Advance two pawns against three to create a fixed weakness. Common in Queen's Gambit positions."},
        ],
    },
    "🏆 Classics": {
        "color": "#1a6898",
        "tagline": "Study the immortal games — absorb timeless ideas.",
        "intro": "The greatest games ever played are a masterclass in every concept. Studying annotated masterpieces builds pattern recognition faster than anything else. Pause and find the best move yourself before reading on.",
        "principles": [
            "Study annotations — understand every move's purpose",
            "Pause at critical positions and calculate first",
            "Identify the strategic theme before the tactics",
            "Replay each game many times — new ideas appear",
            "Ask why the loser didn't defend differently",
        ],
        "topics": [
            {"name": "The Immortal Game",           "moves": "Anderssen vs Kieseritzky  1851",    "level": "Intermediate", "desc": "Anderssen sacrificed both rooks, a bishop, and his queen to deliver checkmate. Pure chess beauty."},
            {"name": "Game of the Century",         "moves": "Byrne vs Fischer  1956",            "level": "Intermediate", "desc": "13-year-old Bobby Fischer sacrificed his queen on move 17 and produced a timeless masterpiece."},
            {"name": "The Opera Game",              "moves": "Morphy vs Duke of Brunswick  1858", "level": "Beginner",     "desc": "Played during an opera, Morphy demolishes opponents with textbook development and a back-rank mate."},
            {"name": "Kasparov vs Topalov",         "moves": "Wijk aan Zee  1999",                "level": "Advanced",     "desc": "The greatest game of the 20th century. Kasparov's king marches across the entire board to win."},
            {"name": "Fischer vs Spassky Game 6",   "moves": "World Championship  1972",          "level": "Advanced",     "desc": "Fischer's best game. A stunning positional masterpiece — his bishop on h3 is a strategic monument."},
            {"name": "Deep Blue vs Kasparov",       "moves": "Philadelphia  1997",                "level": "Advanced",     "desc": "The game that shook the world. A computer defeats the world champion with apparent human creativity."},
        ],
    },
}

# ── User Storage ──────────────────────────────────────────────────────────────
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def register_user(username, password, email):
    users = load_users()
    if username in users:      return False, "Username already exists!"
    if len(username) < 3:      return False, "Username must be at least 3 characters!"
    if len(password) < 6:      return False, "Password must be at least 6 characters!"
    if "@" not in email:       return False, "Please enter a valid email!"
    users[username] = {"password": hash_password(password), "email": email}
    save_users(users)
    return True, "Account created!"

def login_user(username, password):
    users = load_users()
    if username not in users:                               return False, "Username not found!"
    if users[username]["password"] != hash_password(password): return False, "Wrong password!"
    return True, "Login successful!"

# ── Session State ─────────────────────────────────────────────────────────────
defaults = {"logged_in": False, "username": "", "auth_mode": "login",
            "page": "home", "section": None, "playing": None}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TOPIC DETAIL (individual section like Openings, Endgame etc.)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.logged_in and st.session_state.page == "section":
    sec_key = st.session_state.section
    sec     = SECTIONS[sec_key]

    # Back button
    if st.button("← Back to Lessons"):
        st.session_state.page = "lessons"
        st.rerun()

    # Header
    st.markdown(f"""
    <div style='background:#111;border:1px solid rgba(255,255,255,0.07);
                border-left:4px solid {sec["color"]};border-radius:6px;
                padding:1.5rem;margin-bottom:1.2rem'>
        <div style='font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;
                    color:{sec["color"]};margin-bottom:0.4rem'>Chess Academy · {sec_key}</div>
        <div style='font-family:Cinzel,serif;font-size:1.6rem;color:#e8b84b;margin-bottom:0.3rem'>{sec_key}</div>
        <div style='color:rgba(237,232,223,0.5);font-size:0.82rem;font-style:italic;margin-bottom:0.8rem'>{sec["tagline"]}</div>
        <div style='width:36px;height:2px;background:{sec["color"]};margin-bottom:0.8rem'></div>
        <div style='color:rgba(237,232,223,0.7);font-size:0.85rem;line-height:1.8'>{sec["intro"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Principles
    st.markdown(f"<div style='font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:{sec['color']};margin-bottom:0.7rem'>Core Principles</div>", unsafe_allow_html=True)
    for i, p in enumerate(sec["principles"], 1):
        st.markdown(f"<div class='principle'><b style='color:{sec['color']}'>{i}.</b> {p}</div>", unsafe_allow_html=True)

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

    # Topics
    st.markdown(f"<div style='font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:{sec['color']};margin-bottom:0.7rem'>Topics in This Module</div>", unsafe_allow_html=True)
    for t in sec["topics"]:
        badge = t["level"].lower()
        st.markdown(f"""
        <div class='topic-card'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                <div class='topic-name'>{t['name']}</div>
                <span class='badge {badge}'>{t['level']}</span>
            </div>
            <div class='topic-moves'>{t['moves']}</div>
            <div class='topic-desc'>{t['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    if st.button("← Back to Lessons ", key="back2"):
        st.session_state.page = "lessons"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CHESS LESSONS (list of all sections)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.logged_in and st.session_state.page == "lessons":

    st.markdown(f"<div style='color:#c9922e;font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;margin-bottom:0.8rem'>Signed in as {st.session_state.username}</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:Cinzel,serif;font-size:1.5rem;color:#e8b84b;margin-bottom:1.2rem'>♚ Chess Lessons</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:rgba(237,232,223,0.5);font-size:0.82rem;margin-bottom:1.2rem'>Tap a module to open it</div>", unsafe_allow_html=True)

    for key, sec in SECTIONS.items():
        st.markdown(f"""
        <div class='section-card' style='border-left:3px solid {sec["color"]}'>
            <div class='section-title'>{key}</div>
            <div class='section-sub'>{sec["tagline"]}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Open {key} →", key=f"open_{key}"):
            st.session_state.section = key
            st.session_state.page    = "section"
            st.rerun()

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: VIDEO LESSONS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.logged_in and st.session_state.page == "videos":

    st.markdown(f"<div style='color:#c9922e;font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;margin-bottom:0.8rem'>Signed in as {st.session_state.username}</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:Cinzel,serif;font-size:1.5rem;color:#e8b84b;margin-bottom:1.2rem'>🎬 Video Lessons</div>", unsafe_allow_html=True)

    VIDEOS = [
        {"title":"How To Study Chess Openings",          "channel":"GothamChess",  "id":"6IegDENuxU4"},
        {"title":"Best Chess Openings by Rating",        "channel":"GothamChess",  "id":"NFod-ozimmM"},
        {"title":"Play the Sicilian Defense",            "channel":"GothamChess",  "id":"65VWIFlc4C4"},
        {"title":"Learn the Italian Game",               "channel":"Igor Smirnov", "id":"MhNs8GLo894"},
        {"title":"HOW TO WIN AT CHESS",                  "channel":"GothamChess",  "id":"KjqpLdO3_CU"},
        {"title":"Top 10 Endgame Principles",            "channel":"Igor Smirnov", "id":"uszf3ZRxYMo"},
        {"title":"Endgames Like Magnus Carlsen",         "channel":"GothamChess",  "id":"IvxhIozo_zo"},
        {"title":"4 Rules to Dominate Middlegame",       "channel":"Igor Smirnov", "id":"d_QMomOh-3U"},
        {"title":"Chess Tips: How To Make a Plan",       "channel":"GothamChess",  "id":"u8MKyE9Qt8I"},
        {"title":"Top 10 Attacking Concepts",            "channel":"Igor Smirnov", "id":"3sWxNXMnzM4"},
    ]

    for i, v in enumerate(VIDEOS):
        cc = "#ff6060" if v["channel"] == "GothamChess" else "#60a0ff"
        ci = "🔴" if v["channel"] == "GothamChess" else "🔵"
        st.markdown(f"""
        <div class='section-card'>
            <div class='section-title'>{v["title"]}</div>
            <div style='color:{cc};font-size:0.72rem;text-transform:uppercase;letter-spacing:0.1em'>{ci} {v["channel"]}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"▶ Watch Now", key=f"v{i}"):
            st.session_state.playing = v
            st.rerun()

    if st.session_state.playing:
        v = st.session_state.playing
        st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-family:Cinzel,serif;color:#e8b84b;margin-bottom:0.7rem'>▶ {v['title']}</div>", unsafe_allow_html=True)
        st.components.v1.iframe(f"https://www.youtube.com/embed/{v['id']}?autoplay=1", height=320)
        if st.button("✕ Close Video"):
            st.session_state.playing = None
            st.rerun()

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    if st.button("← Back to Home"):
        st.session_state.page    = "home"
        st.session_state.playing = None
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME (after login)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.logged_in and st.session_state.page == "home":

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#111,#181818);
                border:1px solid rgba(255,255,255,0.07);border-left:4px solid #c9922e;
                border-radius:6px;padding:1.8rem;text-align:center;margin-bottom:1.5rem'>
        <div style='font-size:2.5rem'>♚</div>
        <div style='font-family:Cinzel,serif;font-size:1.7rem;color:#e8b84b;margin-bottom:0.3rem'>
            Welcome, {st.session_state.username}!
        </div>
        <div style='color:rgba(237,232,223,0.5);font-size:0.85rem'>Signed in to Chess Academy</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-family:Cinzel,serif;color:#e8b84b;font-size:0.95rem;text-align:center;margin-bottom:1rem'>What would you like to do?</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='section-card' style='text-align:center'>
        <div style='font-size:2rem'>♟</div>
        <div class='section-title' style='text-align:center'>Chess Lessons</div>
        <div class='section-sub'>Openings · Middlegame · Endgame · Strategy · Classics</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Chess Lessons →", key="go_lessons"):
        st.session_state.page = "lessons"
        st.rerun()

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='section-card' style='text-align:center'>
        <div style='font-size:2rem'>🎬</div>
        <div class='section-title' style='text-align:center'>Video Lessons</div>
        <div class='section-sub'>GothamChess 🔴 &amp; Igor Smirnov 🔵</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Video Lessons →", key="go_videos"):
        st.session_state.page = "videos"
        st.rerun()

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out"):
        for k in ["logged_in","username","page","section","playing"]:
            st.session_state[k] = False if k == "logged_in" else ("home" if k == "page" else (None if k in ["section","playing"] else ""))
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LOGIN / SIGNUP
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("""
    <div class='hero-box'>
        <div class='hero-title'>♚ Chess Academy</div>
        <div style='color:#c9922e;font-size:0.7rem;letter-spacing:0.2em;text-transform:uppercase;margin:0.4rem 0'>Sign In to Continue</div>
        <div class='hero-sub'>Learn chess — openings, tactics, endgames &amp; video lessons</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔑 Sign In"):
            st.session_state.auth_mode = "login"; st.rerun()
    with c2:
        if st.button("📝 Sign Up"):
            st.session_state.auth_mode = "signup"; st.rerun()

    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        st.markdown("<div style='font-family:Cinzel,serif;font-size:1.1rem;color:#e8b84b;text-align:center;margin-bottom:1rem'>🔑 Sign In</div>", unsafe_allow_html=True)
        user = st.text_input("Username", placeholder="Your username", key="li_u")
        pwd  = st.text_input("Password", placeholder="Your password", type="password", key="li_p")
        if st.button("Sign In →"):
            if not user or not pwd:
                st.markdown("<div class='error-box'>⚠ Fill in all fields!</div>", unsafe_allow_html=True)
            else:
                ok, msg = login_user(user, pwd)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username  = user
                    st.session_state.page      = "home"
                    st.rerun()
                else:
                    st.markdown(f"<div class='error-box'>❌ {msg}</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:rgba(237,232,223,0.35);font-size:0.8rem;margin-top:0.8rem'>No account? Tap Sign Up above</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-family:Cinzel,serif;font-size:1.1rem;color:#e8b84b;text-align:center;margin-bottom:1rem'>📝 Create Account</div>", unsafe_allow_html=True)
        nu = st.text_input("Username",         placeholder="Choose a username",     key="su_u")
        ne = st.text_input("Email",            placeholder="Your email",            key="su_e")
        np = st.text_input("Password",         placeholder="Min 6 characters",      type="password", key="su_p")
        nc = st.text_input("Confirm Password", placeholder="Repeat password",       type="password", key="su_c")
        if st.button("Create Account →"):
            if not nu or not ne or not np or not nc:
                st.markdown("<div class='error-box'>⚠ Fill in all fields!</div>", unsafe_allow_html=True)
            elif np != nc:
                st.markdown("<div class='error-box'>❌ Passwords do not match!</div>", unsafe_allow_html=True)
            else:
                ok, msg = register_user(nu, np, ne)
                if ok:
                    st.markdown(f"<div class='success-box'>✅ {msg} Please sign in now.</div>", unsafe_allow_html=True)
                    st.session_state.auth_mode = "login"; st.rerun()
                else:
                    st.markdown(f"<div class='error-box'>❌ {msg}</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:rgba(237,232,223,0.35);font-size:0.8rem;margin-top:0.8rem'>Already have an account? Tap Sign In above</div>", unsafe_allow_html=True)

st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:rgba(237,232,223,0.18);font-size:0.7rem'>♚ Chess Academy</div>", unsafe_allow_html=True)
