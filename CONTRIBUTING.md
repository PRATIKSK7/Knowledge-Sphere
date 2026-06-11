# Contributing to Knowledge Sphere

First off, thank you for considering contributing to Knowledge Sphere! It's people like you that make open source such a fantastic community to learn, inspire, and create.

## Getting Started

1. **Fork the repository** and clone it locally.
2. **Set up your environment** following the Installation Guide in the `README.md`.
3. **Create a branch** for your edits (`git checkout -b feature/amazing-feature` or `bugfix/issue-123`).

## Development Workflow

- **Frontend**: Navigate to `frontend/`, run `npm install`, and use `npm run dev`. We use ESLint and Prettier. Please ensure your code passes `npm run lint`.
- **Backend**: Navigate to `backend/`, activate your virtual environment, install requirements, and run FastAPI via `uvicorn app.main:app --reload`.
- **Testing**: Ensure that `e2e_validation.py` runs successfully before submitting a pull request.

## Pull Request Process

1. Ensure your code aligns with our architectural patterns (e.g., separating AI routing logic in `llm_service.py`).
2. Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
3. Your PR should describe the problem you're solving and the solution you've implemented.
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Reporting Bugs
Use the GitHub Issues tab to report bugs. Please use the provided Bug Report template.

## Suggesting Enhancements
We are always looking for ways to make Knowledge Sphere better. Suggest features using the Feature Request template in the Issues tab.
