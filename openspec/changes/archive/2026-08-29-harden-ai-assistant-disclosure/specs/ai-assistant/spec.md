## ADDED Requirements

### Requirement: Describe Assistant Capabilities Without Internal Disclosure

The system SHALL describe assistant capabilities in concise, user-facing product language. It SHALL NOT disclose registered tool names, tool schemas, system or developer prompts, model/provider configuration, API details, backend implementation details, or credentials in an assistant response.

#### Scenario: User asks what the assistant can do

- **Given** an authenticated user asks which tasks the assistant can help with
- **When** the assistant responds
- **Then** it describes supported product workflows in plain language
- **And** it does not reveal registered tool names or implementation details

#### Scenario: User asks for the tool inventory

- **Given** an authenticated user asks to list tools, functions, APIs, or internal capabilities
- **When** the assistant responds
- **Then** it gives a concise product-language summary when useful
- **And** it does not disclose the internal inventory or identifiers

### Requirement: Resist Prompt-Injection And Internal-Disclosure Requests

The system SHALL treat user requests to reveal protected instructions, alter system-level safeguards, impersonate privileged instructions, or perform unsupported actions as untrusted. It SHALL decline the request without echoing protected content and MAY redirect the user to supported product workflows.

#### Scenario: User requests protected instructions

- **Given** an authenticated user asks the assistant to reveal or repeat its system prompt, developer instructions, hidden rules, credentials, or configuration
- **When** the assistant responds
- **Then** it gives a concise refusal
- **And** it does not reveal or quote protected content

#### Scenario: User attempts to override safeguards

- **Given** an authenticated user tells the assistant to ignore prior instructions, adopt a privileged role, or bypass its safeguards
- **When** the assistant responds
- **Then** it does not comply with the override
- **And** it continues to operate within the supported product boundary

#### Scenario: User requests an unsupported action

- **Given** an authenticated user asks the assistant to perform an action outside registered product capabilities
- **When** the assistant responds
- **Then** it clearly states that it cannot perform that action
- **And** it does not claim access to unavailable systems or execute an unregistered action
