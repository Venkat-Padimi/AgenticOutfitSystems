# AI Personal Outfit Styling & Shopping Agent ("Aura Stylist / Blend")
*An Agentic AI Platform & Mobile Application for Autonomous Styling & Group Coordination*

> 📌 **Engineering Roadmap**: See [`docs/PHASED_ARCHITECTURE_ROADMAP.md`](docs/PHASED_ARCHITECTURE_ROADMAP.md) for the complete 5-phase architectural breakdown, deliverables, and benchmark statuses.

---

## 1. System Overview

**AURA Stylist** is an autonomous, goal-oriented styling and shopping agent that discovers, assembles, evaluates, and visualizes complete outfits using real clothing products from Indian e-commerce merchants (Myntra, Flipkart, Amazon India, Ajio, and Zara India).

Unlike conventional recommendation feeds or static chatbots, this system features a **deterministic, bounded ReAct agent orchestrator powered by Google Gemini**:
1. **Decomposes high-level goals** (e.g., "College Farewell Party", "Royal Ethnic", ₹5,000 budget) into structured subtasks.
2. **Dynamically queries real-world shopping APIs** (SerpApi Google Shopping India) with category and budget constraints.
3. **Deterministically evaluates hard constraints in Python** (budget ceilings, size availability, delivery deadlines).
4. **Autonomously detects constraint violations** (e.g., total outfit price exceeding budget).
5. **Replans and repairs ensembles** (swapping high-ticket items, pruning redundant layers, selecting budget-conscious alternatives).
6. **Harmonizes group aesthetics via "Blend"**, allowing friends to coordinate a shared color story while strictly enforcing independent member budgets and individual styles with zero cross-member subsidization.

---

## 2. Architecture & Data Flow

```
                      ┌──────────────────────────────────────────┐
                      │   React Native (Expo SDK / Web / Mobile) │
                      │  - Stylist Studio   - Agent Feed         │
                      │  - Outfit Showcase  - Blend Group Room   │
                      └─────────────────────┬────────────────────┘
                                            │ HTTPS / REST / SSE Stream
                                            ▼
                      ┌──────────────────────────────────────────┐
                      │        FastAPI Gateway & Orchestrator    │
                      │  - Bounded ReAct Cycle (Max 6 Iterations)│
                      │  - Deterministic Python Constraint Engine│
                      │  - Google Gemini 3.5 Function Calling    │
                      │  - SQLite (WAL) / PostgreSQL Persistence │
                      └─────────────────────┬────────────────────┘
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
         ┌───────────────────────────────┐        ┌──────────────────────────────┐
         │ SerpApi Google Shopping India │        │ Controlled Fixture Provider  │
         │ (gl=in, INR, Myntra / Amazon) │        │ (Deterministic Offline Mode) │
         └───────────────────────────────┘        └──────────────────────────────┘
```

---

## 3. Server-Side Environment Variables

