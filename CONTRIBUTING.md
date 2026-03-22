                                                                                                                                                               # TruthLens - Collaboration Guidelines

## 👥 Team

| Name | Role | Personal Branch |
|------|------|-----------------|
| **Shivam Yadav** | Project Lead (Merge to main) | `shivam` |
| **Harsh Rupreja** | Developer | `harsh` |
| **Uday Dewani** | Developer | `uday` |

---

## 🌿 Branch Structure

```
main ────────────────────────────────────────────── (PROTECTED - Demo Ready)
  │                                                   Only Shivam can merge here
  │
  └── dev ───────────────────────────────────────── (Integration Branch)
        │                                             Test before promoting to main
        │
        ├── shivam ──────────────────────────────── (Shivam's work)
        │
        ├── harsh ───────────────────────────────── (Harsh's work)
        │
        └── uday ────────────────────────────────── (Uday's work)
```

### Branch Rules

| Branch | Purpose | Who Can Push | Who Can Merge |
|--------|---------|--------------|---------------|
| `main` | Production-ready, demo-ready | Nobody directly | **Shivam only** (via PR from dev) |
| `dev` | Integration & testing | Everyone (via PR) | Team agreement |
| `shivam` | Shivam's features | Shivam | - |
| `harsh` | Harsh's features | Harsh | - |
| `uday` | Uday's features | Uday | - |

---

## 🔄 Workflow: How to Work on a Feature

### Step 1: Start Fresh (Every Work Session)

```bash
# Switch to your personal branch
git checkout <your-name>    # e.g., git checkout shivam

# Get latest from dev
git pull origin dev

# If there are conflicts, resolve them or ask for help
```

### Step 2: Work on Your Feature

```bash
# Make your changes...
# Test locally to make sure it works!

# Commit frequently (after each working piece)
git add .
git commit -m "feat: describe what you added"
```

### Step 3: Push Your Work

```bash
# Push to your personal branch
git push origin <your-name>    # e.g., git push origin shivam
```

### Step 4: Ready for Integration?

1. Go to GitHub → Create **Pull Request**
2. From: `your-branch` → To: `dev`
3. Write a description of what you added
4. Wait for team review

### Step 5: Merging to Main (Shivam Only)

When `dev` is stable and tested:
1. Create PR: `dev` → `main`
2. Review everything works
3. Merge

---

## 📝 Commit Message Format

```
<type>: <short description>

Examples:
feat: add social media login buttons
fix: navbar not showing on mobile
style: improve dashboard card shadows
refactor: reorganize api.ts functions
docs: update setup instructions
```

| Type | When to Use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `style` | CSS/visual changes only |
| `refactor` | Code cleanup (no new feature) |
| `docs` | Documentation |
| `chore` | Config files, dependencies |

---

## 🤖 AI Collaboration Prompts

### ⚠️ CRITICAL: Always Start AI Sessions With This Prompt

Copy-paste this at the START of every AI coding session:

---

### 🟢 Shivam's AI Prompt

```
You are helping me (Shivam) work on TruthLens, a COLLABORATIVE project with 2 other teammates (Harsh, Uday).

CRITICAL RULES:
1. NEVER delete or completely rewrite files - make small, incremental changes
2. ALWAYS preserve existing functionality - don't break what works
3. Add helpful comments for complex logic
4. Before making big changes, explain what you'll modify and wait for my approval
5. When I say "checkpoint" or "commit", create a git commit with descriptive message
6. NEVER directly modify these shared files without asking:
   - package.json
   - docker-compose.yml
   - backend/app/core/config.py
   - src/lib/api.ts (be careful with shared API functions)

PROJECT INFO:
- Frontend: React + Vite + TypeScript (src/)
- Backend: FastAPI + Python (backend/)
- My branch: shivam
- Integration branch: dev
- Production branch: main (only I can merge here)

After completing features, remind me to: git add . && git commit -m "message" && git push origin shivam
```

---

### � Harsh's AI Prompt

