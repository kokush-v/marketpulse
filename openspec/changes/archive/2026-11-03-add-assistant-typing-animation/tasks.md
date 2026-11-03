## 1. Frontend

- [x] 1.1 Replace the "Assistant is thinking…" text with an animated three-dot typing indicator that keeps an accessible status label, in both widget and page layouts.
- [x] 1.2 Track which assistant replies were received in the current session so that only those replies use the progressive reveal; history loaded from the server renders instantly.
- [x] 1.3 Reveal a newly received assistant reply's text progressively word by word, keeping Markdown rendering readable during the reveal and keeping the chat scrolled to the bottom while it grows.
- [x] 1.4 Show the pending action card, price chart, sources, rating controls, and suggested replies only after the reveal completes.
- [x] 1.5 Disable the indicator animation and the reveal when the user prefers reduced motion.

## 2. Validation

- [x] 2.1 Run `docker compose exec -T frontend npm run lint`, `npm run typecheck`, and `npm run test -- --runInBand`; update existing assistant chat tests affected by the change.
- [x] 2.2 Run `openspec validate add-assistant-typing-animation --strict`.
