# LAWSEER

> **See how a decision changes before you make it.**

LAWSEER is an educational counterfactual decision simulator for civic and legal-style situations. It is not a generic legal chatbot, document summarizer, RAG Q&A app, or legal advice generator. The LexHack 2026 demo focuses on one question: how does a decision graph change when one fact changes?

## Problem

People often face a time-sensitive request with incomplete records. A single answer can hide the assumptions that shaped it. LAWSEER makes those assumptions inspectable: it structures the situation, marks uncertainty, models procedural dependencies, and compares possible action paths.

## Novel Mechanism

The primary scenario is a tenant receiving a sudden request from a landlord to leave within a short period. The user can compare:

- **A. Leave immediately**
- **B. Ask for formal clarification and preserve evidence first**

The core interaction is:

```text
change one fact -> recompute the decision graph -> see consequence paths change
```

The demo changes `formal_notice_received` from No to Yes. The engine recalculates constraints, uncertainty scores, evidence status, consequence copy, dependencies, and the side-by-side comparison. It never labels a scenario as a guaranteed legal outcome.

## Architecture

- `app/models.py` contains strict Pydantic models for `Situation`, `Fact`, `Action`, `Constraint`, `EvidenceItem`, `ScenarioBranch`, `Consequence`, `DecisionComparison`, and `SimulationResult`.
- `app/knowledge.py` contains the small, transparent primary-demo knowledge base and default state.
- `app/engine.py` implements the explicit pipeline: normalize facts, identify missing or uncertain facts, evaluate constraints, generate actions, branch scenarios, propagate consequences, calculate evidence requirements, calculate uncertainty, compare branches, and produce cautious next steps.
- `app/providers.py` is the server-side provider seam. Demo mode is deterministic and needs no key. An optional configured provider can be introduced without exposing credentials to the frontend; the current demo rules remain the source of truth.
- `app/main.py` exposes FastAPI endpoints and serves the vanilla frontend from `app/static/`.
- `app/static/index.html`, `styles.css`, and `app.js` provide the responsive UI and call the API for both the initial simulation and the counterfactual update.

## Demo Flow

1. Open the app and review the tenant scenario and structured facts.
2. Click **Simulate decision**.
3. Review two scenario branches, evidence, uncertainty, dependencies, and next steps.
4. Change **Formal notice received** from **No** to **Yes**.
5. LAWSEER calls `/api/counterfactual`, highlights the recomputed graph, and explains why downstream information changed.
6. Compare the updated branches and verify the next step with an official source or qualified professional.

## Tech Stack

- Python 3.13+
- FastAPI and Uvicorn
- Pydantic v2
- Vanilla HTML, CSS, and JavaScript
- Pytest and FastAPI `TestClient`

## AI Usage

The code and interface were produced with AI coding assistance, which is disclosed here honestly. The demo does not send the entire user prompt to an LLM. It first creates a structured internal representation and applies deterministic, inspectable rules. `app/providers.py` provides a server-only extension seam for a future optional model adapter; no API key is shipped to the browser.

## Limitations and Legal Safety

The knowledge base is intentionally small, illustrative, and not authoritative law. It does not determine whether a notice is valid, whether an action is legal or illegal, or what a court or agency will do. Jurisdiction-specific rules, deadlines, contract terms, facts, and evidence can change the analysis. Scores are scenario uncertainty indicators, not probabilities.

**LAWSEER is an educational decision-support prototype. It does not provide legal advice or predict legal outcomes. Verify important decisions with official sources or a qualified professional.**

## Run Locally

From the project directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Test

```bash
python -m pytest -q
python -m compileall app
```

## API

- `GET /` — frontend
- `GET /health` — health check
- `GET /api/demo` — deterministic default simulation
- `POST /api/simulate` — simulate a supplied `Situation`
- `POST /api/counterfactual` — update one fact and recompute the supplied `Situation`
- `GET /static/styles.css` and `GET /static/app.js` — frontend assets
