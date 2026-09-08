# LAWSEER

> **See how a decision changes before you make it.**

LAWSEER is an educational counterfactual decision simulator for civic and legal-style situations.

It is not a generic legal chatbot, document summarizer, RAG Q&A app, or legal advice generator.

The LexHack 2026 demo focuses on one question:

> **How does a decision graph change when one fact changes?**

---

## Why LAWSEER is Different

Most legal AI tools focus on answering a question or retrieving information.

LAWSEER focuses on **decision change**.

It:

- Structures the user's situation into explicit facts.
- Keeps uncertain and missing information visible.
- Models dependencies that can affect a decision.
- Compares alternative action paths.
- Tracks evidence that supports or is still missing from the scenario.
- Shows uncertainty as a scenario indicator.
- Allows one fact to be changed through a counterfactual control.
- Recomputes the downstream decision state when that fact changes.

### Core Mechanism

```text
change one fact
       ↓
recompute the decision state
       ↓
update constraints, evidence, uncertainty and consequences
       ↓
compare the changed decision paths
       ↓
verify the next step

The key interaction is not:

Ask AI → Get legal answer

It is:

Change a fact → See how the decision changes
Problem

People often face time-sensitive requests with incomplete records.

A single answer can hide the assumptions that shaped it.

LAWSEER makes those assumptions inspectable by structuring the situation, marking uncertainty, modelling procedural dependencies, and comparing possible action paths.

Novel Mechanism

The primary demo scenario is a tenant receiving a sudden request from a landlord to leave within a short period.

The user can compare:

A. Leave immediately
B. Ask for formal clarification and preserve evidence first

The demo changes:

formal_notice_received

from:

No → Yes

The engine then recalculates the scenario state, including uncertainty, evidence status, consequence descriptions, dependencies, and the side-by-side comparison.

The demo also supports reversing the change:

Yes → No

which restores the original scenario state.

LAWSEER does not label a scenario as a guaranteed legal outcome.

Screenshots
1. Landing Page

2. Decision Input

3. Decision State and Counterfactual Control

4. Counterfactual: Formal Notice = Yes

5. Counterfactual Reverted: Formal Notice = No

6. Decision Comparison

7. Evidence and Safety

Architecture

LAWSEER uses an explicit, inspectable simulation pipeline rather than presenting an opaque legal answer.

app/models.py contains strict Pydantic models for Situation, Fact, Action, Constraint, EvidenceItem, ScenarioBranch, Consequence, DecisionComparison, and SimulationResult.
app/knowledge.py contains the small, transparent primary-demo knowledge base and default state.
app/engine.py implements the simulation pipeline: normalize facts, identify missing or uncertain facts, evaluate constraints, generate actions, branch scenarios, propagate consequences, calculate evidence requirements, calculate uncertainty, compare branches, and produce cautious next steps.
app/providers.py provides a server-side provider seam. Demo mode is deterministic and requires no API key.
app/main.py exposes the FastAPI endpoints and serves the frontend.
app/static/ contains the HTML, CSS, and JavaScript interface.
Demo Flow
Open the application.
Review the tenant scenario and structured facts.
Click Simulate decision.
Review the two scenario branches.
Inspect evidence, uncertainty, dependencies, and cautious next steps.
Change Formal notice received from No to Yes.
LAWSEER calls /api/counterfactual and recomputes the decision state.
Observe the changed consequence descriptions, evidence state, dependencies, and uncertainty scores.
Change the fact back to No and verify that the original state is restored.
Technical Pipeline
Situation
   ↓
Structured Facts
   ↓
Fact Normalization
   ↓
Uncertainty Detection
   ↓
Constraint Evaluation
   ↓
Action Branching
   ↓
Consequence Propagation
   ↓
Evidence Requirements
   ↓
Uncertainty Calculation
   ↓
Decision Comparison
   ↓
Cautious Next Steps

The counterfactual endpoint repeats this pipeline after updating the selected fact.

Tech Stack
Python 3.13+
FastAPI
Uvicorn
Pydantic v2
Vanilla HTML
CSS
JavaScript
Pytest
FastAPI TestClient
AI Usage

The code and interface were produced with AI coding assistance, which is disclosed here honestly.

The demo does not send the entire user prompt to an LLM. It first creates a structured internal representation and applies deterministic, inspectable rules.

app/providers.py provides a server-only extension seam for a future optional model adapter. No API key is shipped to the browser.

Limitations and Legal Safety

The knowledge base is intentionally small, illustrative, and not authoritative law.

LAWSEER does not determine:

whether a notice is legally valid;
whether an action is legal or illegal;
what a court or agency will do; or
what the correct legal outcome will be.

Jurisdiction-specific rules, deadlines, contract terms, facts, and evidence can change the analysis.

The displayed scores are scenario uncertainty indicators, not probabilities.

LAWSEER is an educational decision-support prototype. It does not provide legal advice or predict legal outcomes. Verify important decisions with official sources or a qualified professional.

Run Locally
Windows
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Linux / macOS
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Open:

http://127.0.0.1:8000
Test

Run:

python -m pytest -q
python -m compileall app
API
Method	Endpoint	Purpose
GET	/	Frontend application
GET	/health	Health check
GET	/api/demo	Deterministic default simulation
POST	/api/simulate	Simulate a supplied Situation
POST	/api/counterfactual	Update one fact and recompute the supplied Situation
Project Structure
lawseer-lexhack-2026/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── engine.py
│   ├── knowledge.py
│   ├── providers.py
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── screenshots/
│   ├── LAWSEER-01-Landing-Page.png
│   ├── LAWSEER-02-Decision-Input.png
│   ├── LAWSEER-03-Decision-State-Counterfactual.png
│   ├── LAWSEER-04-Consequence-Map-Notice-Yes.png
│   ├── LAWSEER-05-Consequence-Map-Notice-No.png
│   ├── LAWSEER-06-Comparison.png
│   └── LAWSEER-07-Evidence-Safety.png
├── tests/
│   └── test_lawseer.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
Status

LAWSEER — LexHack 2026

A working educational prototype demonstrating counterfactual legal/civic decision simulation.

Core Demo
No
 ↓
Yes
 ↓
Recompute
 ↓
Observe changed decision state
 ↓
No
 ↓
Original state restored

### After paste

**1. `Ctrl + S`**

**2. Close Notepad.**

**3. Run only:**

```bat
git status