import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chess Academy — Video Lessons",
    page_icon="♚",
    layout="wide"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
    background-color: #0a0a0a;
    color: #ede8df;
}
.main { background-color: #0a0a0a; }
.block-container { padding: 2rem; max-width: 1100px; }
h1,h2,h3 { font-family: 'Cinzel', serif !important; color: #ede8df !important; }

.hero-box {
    background: linear-gradient(135deg, #111, #1a1a1a);
    border-left: 4px solid #c9922e;
    border: 1px solid rgba(255,255,255,0.07);
    padding: 2rem 1.8rem;
    border-radius: 4px;
    margin-bottom: 2rem;
    text-align: center;
}
.hero-title { font-family:'Cinzel',serif; font-size:2.4rem; color:#e8b84b; }
.hero-sub   { color:rgba(237,232,223,0.55); font-size:0.9rem; margin-top:0.4rem; }

/* Tab styling */
.tab-row {
    display: flex; gap: 0.6rem;
    margin-bottom: 1.8rem; flex-wrap: wrap;
}
.tab-btn {
    padding: 0.5rem 1.2rem;
    border-radius: 3px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    cursor: pointer;
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(237,232,223,0.6);
    background: #111;
}

/* Video card */
.video-card {
    background: #111;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 1.3rem;
    margin-bottom: 1rem;
}
.video-title {
    font-family: 'Cinzel', serif;
    font-size: 1.05rem;
    color: #e8b84b;
    margin-bottom: 0.3rem;
}
.video-channel {
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.gotham   { color: #e05050; }
.smirnov  { color: #5090e0; }
.video-desc {
    color: rgba(237,232,223,0.55);
    font-size: 0.83rem;
    line-height: 1.6;
    margin-bottom: 0.8rem;
}
.badge {
    display: inline-block;
    padding: 2px 10px; border-radius: 3px;
    font-size: 0.67rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.beginner     { background:rgba(42,122,96,.25);  color:#3db890; }
.intermediate { background:rgba(201,146,46,.25); color:#e8b84b; }
.advanced     { background:rgba(184,56,32,.25);  color:#e07050; }

.section-label {
    font-size:0.68rem; letter-spacing:0.2em;
    text-transform:uppercase; margin-bottom:0.8rem;
}
.gold-line { border:none; border-top:1px solid rgba(201,146,46,0.2); margin:1.5rem 0; }

.now-watching {
    background: #111;
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 4px solid #c9922e;
    padding: 1.2rem 1.5rem;
    border-radius: 4px;
    margin-bottom: 1rem;
}

div[data-testid="stButton"] button {
    background: #c9922e !important;
    color: #0a0a0a !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 3px !important;
    width: 100% !important;
}
div[data-testid="stButton"] button:hover { background: #e8b84b !important; }
</style>
""", unsafe_allow_html=True)

# ── Video Content Database ─────────────────────────────────────────────────────
# Channels: GothamChess (Levy Rozman) | Igor Smirnov (GM Igor Smirnov)
CONTENT = {
    "♟ Openings": [
        {
            "title":   "Italian Game — Complete Guide",
            "channel": "GothamChess",
            "level":   "Beginner",
            "desc":    "Levy walks through the Italian Game from start to finish — development, plans, and key traps to know.",
            "video_id": "lvRDnP718Qs",
        },
        {
            "title":   "Ruy López — Full Tutorial",
            "channel": "GothamChess",
            "level":   "Intermediate",
            "desc":    "The Spanish Opening explained — White's pressure on e5, the main lines, and how to handle Black's defenses.",
            "video_id": "dksvFKJbdOs",
        },
        {
            "title":   "Sicilian Defense — Everything You Need",
            "channel": "GothamChess",
            "level":   "Intermediate",
            "desc":    "The most popular opening at all levels. Levy covers the main variations and what makes the Sicilian so powerful.",
            "video_id": "oNOCMcHcSYI",
        },
        {
            "title":   "Queen's Gambit — How to Play It",
            "channel": "GothamChess",
            "level":   "Intermediate",
            "desc":    "White's best closed game weapon. Learn how to handle both the accepted and declined versions confidently.",
            "video_id": "bLBMEKGigrw",
        },
        {
            "title":   "King's Indian Defense",
            "channel": "GothamChess",
            "level":   "Advanced",
            "desc":    "Black's dynamic weapon against 1.d4. Counterattack the center and launch devastating kingside attacks.",
            "video_id": "FhXqFaHpjBo",
        },
        {
            "title":   "French Defense — Complete Guide",
            "channel": "GothamChess",
            "level":   "Beginner",
            "desc":    "A solid and reliable reply to 1.e4. Learn the key pawn breaks and how to activate the light-squared bishop.",
            "video_id": "VnTBqPRXOHU",
        },
    ],

    "⚔ Middlegame": [
        {
            "title":   "Chess Tactics — Forks, Pins & Skewers",
            "channel": "GothamChess",
            "level":   "Beginner",
            "desc":    "The three most important tactical patterns every chess player must know. Spot them instantly and win material.",
            "video_id": "sGgNPw5PDWE",
        },
        {
            "title":   "How to Attack in Chess",
            "channel": "GothamChess",
            "level":   "Intermediate",
            "desc":    "Levy breaks down how to build and launch a successful attack — from identifying weaknesses to delivering checkmate.",
            "video_id": "pGDVHBGLADY",
        },
        {
            "title":   "Discovered Attacks & Double Checks",
            "channel": "Igor Smirnov",
            "level":   "Intermediate",
            "desc":    "GM Igor Smirnov explains discovered attacks and double checks — some of the most powerful tactical weapons in chess.",
            "video_id": "8afFCOkgkqk",
        },
        {
            "title":   "How to Find the Best Move",
            "channel": "Igor Smirnov",
            "level":   "Intermediate",
            "desc":    "A systematic approach to calculation. Learn GM Smirnov's proven method to find strong moves in any position.",
            "video_id": "1xSJoMNWqYI",
        },
        {
            "title":   "Piece Coordination — Winning Strategy",
            "channel": "Igor Smirnov",
            "level":   "Advanced",
            "desc":    "How to coordinate all your pieces to work together as a team. A key skill that separates good players from great ones.",
            "video_id": "4jtVMRFsVbw",
        },
        {
            "title":   "Pawn Structure — Master the Middlegame",
            "channel": "GothamChess",
            "level":   "Intermediate",
            "desc":    "Understanding pawn structure is the key to forming long-term plans. Levy explains isolated, passed, and doubled pawns.",
            "video_id": "JjzGqMoFGaI",
        },
    ],

    "♔ Endgame": [
        {
            "title":   "King & Pawn Endgames — Full Guide",
            "channel": "GothamChess",
            "level":   "Beginner",
            "desc":    "The foundation of all endgame theory. Learn the opposition, key squares, and how to promote your pawn every time.",
            "video_id": "XpYGgPzYQW4",
        },
        {
            "title":   "Rook Endings — Lucena & Philidor",
            "channel": "GothamChess",
            "level":   "Intermediate",
            "desc":    "The two most important rook endgame positions in chess. Master these and you will save and win countless games.",
            "video_id": "RokcVZNJMg0",
        },
        {
            "title":   "Basic Checkmates You Must Know",
            "channel": "GothamChess",
            "level":   "Beginner",
            "desc":    "Queen vs King and Rook vs King checkmates explained simply. Every player must know these patterns cold.",
            "video_id": "jmDwSFBqJDI",
        },
        {
            "title":   "Endgame Secrets — Win More Games",
            "channel": "Igor Smirnov",
            "level":   "Intermediate",
            "desc":    "GM Smirnov reveals the most important endgame principles that most players never learn. Improve your technique fast.",
            "video_id": "8bPkFLg9ALk",
        },
        {
            "title":   "Zugzwang — The Deadly Endgame Weapon",
            "channel": "Igor Smirnov",
            "level":   "Intermediate",
            "desc":    "How to use zugzwang to force your opponent into losing positions. One of the most powerful endgame concepts.",
            "video_id": "4mBBFQkHSPE",
        },
        {
            "title":   "Bishop vs Knight Endings",
            "channel": "Igor Smirnov",
            "level":   "Advanced",
            "desc":    "When is the bishop better than the knight? GM Smirnov explains the key factors and how to convert these endings.",
            "video_id": "3VDRtQUEbHo",
        },
    ],

    "🧠 Strategy": [
        {
            "title":   "Chess Strategy for Beginners",
            "channel": "GothamChess",
            "level":   "Beginner",
            "desc":    "Levy's complete guide to chess strategy — how to form plans, identify weaknesses, and think long-term in any position.",
            "video_id": "UiQGKmxXEBE",
        },
        {
            "title":   "How to Create a Plan in Chess",
            "channel": "Igor Smirnov",
            "level":   "Intermediate",
            "desc":    "GM Smirnov teaches a clear system for forming strategic plans. Stop making random moves and start playing with purpose.",
            "video_id": "vZzZFdFPCsU",
        },
        {
            "title":   "Weak Squares & Outposts",
            "channel": "Igor Smirnov",
            "level":   "Intermediate",
            "desc":    "How to identify weak squares in your opponent's position and use them as permanent outposts for your pieces.",
            "video_id": "7lGQAJqbnPQ",
        },
        {
            "title":   "Prophylaxis — Think Like Petrosian",
            "channel": "GothamChess",
            "level":   "Advanced",
            "desc":    "The art of preventing your opponent's plans before they happen. The most underrated skill in chess explained clearly.",
            "video_id": "iCJiVqVcKnw",
        },
        {
            "title":   "Pawn Breaks — Unlock Your Position",
            "channel": "Igor Smirnov",
            "level":   "Intermediate",
            "desc":    "When and how to use pawn breaks to open files, activate pieces, and shatter your opponent's structure.",
            "video_id": "2nADpBdXFzI",
        },
        {
            "title":   "Space Advantage — How to Use It",
            "channel": "Igor Smirnov",
            "level":   "Advanced",
            "desc":    "Having more space means more options. GM Smirnov shows how to convert a space advantage into a winning attack.",
            "video_id": "6pOsDkLm5Jk",
        },
    ],
}

# ── Session State ─────────────────────────────────────────────────────────────
if "selected_video" not in st.session_state:
    st.session_state.selected_video = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "♟ Openings"

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero-box'>
    <div class='hero-title'>♚ Chess Academy</div>
    <div style='color:#c9922e;font-size:0.75rem;letter-spacing:0.2em;text-transform:uppercase;margin:0.4rem 0'>
        Video Lessons — GothamChess & Igor Smirnov
    </div>
    <div class='hero-sub'>Watch and learn from the best chess educators on YouTube</div>
</div>
""", unsafe_allow_html=True)

# ── Tab Navigation ────────────────────────────────────────────────────────────
tabs = list(CONTENT.keys())
cols = st.columns(len(tabs))
for i, tab in enumerate(tabs):
    with cols[i]:
        if st.button(tab, key=f"tab_{i}"):
            st.session_state.active_tab = tab
            st.session_state.selected_video = None
            st.rerun()

active = st.session_state.active_tab

# Show active tab indicator
st.markdown(f"""
<div style='text-align:center;color:#c9922e;font-size:0.7rem;
            letter-spacing:0.15em;text-transform:uppercase;margin-bottom:1.5rem'>
    Now Browsing: {active}
</div>
""", unsafe_allow_html=True)

# ── Level Filter ──────────────────────────────────────────────────────────────
level_filter = st.selectbox(
    "Filter by Level",
    ["All Levels", "Beginner", "Intermediate", "Advanced"],
    key="level_filter"
)

st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

# ── Video Grid ────────────────────────────────────────────────────────────────
videos = CONTENT[active]
if level_filter != "All Levels":
    videos = [v for v in videos if v["level"] == level_filter]

col1, col2 = st.columns(2)

for i, video in enumerate(videos):
    col = col1 if i % 2 == 0 else col2
    with col:
        channel_class = "gotham" if video["channel"] == "GothamChess" else "smirnov"
        channel_icon  = "🔴" if video["channel"] == "GothamChess" else "🔵"
        badge_class   = video["level"].lower()

        st.markdown(f"""
        <div class='video-card'>
            <div class='video-title'>{video['title']}</div>
            <div class='video-channel {channel_class}'>{channel_icon} {video['channel']}</div>
            <span class='badge {badge_class}'>{video['level']}</span>
            <div class='video-desc'>{video['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"▶ Watch Now", key=f"watch_{active}_{i}"):
            st.session_state.selected_video = video
            st.rerun()

# ── Video Player ──────────────────────────────────────────────────────────────
if st.session_state.selected_video:
    video = st.session_state.selected_video
    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

    channel_class = "gotham" if video["channel"] == "GothamChess" else "smirnov"
    channel_icon  = "🔴" if video["channel"] == "GothamChess" else "🔵"

    st.markdown(f"""
    <div class='now-watching'>
        <div style='font-size:0.68rem;letter-spacing:0.18em;text-transform:uppercase;
                    color:#c9922e;margin-bottom:0.4rem'>▶ Now Playing</div>
        <div style='font-family:Cinzel,serif;font-size:1.5rem;
                    color:#e8b84b;margin-bottom:0.3rem'>{video['title']}</div>
        <div class='video-channel {channel_class}'>{channel_icon} {video['channel']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Play the YouTube video
    st.video(f"https://www.youtube.com/watch?v={video['video_id']}")

    st.markdown(f"""
    <div style='background:#111;border:1px solid rgba(255,255,255,0.07);
                border-left:3px solid #c9922e;padding:1rem 1.2rem;
                border-radius:4px;margin-top:0.8rem;
                color:rgba(237,232,223,0.7);font-size:0.87rem;line-height:1.7'>
        {video['desc']}
    </div>
    """, unsafe_allow_html=True)

    if st.button("✕ Close Video"):
        st.session_state.selected_video = None
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;color:rgba(237,232,223,0.25);font-size:0.75rem;padding:0.5rem'>
    ♚ Chess Academy · Videos from GothamChess 🔴 &amp; Igor Smirnov 🔵
</div>
""", unsafe_allow_html=True)