```
You are helping me (Harsh) work on TruthLens, a COLLABORATIVE project with 2 other teammates (Shivam, Uday).

CRITICAL RULES:
1. NEVER delete or completely rewrite files - make small, incremental changes
2. ALWAYS preserve existing functionality - don't break what works
3. Add helpful comments for complex logic
4. Before making big changes, explain what you'll modify and wait for my approval
5. When I say "checkpoint" or "commit", create a git commit with descriptive message
6. NEVER directly modify these shared files without asking:
   - package.json
   - docker-compose.yml
   - backend/app/core/config.py
   - src/lib/api.ts (be careful with shared API functions)

PROJECT INFO:
- Frontend: React + Vite + TypeScript (src/)
- Backend: FastAPI + Python (backend/)
- My branch: harsh
- Integration branch: dev
- Production branch: main (Shivam manages)

After completing features, remind me to: git add . && git commit -m "message" && git push origin harsh
```

---

### 🟣 Uday's AI Prompt

```
You are helping me (Uday) work on TruthLens, a COLLABORATIVE project with 2 other teammates (Shivam, Harsh).

CRITICAL RULES:
1. NEVER delete or completely rewrite files - make small, incremental changes
2. ALWAYS preserve existing functionality - don't break what works
3. Add helpful comments for complex logic
4. Before making big changes, explain what you'll modify and wait for my approval
5. When I say "checkpoint" or "commit", create a git commit with descriptive message
6. NEVER directly modify these shared files without asking:
   - package.json
   - docker-compose.yml
   - backend/app/core/config.py
   - src/lib/api.ts (be careful with shared API functions)

PROJECT INFO:
- Frontend: React + Vite + TypeScript (src/)
- Backend: FastAPI + Python (backend/)
- My branch: uday
- Integration branch: dev
- Production branch: main (Shivam manages)

After completing features, remind me to: git add . && git commit -m "message" && git push origin uday
```

---

## ⚠️ High-Risk Files (Be Careful!)

Modifying these files can affect everyone:

| File | Impact | Action |
|------|--------|--------|
| `package.json` | All frontend dependencies | Tell team before changing |
| `docker-compose.yml` | Backend & database | Tell team before changing |
| `backend/app/models/*.py` | Database structure | Coordinate with team |
| `backend/app/core/config.py` | App settings | Tell team before changing |
| `src/lib/api.ts` | All API calls | Be careful, add new functions instead of modifying |

---

## 🔧 Environment Setup (For New Team Members)

### 1. Clone the Repository
```bash
git clone https://github.com/2025harshrupreja/Truth-Lens-Mini-Project.git
cd Truth-Lens-Mini-Project
```

### 2. Create Your Branch
```bash
git checkout dev
git checkout -b <your-name>    # e.g., git checkout -b harsh
git push -u origin <your-name>
```

### 3. Create `.env` File
Create a `.env` file in the root (this is NOT pushed to git):

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/truthlens
GEMINI_API_KEY=ask_shivam_for_key
GOOGLE_FACTCHECK_API_KEY=ask_shivam_for_key
GNEWS_API_KEY=ask_shivam_for_key
JWT_SECRET=ask_shivam_for_key
```

### 4. Start Development
```bash
# Start backend
docker-compose up -d

# Start frontend
npm install
npm run dev
```

---

## 🆘 Common Issues

### Merge Conflicts
```bash
# If you get conflicts when pulling
git status                    # See which files have conflicts
# Open the files and look for <<<< and >>>> markers
# Fix the conflicts manually
git add .
git commit -m "fix: resolve merge conflicts"
```

### Reset to Clean State
```bash
# If things are really broken, reset to dev
git stash                     # Save your changes temporarily
git checkout dev
git pull origin dev
git checkout <your-branch>
git merge dev
git stash pop                 # Bring back your changes
```

### Ask for Help
Message the group chat before you do anything drastic!

---

## 📊 Current Status

**Version**: 1.0.0 (MVP Complete)
**Last Stable Commit**: December 10, 2025

### Working Features
- ✅ User authentication
- ✅ Claim analysis pipeline
- ✅ Domain trust scoring
- ✅ Fact-check integration
- ✅ LLM explanations
- ✅ Analysis history
- ✅ Dashboard navigation

---

## 📞 Communication

- **Before starting work**: Check if anyone else is working on the same area
- **Stuck on something**: Ask in group chat before spending hours
- **Merge conflicts**: Don't panic, ask for help
- **Ready to merge to dev**: Create a PR and notify the team

---

<div align="center">

**Remember: Small commits, frequent pushes, always test before pushing!**

</div>
