"""The 30-day story skeleton, authored backward from its payoffs.

Threads with deliberate shapes:
  - iclr_rebuttal : the spine — stays hot the whole month, urgency climbs.
  - compute       : H100 grant (a needle to retain).
  - labmeeting    : a CONFLICT — time set on n5, moved on n11 (must reconcile, not double-store).
  - collab_fizzle : a thread that goes silent (must be allowed to fade — hero moment for forgetting).
  - pref_memory   : user keeps saving memory/agent papers (infer a durable, un-hand-coded interest).
  - insight       : the planted latent connection (premise n6 + premise n13 -> synth n15 -> confirm n22).
  - noise         : newsletters / recruiter spam / promos (the control the system must ignore).

Ground-truth labels live here in the script, independent of any generated body text — that
independence is what keeps the evaluation non-circular.
"""
from __future__ import annotations

PERSONA = (
    "Maya Chen, a 2nd-year CS PhD student at a research university, preparing an ICLR "
    "submission on agent memory. Works with an advisor and a small lab; reads heavily on "
    "memory systems and agents."
)

# Stable ids for the two latent-insight premises (referenced by INSIGHT below).
PREMISE_X = "n06-arxiv-1"   # technique X: consolidation reduces interference
PREMISE_Y = "n13-notes-1"   # anomaly Y: accuracy drops as the store grows

# Each beat: (id, night, source, sender, subject, body, thread, label)
BEATS: list[dict] = [
    # --- preferences / setup ---
    dict(id="n01-notes-1", night=1, source="notes", sender="self",
         subject="Saved to read: MemGPT",
         body="Saved MemGPT (virtual context management, paging between in-context and external "
              "memory). Relevant to my memory-rewrite idea.",
         thread="pref_memory", label="needle"),

    # --- rebuttal arc (the spine) ---
    dict(id="n02-gmail-1", night=2, source="gmail", sender="iclr-pcs@iclr.cc",
         subject="Your ICLR submission: reviews available",
         body="Reviews are in for 'Structured Memory Rewrite for Sleep-Time Agents'. "
              "Scores: 6, 6, 4. Reviewer 2 (score 4) is the one to address.",
         thread="iclr_rebuttal", label="needle"),
    dict(id="n03-gmail-1", night=3, source="gmail", sender="iclr-pcs@iclr.cc",
         subject="Re: reviewer 2 detailed comments",
         body="Reviewer 2: 'The paper does not isolate whether gains come from the rewrite "
              "operations or merely from having any memory. An ablation comparing rewrite vs. "
              "naive append is needed; without it I lean reject.'",
         thread="iclr_rebuttal", label="needle"),
    dict(id="n04-slack-1", night=4, source="slack", sender="advisor",
         subject="#lab: rebuttal plan",
         body="advisor: Let's prioritize the rewrite-vs-append ablation for the rebuttal. "
              "Rebuttal deadline is day 19 — we need results well before then.",
         thread="iclr_rebuttal", label="needle"),

    # --- collaboration that fizzles (forgetting target) ---
    dict(id="n03-gmail-2", night=3, source="gmail", sender="d.okafor@otherschool.edu",
         subject="Co-author a workshop paper?",
         body="Hey Maya — want to co-author a quick workshop paper on agent-memory benchmarks? "
              "Could be low effort. Let me know!",
         thread="collab_fizzle", label="context"),
    dict(id="n04-gmail-2", night=4, source="gmail", sender="d.okafor@otherschool.edu",
         subject="Re: Co-author a workshop paper?",
         body="Following up — sketched a rough outline, take a look when you have a sec.",
         thread="collab_fizzle", label="context"),
    dict(id="n06-slack-1", night=6, source="slack", sender="d.okafor",
         subject="dm: workshop paper",
         body="d.okafor: still keen on that workshop paper? no rush at all.",
         thread="collab_fizzle", label="context"),
    # ...then silence. A library would carry this forever; nocturne should let it fade.

    # --- the planted insight: premise X ---
    dict(id=PREMISE_X, night=6, source="arxiv", sender="arxiv-cs-ai",
         subject="New: Consolidation reduces cross-fact interference",
         body="Technique paper: periodically consolidating accumulated context into a compact "
              "summary reduces interference between unrelated facts, improving downstream recall. "
              "(Saved — relevant to my memory work.)",
         thread="insight", label="context"),

    # --- compute grant (needle) ---
    dict(id="n09-gmail-1", night=9, source="gmail", sender="cluster-admin@univ.edu",
         subject="H100 allocation approved",
         body="Your May allocation is approved: 2400 H100 GPU-hours. Quota resets monthly.",
         thread="compute", label="needle"),
    dict(id="n10-github-1", night=10, source="github", sender="ci-bot",
         subject="issue #214: kick off rewrite-vs-append ablation runs",
         body="Tracking issue opened for the rebuttal ablation sweep (rewrite vs append vs window).",
         thread="iclr_rebuttal", label="context"),

    # --- conflict: lab meeting time set, then moved ---
    dict(id="n05-cal-1", night=5, source="calendar", sender="calendar",
         subject="Weekly lab meeting scheduled",
         body="Recurring: Lab meeting every Thursday 14:00, room 311.",
         thread="labmeeting", label="needle"),
    dict(id="n11-gmail-1", night=11, source="gmail", sender="advisor",
         subject="Lab meeting moving",
         body="Heads up: moving the weekly lab meeting to Wednesdays 11:00 starting next week. "
              "Please update your calendar — the old Thursday 14:00 slot is dropped.",
         thread="labmeeting", label="needle"),

    # --- the planted insight: premise Y (the anomaly) ---
    dict(id=PREMISE_Y, night=13, source="notes", sender="self",
         subject="Experiment log: weird accuracy drop",
         body="Odd: in the append baseline, QA accuracy drops once the store grows past ~40 items "
              "even though the target fact is still in there. Not a retrieval miss — feels like "
              "the extra material is getting in the way.",
         thread="insight", label="context"),
    dict(id="n13-notes-2", night=13, source="notes", sender="self",
         subject="Saved: consolidation vs accumulation",
         body="Saved another memory paper arguing compression beats accumulation for working sets.",
         thread="pref_memory", label="needle"),

    # --- rebuttal results + submission ---
    dict(id="n16-notes-1", night=16, source="notes", sender="self",
         subject="Ablation results in",
         body="Rewrite beats naive append by ~9 F1 points on needle survival; append blows the "
              "token budget by day 20 of the sim. Clean result for the rebuttal.",
         thread="iclr_rebuttal", label="needle"),
    dict(id="n19-gmail-1", night=19, source="gmail", sender="iclr-pcs@iclr.cc",
         subject="Rebuttal received",
         body="Your author response for submission 4127 has been received (deadline day 19).",
         thread="iclr_rebuttal", label="needle"),

    # --- the insight confirmation (the jaw-dropper payoff) ---
    dict(id="n22-notes-1", night=22, source="notes", sender="self",
         subject="Bounded-memory variant works",
         body="Ran the bounded-memory variant: the accuracy drop is gone — recall held flat as the "
              "stream grew. Aggressive consolidation fixed it.",
         thread="insight", label="needle"),

    # --- more preference reinforcement ---
    dict(id="n18-arxiv-1", night=18, source="arxiv", sender="arxiv-cs-ai",
         subject="New: lifelong memory for agents",
         body="Another agent-memory paper. Saved to the reading list.",
         thread="pref_memory", label="context"),
    dict(id="n24-notes-1", night=24, source="notes", sender="self",
         subject="Saved: episodic memory survey",
         body="Saved a survey on episodic memory for LLM agents.",
         thread="pref_memory", label="context"),

    # --- camera-ready / resolution ---
    dict(id="n27-gmail-1", night=27, source="gmail", sender="iclr-pcs@iclr.cc",
         subject="Decision + camera-ready",
         body="Good news: Reviewer 2 raised their score from 4 to 6 after the rebuttal. "
              "Paper accepted; camera-ready due in two weeks.",
         thread="iclr_rebuttal", label="needle"),
]


