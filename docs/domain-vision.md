# Domain Vision Statement — Tiferet Streamlit

**Status:** Draft · **Domain:** `tiferet-streamlit` · **Code:** `tiferet_streamlit/` · **Branch:** `main`

## The bet: a page is a declared view, not a script

Most Streamlit apps are written as one long script per page: pull some data, hold a few numbers in memory, draw some widgets, react to clicks, repeat. That works for a demo. It gets expensive the moment a team wants more than one page, wants the same button to behave the same way in two places, or wants to know what a session actually did after the fact — because none of that is written down anywhere except buried inside the script itself.

Tiferet Streamlit makes a different bet: a page should be a **declared view** — a small, named unit that owns its own state, hands its real logic off to a separate backend instead of burying it inline, and can be assembled into a multi-page app from configuration instead of a growing pile of hand-wired navigation code. The screen becomes a thin, predictable shell around a backend that already knows how to test itself, version itself, and be reused outside the browser entirely.

## What this domain makes real

This domain is the bridge between a Streamlit app's browser-facing surface — its pages, its widgets, its in-browser memory — and a Tiferet-built backend's business logic. It gives every page a consistent shape: a place to set up initial state once, a place to hold values that survive from one click to the next without leaking into other pages, a way to hand work off to the backend and get an answer back, and a way to assemble many such pages into one navigable application, either by hand or from a configuration file.

## What we get for it

**Pages that stay thin.** Because real logic is handed off rather than inlined, a page's code is almost entirely "what does this look like," not "what does this do." That is what makes a page reviewable in minutes instead of an afternoon.

**State that doesn't collide.** A Streamlit app's in-browser memory is shared across everything running in it. Left alone, two pages — or two copies of the same widget — can silently overwrite each other's values. This domain isolates each page's state behind its own name automatically, so that class of bug can't happen by accident.

**Apps that assemble instead of accumulate.** Multi-page Streamlit apps are usually built by hand-wiring one navigation call after another. Here, a page can instead be described — its route, its title, its icon, which code implements it — as data, and the running app is assembled from that description. Adding a page becomes a configuration change, not a code change to a growing central file.

**Less repetition per widget.** Today, every widget on a page is wired by hand: read a stored value, draw the widget, write the value back, decide whether to call the backend. A page with a dozen widgets repeats that pattern a dozen times. Making the common version of that wiring — keep a widget in sync with stored state, and call the backend when it changes — something you ask for once, instead of writing out every time, is a direct, near-term reduction in how much of a page has to be hand-assembled.

**A record of what actually happened.** Once a page hands work off to the backend today, there is no trace of it afterward — not for debugging, not for support, not for understanding how a session unfolded. Recording that a piece of work was requested, and what came back, turns "we think this is what the user did" into something that can actually be checked.

**A look that's declared, not hand-patched.** Streamlit ships its own default appearance and a way to configure it, but teams commonly end up hand-patching individual pages with one-off style tweaks that live nowhere consistent. Reaching that same native appearance system through configuration — the same way a page's routing already is — keeps a look consistent without turning every page into a place styling rules get invented from scratch.

## The core of the work

Every page in this domain follows the same shape: **set up** its state once, **render** its widgets against that state, **hand off** work to the backend when needed, and **remember** what state and requests happened along the way. A page is the smallest independently-testable unit; an app is a collection of pages assembled from either code or configuration. The central design commitment is that a page should never need to know how the backend does its job, only that it can ask and get an answer back — and that asking should leave a trace.

## What it deliberately does not do

It does not decide how backend logic works, validate data, or enforce business rules — that belongs to the Tiferet backend a page talks to. It does not replace Streamlit's own rendering, its widgets, or its native appearance controls — it reaches them through configuration rather than working around them. It does not promise to reconstruct a session's exact state from history alone; it promises to record what happened, which is a smaller and more honest claim than full replay. And it does not invent a styling system from scratch — it gives configuration a path to the appearance controls Streamlit already provides.

---

*Companion document:* `docs/core-domain-distillation.md` — the detailed
walkthrough of the domain's vocabulary, behaviors, and the relationships
between its parts.
