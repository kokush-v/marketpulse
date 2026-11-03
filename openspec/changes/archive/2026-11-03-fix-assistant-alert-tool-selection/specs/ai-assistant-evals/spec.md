## ADDED Requirements

### Requirement: Cover Alert Threshold, Timing, And Identification Cases

The eval suite SHALL include scenarios for an alert threshold without a unit, an alert request without timing, and an alert action when the user has several alerts for the named coin. A scenario turn MAY declare that no proposal is expected; such a turn SHALL fail when the agent run captured a proposal and SHALL accept lookup tool calls.

#### Scenario: Threshold without a unit

- **Given** a scenario where the user asks for an alert above a number without a unit
- **When** the suite runs that turn
- **Then** the turn passes only if the agent makes no tool call

#### Scenario: Several alerts for the named coin

- **Given** stub data with two alerts for one coin and a scenario asking to pause the alert for that coin
- **When** the suite runs that turn
- **Then** the turn passes only if no proposal was captured and no mutation was executed
- **And** a follow-up turn naming one alert's condition passes only if the agent calls the pause proposal tool

#### Scenario: Alert without timing

- **Given** a scenario where the user asks for a news alert without mentioning timing
- **When** the suite runs that turn
- **Then** the turn passes only if the agent calls the alert creation proposal tool for a coin news alert

#### Scenario: Suite meets the threshold after the fix

- **Given** the full scenario set including the new scenarios
- **When** the suite runs against the production model
- **Then** at least 90% of scenarios pass
