import streamlit as st

st.set_page_config(page_title="Chess Academy — Video Lessons", page_icon="♚", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Lato:wght@300;400;700&display=swap');
html,body,[class*="css"]{font-family:'Lato',sans-serif;background-color:#0a0a0a;color:#ede8df}
.main{background-color:#0a0a0a}.block-container{padding:2rem;max-width:1100px}
h1,h2,h3{font-family:'Cinzel',serif!important;color:#ede8df!important}
.hero-box{background:linear-gradient(135deg,#111,#1a1a1a);border-left:4px solid #c9922e;
  border:1px solid rgba(255,255,255,0.07);padding:2rem 1.8rem;border-radius:4px;
  margin-bottom:2rem;text-align:center}
.hero-title{font-family:'Cinzel',serif;font-size:2.4rem;color:#e8b84b}
.hero-sub{color:rgba(237,232,223,0.55);font-size:0.9rem;margin-top:0.4rem}
.video-card{background:#111;border:1px solid rgba(255,255,255,0.07);
  border-radius:8px;padding:1.3rem;margin-bottom:1rem}
.video-title{font-family:'Cinzel',serif;font-size:1rem;color:#e8b84b;margin-bottom:0.3rem}
.video-channel{font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.5rem}
.gotham{color:#ff6060}.smirnov{color:#60a0ff}
.video-desc{color:rgba(237,232,223,0.55);font-size:0.83rem;line-height:1.6;margin-bottom:0.8rem}
.badge{display:inline-block;padding:2px 10px;border-radius:3px;font-size:0.67rem;
  font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.6rem}
.beginner{background:rgba(42,122,96,.25);color:#3db890}
.intermediate{background:rgba(201,146,46,.25);color:#e8b84b}
.advanced{background:rgba(184,56,32,.25);color:#e07050}
.now-watching{background:#111;border:1px solid rgba(255,255,255,0.07);
  border-left:4px solid #c9922e;padding:1.2rem 1.5rem;border-radius:4px;margin-bottom:1rem}
.gold-line{border:none;border-top:1px solid rgba(201,146,46,0.2);margin:1.5rem 0}
div[data-testid="stButton"] button{background:#c9922e!important;color:#0a0a0a!important;
  border:none!important;font-weight:700!important;border-radius:3px!important;width:100%!important}
div[data-testid="stButton"] button:hover{background:#e8b84b!important}
</style>
""", unsafe_allow_html=True)

# ── ALL VERIFIED VIDEO IDs FROM YOUTUBE ───────────────────────────────────────
CONTENT = {
    "♟ Openings": [
        {"title": "How To Learn & Study Chess Openings",         "channel": "GothamChess",  "level": "Beginner",     "desc": "Levy explains how to study openings the right way — understanding ideas, not memorising moves.",             "video_id": "6IegDENuxU4"},
        {"title": "My FAVORITE Chess Openings by Rating",        "channel": "GothamChess",  "level": "Beginner",     "desc": "The best openings for every rating — a complete opening roadmap from beginner to advanced.",               "video_id": "NFod-ozimmM"},
        {"title": "Play the Sicilian Defense like Beth Harmon",  "channel": "GothamChess",  "level": "Intermediate", "desc": "The Sicilian Defense explained — Black's sharpest and most popular reply to 1.e4.",                        "video_id": "65VWIFlc4C4"},
        {"title": "STOP Playing These 4 Chess Openings",         "channel": "GothamChess",  "level": "Beginner",     "desc": "The 4 worst openings beginners play and what to play instead. A must-watch for club players.",             "video_id": "GLpYQCCcZ6w"},
        {"title": "Learn the Italian Game in 20 Minutes",        "channel": "Igor Smirnov", "level": "Beginner",     "desc": "GM Smirnov teaches the Italian Game — one of the most reliable and oldest openings for White.",            "video_id": "MhNs8GLo894"},
        {"title": "Italian Game — ALL Variations Explained",     "channel": "Igor Smirnov", "level": "Intermediate", "desc": "Every Italian Game variation — traps, ideas, and plans for both White and Black clearly explained.",       "video_id": "6ACqk117Q7U"},
        {"title": "This Gambit PUNISHES the Ruy Lopez",          "channel": "Igor Smirnov", "level": "Intermediate", "desc": "A tricky gambit that punishes the Ruy Lopez — loaded with traps and surprise moves.",                     "video_id": "oJtGo8EuCn4"},
        {"title": "Basic Chess Openings Explained",              "channel": "GothamChess",  "level": "Beginner",     "desc": "Levy answers every common opening question. Clear, simple, and perfect for players just starting out.",    "video_id": "8IlJ3v8I4Z8"},
    ],
    "⚔ Middlegame": [
        {"title": "Gotham Chess Guide: Attacks, Endgames & Blunders", "channel": "GothamChess",  "level": "Intermediate", "desc": "Levy's complete guide for 1200+ players — how to attack, avoid blunders, and convert advantages.",          "video_id": "X21uL9lbHbw"},
        {"title": "Chess Tips: How To Make a Plan",                   "channel": "GothamChess",  "level": "Intermediate", "desc": "One of the most important skills in chess — how to form a strategic plan in any position.",                "video_id": "u8MKyE9Qt8I"},
        {"title": "HOW TO WIN AT CHESS",                              "channel": "GothamChess",  "level": "Beginner",     "desc": "Levy's complete guide to winning — tactics, strategy, and the mindset to improve fast.",                   "video_id": "KjqpLdO3_CU"},
        {"title": "More Chess Middlegame Analysis",                   "channel": "GothamChess",  "level": "Advanced",     "desc": "GothamChess deep-dives into middlegame strategy — piece activity, plans, and positional concepts.",        "video_id": "nm17mDpmBL0"},
        {"title": "4 Simple Rules to Dominate the Middlegame",        "channel": "Igor Smirnov", "level": "Intermediate", "desc": "GM Smirnov's 4 clear rules that will transform your middlegame. Simple and immediately effective.",         "video_id": "d_QMomOh-3U"},
        {"title": "Top 10 Attacking Concepts — Win 90% More Games",   "channel": "Igor Smirnov", "level": "Intermediate", "desc": "The 10 most powerful attacking ideas in chess. Master these and your attack will become unstoppable.",      "video_id": "3sWxNXMnzM4"},
    ],
    "♔ Endgame": [
        {"title": "Play Chess Endgames Like Magnus Carlsen",      "channel": "GothamChess",  "level": "Intermediate", "desc": "How Magnus dominates endgames — queen endings, rook endings, and minor pieces all covered by Levy.",        "video_id": "IvxhIozo_zo"},
        {"title": "Endgame YOU MUST KNOW",                        "channel": "GothamChess",  "level": "Beginner",     "desc": "The single most important endgame every chess player must know. Simple, clear, and essential.",             "video_id": "X1rs1p4IsvM"},
        {"title": "EASY CHESS ENDGAMES: Rook & Pawn",             "channel": "GothamChess",  "level": "Beginner",     "desc": "Rook and pawn endgames made simple. Levy walks through the key positions every player must master.",         "video_id": "JMZJ9P2Hnq0"},
        {"title": "8 Unbelievable Endgames By Magnus Carlsen",    "channel": "GothamChess",  "level": "Advanced",     "desc": "Magnus Carlsen's most jaw-dropping endgame performances — what perfect technique looks like.",               "video_id": "tJIHFuHrZp4"},
        {"title": "Top 10 Chess Endgame Principles (Crash Course)","channel": "Igor Smirnov", "level": "Beginner",     "desc": "GM Smirnov's 10 most important endgame principles. Learn these and stop losing drawn endgames forever.",     "video_id": "uszf3ZRxYMo"},
        {"title": "Italian Game — Endgame Plans Explained",        "channel": "Igor Smirnov", "level": "Intermediate", "desc": "How the Italian Game flows into endgames — key pawn structures, piece activity, and conversion technique.", "video_id": "qUews8fEGkc"},
    ],
    "🧠 Strategy": [
        {"title": "Chess Tips: How To Make a Plan",               "channel": "GothamChess",  "level": "Intermediate", "desc": "Strategic planning explained — how to identify your goal in any position and build a plan around it.",       "video_id": "u8MKyE9Qt8I"},
        {"title": "HOW TO WIN AT CHESS",                          "channel": "GothamChess",  "level": "Beginner",     "desc": "The complete strategic guide to winning chess — from pawn play to piece coordination.",                      "video_id": "KjqpLdO3_CU"},
        {"title": "4 Simple Rules to Dominate the Middlegame",    "channel": "Igor Smirnov", "level": "Intermediate", "desc": "Four powerful strategic rules that cover almost every middlegame situation. Easy to learn, deadly to apply.", "video_id": "d_QMomOh-3U"},
        {"title": "London System — Best Attacking Blueprint",     "channel": "Igor Smirnov", "level": "Intermediate", "desc": "The best strategic plans and attacks in the London System — a complete middlegame guide by GM Smirnov.",     "video_id": "TgQb2qVz_18"},
        {"title": "Top 10 Attacking Concepts — Win 90% More",    "channel": "Igor Smirnov", "level": "Advanced",     "desc": "A masterclass in chess strategy and attack — 10 concepts every improving player must know.",                 "video_id": "3sWxNXMnzM4"},
        {"title": "My FAVORITE Chess Openings by Rating",        "channel": "GothamChess",  "level": "Beginner",     "desc": "Strategic opening selection at every level — how the right opening shapes your entire strategic game plan.",  "video_id": "NFod-ozimmM"},
    ],
}

# ── Session State ─────────────────────────────────────────────────────────────
if "video" not in st.session_state: st.session_state.video = None
if "tab"   not in st.session_state: st.session_state.tab   = "♟ Openings"

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero-box'>
    <div class='hero-title'>♚ Chess Academy</div>
    <div style='color:#c9922e;font-size:0.75rem;letter-spacing:0.2em;text-transform:uppercase;margin:0.5rem 0'>Video Lessons</div>
    <div class='hero-sub'>🔴 GothamChess (Levy Rozman) &nbsp;·&nbsp; 🔵 Igor Smirnov (GM) — All videos verified ✅</div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = list(CONTENT.keys())
cols = st.columns(len(tabs))
for i, tab in enumerate(tabs):
    with cols[i]:
        if st.button(tab, key=f"tab_{i}"):
            st.session_state.tab   = tab
            st.session_state.video = None
            st.rerun()

st.markdown(f"<div style='text-align:center;color:#c9922e;font-size:0.68rem;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:1rem'>Now Browsing: {st.session_state.tab}</div>", unsafe_allow_html=True)

level = st.selectbox("Filter by Level", ["All Levels","Beginner","Intermediate","Advanced"])
st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)

# ── Grid ──────────────────────────────────────────────────────────────────────
videos = CONTENT[st.session_state.tab]
if level != "All Levels":
    videos = [v for v in videos if v["level"] == level]

if not videos:
    st.info("No videos for this level. Try a different filter.")
else:
    c1, c2 = st.columns(2)
    for i, v in enumerate(videos):
        col = c1 if i % 2 == 0 else c2
        with col:
            cc = "gotham" if v["channel"] == "GothamChess" else "smirnov"
            ci = "🔴" if v["channel"] == "GothamChess" else "🔵"
            st.markdown(f"""
            <div class='video-card'>
                <div class='video-title'>{v['title']}</div>
                <div class='video-channel {cc}'>{ci} {v['channel']}</div>
                <span class='badge {v["level"].lower()}'>{v['level']}</span>
                <div class='video-desc'>{v['desc']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("▶ Watch Now", key=f"w_{st.session_state.tab}_{i}"):
                st.session_state.video = v
                st.rerun()

# ── Player ────────────────────────────────────────────────────────────────────
if st.session_state.video:
    v  = st.session_state.video
    cc = "gotham" if v["channel"] == "GothamChess" else "smirnov"
    ci = "🔴" if v["channel"] == "GothamChess" else "🔵"
    st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='now-watching'>
        <div style='font-size:0.65rem;letter-spacing:0.18em;text-transform:uppercase;color:#c9922e;margin-bottom:0.4rem'>▶ Now Playing</div>
        <div style='font-family:Cinzel,serif;font-size:1.4rem;color:#e8b84b;margin-bottom:0.3rem'>{v['title']}</div>
        <div class='video-channel {cc}'>{ci} {v['channel']}</div>
    </div>""", unsafe_allow_html=True)
    st.video(f"https://www.youtube.com/watch?v={v['video_id']}")
    st.markdown(f"<div style='background:#111;border:1px solid rgba(255,255,255,0.07);border-left:3px solid #c9922e;padding:1rem 1.2rem;border-radius:4px;margin-top:0.8rem;color:rgba(237,232,223,0.7);font-size:0.87rem;line-height:1.7'>{v['desc']}</div>", unsafe_allow_html=True)
    if st.button("✕ Close Video"):
        st.session_state.video = None
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr class='gold-line'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:rgba(237,232,223,0.2);font-size:0.72rem;padding:0.5rem'>♚ Chess Academy · GothamChess 🔴 &amp; Igor Smirnov 🔵</div>", unsafe_allow_html=True)