NEEDLES = [
    dict(id="need-iclr", thread="iclr_rebuttal",
         description="Reviewer 2 wants a rewrite-vs-append ablation (rebuttal due day 19).",
         present_from_night=4, keywords=["reviewer 2", "ablation", "append"]),
    dict(id="need-compute", thread="compute",
         description="H100 allocation = 2400 GPU-hours.",
         present_from_night=9, keywords=["2400", "gpu"]),
    dict(id="need-labmeeting", thread="labmeeting",
         description="Lab meeting is now Wednesday 11:00 (moved from Thursday 14:00).",
         present_from_night=11, keywords=["wednesday", "11"]),
    dict(id="need-pref", thread="pref_memory",
         description="User has a durable interest in agent-memory papers.",
         present_from_night=13, keywords=["memory"]),
]


QA = [
    dict(id="q-r2", ask_night=6, thread="iclr_rebuttal",
         question="What does Reviewer 2 want addressed in the rebuttal?",
         answer="An ablation isolating the rewrite operations from naive append.",
         keywords=["ablation", "append"]),
    dict(id="q-gpu", ask_night=12, thread="compute",
         question="How many GPU-hours is the approved H100 allocation?",
         answer="2400 GPU-hours.", keywords=["2400"]),
    dict(id="q-meeting", ask_night=12, thread="labmeeting",
         question="What day and time is the lab meeting now?",
         answer="Wednesday 11:00.", keywords=["wednesday", "11"]),
    dict(id="q-deadline", ask_night=20, thread="iclr_rebuttal",
         question="When was the ICLR rebuttal due?",
         answer="Day 19.", keywords=["19"]),
    dict(id="q-pref", ask_night=25, thread="pref_memory",
         question="What research topic does the user consistently save papers about?",
         answer="Agent memory systems.", keywords=["memory"]),
    dict(id="q-r2-final", ask_night=28, thread="iclr_rebuttal",
         question="Did Reviewer 2 change their score after the rebuttal?",
         answer="Yes — raised from 4 to 6.", keywords=["6", "raised"]),
]


INSIGHT = dict(
    premise_item_ids=[PREMISE_X, PREMISE_Y],
    statement=("The append baseline's accuracy drop at scale is interference from accumulation; "
               "consolidation / bounded memory (the paper's technique X) fixes the anomaly Y — "
               "so aggressive consolidation, not accumulation, is the right bet."),
    keywords=["consolidat", "interfer", "bounded", "accumulat"],
    proposable_from_night=13,
    confirmed_by_night=22,
)


# Deterministic noise: subjects cycled per night so the trace is fixed and committable.
NOISE_SUBJECTS = [
    ("newsletter@thebatch.ai", "The Batch: this week in AI"),
    ("recruiter@bigtechco.com", "Exciting Staff ML Engineer opportunity!"),
    ("promos@deals.example", "50% off your favorite cloud GPUs (limited time)"),
    ("noreply@social.example", "You have 7 new connection requests"),
    ("calendar", "Reminder: campus parking permit renewal"),
    ("newsletter@importai.net", "Import AI: policy roundup"),
    ("sales@vectordb.example", "Is your RAG stack slow? Try our managed vector DB"),
    ("noreply@coursera.example", "New course recommendations for you"),
]
