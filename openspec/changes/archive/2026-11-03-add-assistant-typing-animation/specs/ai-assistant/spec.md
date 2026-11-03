## ADDED Requirements

### Requirement: Show A Typing Indicator While A Reply Is Pending

The assistant chat SHALL show an animated typing indicator, with an accessible status label, while the assistant reply to a sent message is pending. The indicator SHALL be removed when the reply arrives or the request fails.

#### Scenario: User sends a message

- **Given** an authenticated user is in an assistant conversation
- **When** the user sends a message and the reply is pending
- **Then** the chat shows an animated typing indicator below the conversation
- **And** assistive technologies can announce that the assistant is responding

#### Scenario: Reply arrives or request fails

- **Given** the typing indicator is visible
- **When** the assistant reply arrives or the request fails
- **Then** the chat removes the typing indicator

### Requirement: Reveal New Assistant Replies Progressively

The assistant chat SHALL reveal the text of an assistant reply received during the current session progressively, word by word, and SHALL show the reply's attached content (pending action, price chart, sources, rating controls, and suggested replies) only after the text is fully revealed. Messages loaded from conversation history SHALL render immediately without the reveal.

#### Scenario: New reply arrives

- **Given** an authenticated user sent a message in the current session
- **When** the assistant reply arrives
- **Then** the reply text appears progressively word by word
- **And** the attached content of that reply appears after the full text is shown

#### Scenario: User opens an existing conversation

- **Given** an authenticated user has a conversation with recorded messages
- **When** the user opens that conversation
- **Then** all recorded messages and their attached content are shown immediately without the reveal

### Requirement: Respect Reduced Motion For Assistant Chat Animations

When the user's system requests reduced motion, the assistant chat SHALL show the typing indicator without animation and SHALL render new assistant replies and their attached content immediately.

#### Scenario: User prefers reduced motion

- **Given** an authenticated user whose system requests reduced motion
- **When** the user sends a message and the reply arrives
- **Then** the pending state is shown without animation
- **And** the reply text and its attached content appear immediately
