# Unstructured Feedback Intelligence (UFI) Pipeline
**An AI-native system for parsing qualitative data, preventing data poisoning, and keeping humans in control.**

[![Demo Video](https://img.shields.io/badge/Watch-2_Minute_Demo-red?style=for-the-badge&logo=youtube)](#) *(https://www.youtube.com/@ZuseTheGoose)*

## 🛑 The Problem: LLMs Are Gullible
Product managers and analysts drown in unstructured qualitative data (support tickets, app reviews). While LLMs are excellent at extracting sentiment from this noise, they lack operational skepticism. If a bot network submits 1,000 synthetic reviews complaining about a "crypto transfer fee," a standard LLM pipeline will dutifully extract that data, poison the analytics dashboard, and trigger a false product crisis. 

## 💡 The Solution: Authenticity Quarantine
The UFI Pipeline doesn't just extract data; it evaluates the linguistic fingerprint of the input first. Built entirely on a **locally-hosted, privacy-first LLM** (Llama 3.2), the system processes unstructured text, scores its authenticity, and executes a routing fork. Valid data updates the main strategic dashboard, while suspected synthetic data is shunted into a Quarantine database for human audit.

## 🧠 System Architecture
1. **Ingestion:** Reads raw, messy user feedback (CSV). *Note: This MVP uses the [Kaggle Fake Reviews Dataset](https://www.kaggle.com/datasets/mexwell/fake-reviews-dataset) to rigorously test the pipeline against a 50/50 split of verified human ("OR") and computer-generated ("CG") text.*
2. **Local Inference (Ollama/Llama 3.2):** Bypasses external cloud APIs to maintain strict zero-PII fintech compliance. Uses Few-Shot Prompting and strict JSON enforcement to extract:
   * `TL;DR`: A 3-to-6 word summary.
   * `Entity`: Hardcoded entity resolution (e.g., "Authentication/Login", "App Performance").
   * `Sentiment Score`: 0.0 to 1.0.
   * `Authenticity Score`: 0-100 evaluation of human vs. synthetic phrasing.
3. **The Routing Fork:** Data scoring `< 70` is sent to a SQLite Quarantine table. Data `>= 70` goes to the Valid Feedback table.
4. **The Human Interface (Streamlit):** A dual-tab dashboard separating strategic product metrics from the security audit log.

---

## 🎯 Answering the AI Builder Prompt

### What the human can now do that they couldn't before
The human is freed from the cognitive exhaustion of manually reading and tagging thousands of reviews. Instead of relying on anecdotal, cherry-picked feedback (which invites confirmation bias), the human can instantly query the mathematical reality of user sentiment across the entire user base, filtered cleanly of bot spam.

### What the AI is responsible for
The AI assumes the operational burden of large-scale semantic pattern recognition. It is responsible for parsing chaotic human language, classifying it into strict structural schemas, and acting as the first line of defense against synthetic data poisoning.

### Explicitly: Where the AI must stop (The Critical Human Decision)
The AI **must stop at product prioritization and quarantine overrides**. 
Mathematically, the AI might identify that "Identity Verification" causes massive negative sentiment and suggest removing it. However, the AI lacks the business context of FINTRAC regulations or AML compliance. The human retains the authority to decide if friction is a required legal constraint or a genuine UX flaw. Furthermore, the human must audit the Quarantine to ensure unconventional human writing isn't accidentally silenced by the AI's filter.

### What would break first at scale
At massive scale, the system's point of failure is **semantic drift and novel spam vectors**. As the company launches entirely new products, or as bot networks utilize more sophisticated LLMs to write fake reviews, Llama 3.2’s static prompt will begin to miscategorize nuanced feedback. To prevent the database from filling with "hallucinated" entities, the human operator must establish a continuous evaluation loop, periodically sampling the AI’s categorization and updating the extraction logic to adapt to shifting human language.

---

## 🛠️ Tech Stack
* **Language/Framework:** Python, Pandas, Streamlit (Dashboard UI)
* **AI/Inference:** Ollama, Llama 3.2 (3B parameters, running locally)
* **Database:** SQLite (Relational structuring and routing)
* **Visualization:** Plotly Express

## 🚀 How to Run Locally

**1. Install Dependencies**
Ensure you have [Ollama](https://ollama.com/) installed on your machine.
```bash
# Pull the local model
ollama pull llama3.2

# Install Python requirements
pip install pandas streamlit plotly ollama