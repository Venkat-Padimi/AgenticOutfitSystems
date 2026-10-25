# AI Personal Outfit Styling & Shopping Agent ("Blend")
*An Agentic AI Case Study & Mobile Application for Engineering Evaluation*

---

## 1. System Overview

**AURA Stylist** is an autonomous, goal-oriented styling and shopping agent that discovers, assembles, evaluates, and visualizes complete outfits using real clothing products from Indian e-commerce merchants (Myntra, Flipkart, Amazon India, Ajio, and Zara India).

Unlike conventional recommendation feeds or chatbots, this system features a **deterministic, bounded ReAct agent loop**:
1. **Decomposes high-level goals** (e.g., "College Farewell Party", "Smart Casual", ₹5,000 budget) into subtasks.
2. **Dynamically queries real-world shopping APIs** with price and category constraints.
3. **Deterministically evaluates hard constraints** (budget arithmetic, size availability, delivery deadlines).
4. **Autonomously catches constraint violations** (e.g., total cost overshooting budget ceiling).
5. **Replans and repairs the ensemble** (swapping high-ticket items, pruning redundant layers, selecting budget-conscious alternatives).
6. **Harmonizes group aesthetics via "Blend"**, allowing friends to coordinate a shared color story while preserving each person's unique budget and silhouette.

---

## 2. Architecture & Data Flow

```
                      ┌──────────────────────────────────────────┐
                      │   React Native (Expo SDK 58 / Web)       │
                      │  - Stylist Studio   - Agent Feed         │
                      │  - Outfit Showcase  - Blend Group Room   │
                      └─────────────────────┬────────────────────┘
                                            │ REST / SSE Stream
                                            ▼
                      ┌──────────────────────────────────────────┐
                      │        FastAPI Gateway & Orchestrator     │
                      │  - Bounded ReAct Cycle (Max 6 Steps)     │
                      │  - Deterministic Constraint Engines      │
                      │  - Google Gemini 2.5 Flash Function Calls│
                      └─────────────────────┬────────────────────┘
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
         ┌───────────────────────────────┐        ┌──────────────────────────────┐
         │ SerpApi Google Shopping India │        │ Controlled Fixture Provider  │
         │ (gl=in, INR, Myntra / Amazon) │        │ (Deterministic Edge Cases)   │
         └───────────────────────────────┘        └──────────────────────────────┘
```

---

## 3. Demonstration Scenarios

| Scenario | Objective | Demonstrable Behavior |
| :--- | :--- | :--- |
| **Scenario 1: Standard Themed Look** | Budget ₹6,000, "Tech Fest Keynote" | Assembles blazer, oxford shirt, chinos, and handcrafted leather loafers within budget. |
| **Scenario 2: Budget Overrun & Self-Correction** | Budget ₹5,000, "College Farewell" | Agent initially encounters luxury blazer exceeding budget (₹8,097 total), triggers `ConstraintStatus.VIOLATED`, invokes `ReplanOutfit`, swaps to high-rated cotton-linen blazer (₹4,697 total), and documents the tradeoff. |
| **Scenario 5: "Blend" Group Coordination** | Shared Theme: "Royal Retro" (Navy & Champagne) | Arjun (₹6,000 budget, formal) + Sneha (₹3,500 budget, ethnic fusion) are synchronized without clashing and without exceeding individual budgets. |

---

## 4. Quick Start & Execution Guide

### 4.1 Backend Orchestrator (FastAPI)

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env` in `/backend`:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Add your keys (optional; the app operates in hybrid/fixture mode with full offline resilience if keys are omitted):
   * `SERPAPI_API_KEY`: Get free tier key from [serpapi.com](https://serpapi.com/) (250 free searches/month).
   * `GEMINI_API_KEY`: Get free tier key from [aistudio.google.com](https://aistudio.google.com/).

2. **Start the FastAPI Server**:
   ```powershell
   python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
   ```
   * Health endpoint: `http://localhost:8000/health`
   * Interactive Swagger Docs: `http://localhost:8000/docs`

3. **Run the Automated Test Suite**:
   ```powershell
   python -m pytest backend/tests/test_vertical_slice.py -v
   ```

---

### 4.2 Mobile Client (React Native / Expo)

1. **Start the Expo Development Server**:
   ```powershell
   cd mobile
   npx expo start
   ```

2. **To Run on Physical Device (Expo Go)**:
   * Install the **Expo Go** app from Google Play Store or iOS App Store.
   * Scan the QR code displayed in the terminal.
   * *(Note: Ensure phone and computer are on the same Wi-Fi network)*.

3. **To Run in Web Browser (Zero-Install Classroom Presentation)**:
   ```powershell
   cd mobile
   npx expo start --web
   ```
   * Or press `w` in the Expo terminal to open `http://localhost:8081`.

---

## 5. Security & Sensitive Data Handling
* **Zero Secret Leakage**: API keys remain strictly server-side in `backend/.env`.
* **Verified E-Commerce Links**: Buy buttons route users to direct merchant product URLs on Myntra, Amazon India, Ajio, Flipkart, and Zara India.
* **No Autonomous Payments**: The agent assembles, evaluates, and links to carts; it does not execute financial transactions automatically.
