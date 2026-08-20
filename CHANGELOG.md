# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 3 (History, Search, Favorites & UX)**
  - `HistoryPage` with advanced filtering and debounced global search.
  - `FavoritesPage` with support for custom Favorite Collections.
  - `AnalyticsPage` powered by `recharts` for timeline and issue distributions.
  - `ProfilePage` and `SettingsPage` (Dark/Light mode, JSON Data Export, Account Deletion).
  - Backend Redis caching for mock PDF/HTML report generation.
  - Backend smart filtering using PostgreSQL JSONB operations (Security Score, Tech Debt).
  - Enhanced Dashboard metrics (LOC analyzed, AI reviews this month, Avg Repo Score).
  - Seamless UX improvements via Loading Skeletons and premium Empty States.
- **Phase 1 (Foundation)**
  - Full-stack Vite/React/TS and FastAPI scaffolding.
  - Tailwind CSS v4 styling with dark mode support.
  - JWT Authentication, Contexts, and secure password hashing.
  - PostgreSQL database integration via SQLAlchemy (Async).
  - UI Component library (Buttons, Inputs, Cards, Modals, Toasts).
  - Docker Compose configuration for dev and production.
  
- **Phase 2 (Core Review Engine)**
  - Asynchronous AI Code Review integration using Google Gemini 2.0 Flash.
  - Language-aware Regex Static Analysis Engine (Python, JS/TS, Java, C/C++).
  - Background task processing for robust review ingestion.
  - Review Submission UI with 3 modes (Paste, Drag & Drop File Upload, GitHub URL).
  - Review Results Dashboard with Animated Scoreboards (`react-circular-progressbar`).
  - Side-by-Side original vs improved code diffing (`@monaco-editor/react`).
  - GitHub Repository cloner for aggregate codebase analysis.
  - CI/CD workflow configuration via GitHub Actions.
  - Ruff, Black, ESLint, and Prettier formatting integration.

### Fixed
- Fixed unhandled asynchronous execution blocking in `GeminiProvider`.
- Corrected frontend API schemas and unwrapped generic responses properly.
- Fixed invalid Radix UI `asChild` prop propagation in custom Button components.
- Resolved type mismatches between frontend `Review` interfaces and backend `ReviewResponse` payloads.
