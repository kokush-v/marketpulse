# MarketPulse Copilot Instructions

This repository follows OpenSpec-driven development.

Review rules:

- Check that implementation matches the related OpenSpec change.
- Do not approve code without a related OpenSpec change.
- Backend endpoints must have tests.
- User data must be scoped by authenticated user.
- External API keys must never be exposed to frontend.
- Health checks must not expose secrets or database credentials.
- CI must pass before merge.
- For frontend async screens, check loading, error, and empty states.
