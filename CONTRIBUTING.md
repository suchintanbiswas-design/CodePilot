# Contributing to CodePilot

First off, thank you for considering contributing to CodePilot! It's people like you that make this tool great.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please treat all contributors and users with respect.

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally.
3. **Install dependencies** for both the backend and frontend.
4. **Set up the environment** by copying `.env.example` to `.env` and filling in your API keys.

## Development Workflow

1. Create a descriptive branch for your feature or bug fix (`git checkout -b feature/amazing-feature`).
2. Write code that adheres to our style guidelines (see below).
3. Commit your changes with clear, descriptive commit messages.
4. Push your branch and open a Pull Request against the `main` branch.

## Code Formatting and Linting

CodePilot utilizes automated formatting and linting tools to maintain code quality. Please ensure your code passes all checks before submitting a PR.

### Backend (Python)
We use **Ruff** and **Black**.
- Run formatting: `black .`
- Run linting: `ruff check .`

### Frontend (TypeScript/React)
We use **ESLint** and **Prettier**.
- Run formatting: `npm run format`
- Run linting: `npm run lint`

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
3. You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.