All secret keys and credentials **must remain strictly server-side**. They are read from `backend/.env` locally or configured as environment variables in your hosting provider (e.g., Render Dashboard).

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Recommended | `""` | Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/). When omitted, the orchestrator safely runs deterministic fallback heuristics. |
| `GEMINI_MODEL` | No | `gemini-3.5-flash-lite` | Gemini model identifier used for agent tool calling and reasoning. |
| `SERPAPI_API_KEY` | Recommended | `""` | SerpApi key from [serpapi.com](https://serpapi.com/) (250 free searches/month). |
| `SHOPPING_PROVIDER_MODE` | No | `hybrid` | `hybrid` (live SerpApi with safe fallback), `live` (strictly live API), or `fixture` (controlled offline mock datasets). |
| `HOST` | No | `0.0.0.0` | Network host interface to bind. Production hosts require `0.0.0.0`. |
| `PORT` | No | `8000` | Port to bind. Hosting platforms (Render, Railway, Heroku) inject this dynamically via `$PORT`. |
| `DEBUG` | No | `False` | Enables FastAPI auto-reload and verbose logging. Must be `False` in production. |
| `ALLOWED_ORIGINS` | No | *(safe local defaults)* | Comma-separated list of CORS origins allowed to access the API (e.g. `https://my-app.vercel.app,http://localhost:8081`). Pass `*` for public access. |
| `DATABASE_URL` | No | `""` | Database connection string. Supports PostgreSQL (`postgresql://user:pass@host/db`) or custom SQLite path (`sqlite:////var/data/blend.db`). |
| `PERSISTENCE_DIR` | No | `""` | Directory for persistent storage files (e.g., `/var/data` when using a Render Persistent Disk). |
| `AGENT_TIMEOUT_SECONDS` | No | `60.0` | Maximum execution timeout for an agent orchestration run. |
| `AGENT_MAX_ITERATIONS` | No | `6` | Maximum iterations permitted in the autonomous replanning loop. |

> ⚠️ **Security Mandate**: Never commit `.env` files or hardcode API keys into repository code or mobile client bundles.

---

## 4. Production Backend Deployment (Render)

The backend is fully configured for deployment on [Render](https://render.com/) as a Python Web Service.

### Option A: 1-Click Blueprint Deployment (`render.yaml`)

1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** > **Blueprint**.
3. Connect your `AgenticOutfitSystems` GitHub repository.
4. Render will detect [`render.yaml`](render.yaml) automatically and prompt for:
   * `GEMINI_API_KEY` (secret)
   * `SERPAPI_API_KEY` (secret)
5. Click **Apply**. Render will automatically provision the service, build dependencies, bind to `$PORT`, and run health checks.

### Option B: Manual Web Service Setup

1. In the Render Dashboard, click **New +** > **Web Service**.
2. Select your GitHub repository.
3. Configure the following fields:
   * **Name**: `aura-stylist-backend`
   * **Language / Runtime**: `Python`
   * **Root Directory**: `backend`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   * **Health Check Path**: `/health`
4. In the **Environment Variables** tab, add:
   * `GEMINI_API_KEY`: *(your Gemini key)*
   * `SERPAPI_API_KEY`: *(your SerpApi key)*
   * `SHOPPING_PROVIDER_MODE`: `hybrid`
   * `GEMINI_MODEL`: `gemini-3.5-flash-lite`
   * `DEBUG`: `False`
   * `ALLOWED_ORIGINS`: `*` *(or your web domain)*
   * `PYTHON_VERSION`: `3.11.9`
5. Click **Create Web Service**.
6. Once deployed, test the live health endpoint:
   ```bash
   curl https://your-service-name.onrender.com/health
   ```
   Expected response:
   ```json
   {"status":"healthy","provider_mode":"hybrid","serpapi_configured":true,"gemini_configured":true}
   ```

---

## 5. Persistent Storage for Group Styling ("Blend")

Cloud container filesystems (such as Render Free Web Services) are **ephemeral** and reset on redeployments or container restarts. To ensure Blend group rooms, budgets, and harmonized outfits are durable, Aura Stylist provides pluggable persistence:

1. **Default / Development / Persistent Disk**:
   * Uses built-in **SQLite** with Write-Ahead Logging (`WAL` mode) and atomic writes.
   * If using Render's persistent disk (paid plan), attach a disk mounted at `/var/data` and set `PERSISTENCE_DIR=/var/data`.
2. **Cloud PostgreSQL (Render Free Tier / Neon / Supabase)**:
   * Render provides a free managed PostgreSQL database.
   * Simply set `DATABASE_URL=postgresql://user:password@host:5432/aura_db` in the web service environment.
   * The persistence manager automatically detects PostgreSQL via `psycopg` and manages schema migrations seamlessly.

---

## 6. Mobile Client Configuration & Production Build

The mobile application is built with **React Native**, **Expo SDK**, and **TypeScript**.

### 6.1 Configuring the API Base URL

The mobile app reads its backend target from `EXPO_PUBLIC_API_BASE_URL`.

1. Copy the example configuration in `mobile/`:
   ```bash
   cp mobile/.env.example mobile/.env
   ```
2. Update `mobile/.env` with your public backend URL:
   ```env
   EXPO_PUBLIC_API_BASE_URL=https://your-service-name.onrender.com
   ```
   *(No trailing slash. In Expo, `EXPO_PUBLIC_*` variables are embedded at build time).*

### 6.2 Running Locally with Expo Go

```bash
cd mobile
npx expo start
```
* **Physical Device**: Scan the QR code with the **Expo Go** app on Android or iOS.
* **Android Emulator**: Press `a` in the Expo terminal.
* **Web Browser**: Press `w` or run `npx expo start --web`.

### 6.3 Building a Standalone Android APK / AAB (Production)

To build a standalone production Android binary without requiring a local Metro bundler:

1. Install EAS CLI:
   ```bash
   npm install -g eas-cli
   ```
2. Log in to your Expo account:
   ```bash
   eas login
   ```
3. Configure the build profile in `mobile/eas.json`:
   ```bash
   cd mobile
   eas build:configure
   ```
4. Build the Android APK:
   ```bash
   eas build --platform android --profile preview
   ```
5. Install the resulting `.apk` directly onto physical Android devices.

---

## 7. Automated Testing & Verification Suite

All core functionality is guarded by automated test suites that run offline without consuming live API credits.

### 7.1 Backend Tests (Pytest)

Run all 31 automated backend tests across agent orchestration, constraint validation, vertical slices, and group coordination:
```bash
python -m pytest backend/tests -v
```
Test Breakdown:
* `test_blend_coordination.py`: 15 tests covering multi-member budgets, color harmony scoring, repair loops, item swaps, live provider error handling, and room persistence.
* `test_gemini_orchestrator.py`: 12 tests validating Gemini tool calling, bounded replanning, timeout safety, and deterministic fallback.
* `test_vertical_slice.py`: 4 tests validating full request-to-response styling pipelines across budget overrun scenarios.

### 7.2 Mobile TypeScript Typecheck

Verify that the entire TypeScript codebase has zero compile or type errors:
```bash
cd mobile
npx tsc --noEmit
```

### 7.3 Mobile Web Bundle Export

Verify that the production React Native web bundle builds cleanly:
```bash
cd mobile
npx expo export --platform web --output-dir dist_test
```

---

## 8. Security & Data Integrity Principles

* **Zero Secret Leakage**: API keys, database credentials, and internal tokens exist only on the server. No client bundle or repository file contains secrets.
* **Python-Authoritative Constraints**: Google Gemini performs contextual reasoning and candidate discovery, but Python enforces all hard constraints (budget sums, sizing availability, category requirements). Gemini cannot override budget ceilings or fabricate inventory.
* **Honest Error Handling**: If a live shopping provider fails (e.g. rate limit, network timeout), errors are surfaced honestly in member statuses (`partial` / `failed`); the system never silently replaces live failures with fixtures.
* **Zero Cross-Member Budget Subsidy**: In Blend group sessions, each member's budget is strictly bounded to their own garments. One member's surplus budget is never spent on another member.
