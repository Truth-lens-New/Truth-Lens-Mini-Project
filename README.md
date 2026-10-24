# 🔍 TruthLens - Multi-Modal Misinformation Detection Platform

<div align="center">

![TruthLens Banner](https://img.shields.io/badge/TruthLens-AI%20Powered-00FFC3?style=for-the-badge&logo=shield&logoColor=white)
![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/status-MVP%20Complete-success?style=for-the-badge)

**Analyze images, videos, and articles with forensic-grade AI.**
**Detect deepfakes, manipulations, and misinformation instantly.**

</div>

> [!IMPORTANT]
> **Dec 2025 - Frontend Restructured!** 
> The frontend moved from `src/` to `client/`. Run: `cd client && npm install`

---

## 👥 Team

| Name | Role | Branch |
|------|------|--------|
| **Shivam Yadav** | Developer | `shivam` |
| **Harsh Rupreja** | Developer | `harsh` |
| **Uday Dewani** | Developer | `uday` |

---

## 🚀 Features

### ✅ MVP Complete (v1.0.0)

- **🔐 User Authentication** - Secure login/register with JWT tokens
- **📝 Article/Claim Analysis** - Extract and verify claims from text or URLs
- **🌐 Domain Trust Scoring** - Evaluate source credibility (0-100 score)
- **✓ Fact-Check Integration** - Google Fact Check API integration
- **📰 Evidence Retrieval** - GNews API for corroborating sources
- **🤖 Stance Classification** - AI-powered stance detection
- **⚖️ Verdict Aggregation** - Intelligent verdict synthesis
- **💬 LLM Explanations** - Human-readable analysis explanations
- **📊 Analysis History** - View past verification results
- **🎨 Modern UI** - Dark theme with glassmorphism design

---

## 🛠️ Tech Stack

### Frontend
- **React 18** + TypeScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide Icons** - UI icons

### Backend
- **FastAPI** - Python API framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Google Gemini** - LLM integration

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

---

## 📁 Project Structure

```
TruthLens/
├── client/                       # Frontend (React + Vite)
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── LandingPage.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ArticleVerification.tsx
│   │   │   └── ...
│   │   ├── lib/                 # Utilities (api.ts)
│   │   └── types/               # TypeScript definitions
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # Backend (FastAPI)
│   └── app/
│       ├── api/v1/              # API endpoints
│       │   ├── auth.py          # Authentication
│       │   ├── analyze.py       # Analysis pipeline
│       │   └── history.py       # History management
│       ├── models/              # Database models
│       ├── services/            # Business logic
│       │   ├── domain_trust.py  # Domain scoring
│       │   ├── factcheck.py     # Fact-check API
│       │   ├── evidence.py      # News retrieval
│       │   ├── stance.py        # Stance classification
│       │   └── explanation.py   # LLM explanations
│       └── core/                # Config & database
│
├── data/                        # Seed data
├── docker-compose.yml           # Docker configuration (LOCAL DEVELOPMENT ONLY —
                             # see docker-compose.prod.yml for production)
├── CONTRIBUTING.md              # Collaboration guide
└── README.md                    # This file
```

---

## 🏃 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose
- API Keys (Gemini, Google Fact Check, GNews)

### 1. Clone the Repository
```bash
git clone https://github.com/2025harshrupreja/Truth-Lens-Mini-Project.git
cd Truth-Lens-Mini-Project
```

### 2. Setup Environment
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/truthlens

# API Keys
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_key
GNEWS_API_KEY=your_gnews_api_key

# JWT
JWT_SECRET=your_jwt_secret_key
```

### 3. Start Backend (Docker)
```bash
docker-compose up -d
```

### 4. Install Frontend Dependencies
```bash
cd client
npm install
```

### 5. Start Development Server
```bash
npm run dev
```

### 6. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

---

## 🌿 Git Workflow

We use a **3-tier branching strategy**:

```
main (production-ready, demo-ready)
  │
  └── dev (integration & testing)
        │
        ├── shivam
        ├── harsh
        └── uday
```

**Flow**: `personal branch → dev → main`

📖 See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---

## 🤖 AI Collaboration

This project uses AI-assisted development. Each team member should use the AI prompt in `CONTRIBUTING.md` to ensure safe, merge-friendly code changes.

---

## 📸 Screenshots

| Landing Page | Analysis Results |
|--------------|------------------|
| Dark theme with modern UI | Detailed verification breakdown |

---

## 📄 License

This project is developed as part of an academic mini-project.

---

<div align="center">

**Built with ❤️ by Team TruthLens**

*Shivam • Harsh • Uday*

</div>
