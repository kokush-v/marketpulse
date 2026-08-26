## MODIFIED Requirements

### Requirement: Guide Alert Creation Through A Visible Fixed Node Graph
The system SHALL guide alert creation and editing through a visible fixed node graph instead of a stepper.

#### Scenario: User moves through alert creation
- **Given** an authenticated user is creating or editing an alert
- **When** the flow renders
- **Then** the system shows a visible guided sequence of alert-authoring stages on a fixed canvas
- **And** the user advances through that sequence without facing one large undifferentiated form

#### Scenario: User reviews multiple stages at once
- **Given** an authenticated user is creating or editing an alert
- **When** the fixed node graph renders
- **Then** the main authoring nodes remain visible together
- **And** the user is not forced through a single active-step presentation

### Requirement: Use A Fixed Y-Shaped React Flow Canvas For Alert Authoring
The system SHALL use a React Flow canvas organized as a fixed Y-shaped graph of compact authoring nodes for alert create and edit flows, and SHALL NOT require a dedicated preview node.

#### Scenario: User opens alert creation
- **Given** an authenticated user opens the create-alert flow
- **When** the alert authoring screen loads
- **Then** the system renders a React Flow canvas for alert authoring
- **And** the canvas shows coin, scenario, and timing nodes feeding one central review/save node
- **And** the canvas does not show a separate preview node

#### Scenario: User opens alert editing
- **Given** an authenticated user has an existing alert
- **When** the user opens the edit flow
- **Then** the system renders the same fixed Y-shaped React Flow canvas populated with the existing alert state

### Requirement: Keep Alert Authoring Connections Fixed
The system SHALL define alert-authoring node connections in code and SHALL NOT allow the user to customize graph topology.

#### Scenario: User interacts with the flow
- **Given** an authenticated user is creating or editing an alert
- **When** the user interacts with the alert-authoring canvas
- **Then** the system allows guided interaction within nodes
- **And** the system does not allow the user to create, remove, or reconnect edges between nodes

### Requirement: Use Smooth Centered Edge Styling In The Alert Canvas
The system SHALL render alert-authoring edges as smooth curved visual connections that read as flowing from the outer authoring nodes into the central review/save node, and SHOULD visually approach node centers rather than emphasizing square connection points.

#### Scenario: User views connections between nodes
- **Given** an authenticated user is creating or editing an alert
- **When** the alert-authoring canvas renders its fixed edges
- **Then** the system shows smooth curved edges between the outer authoring nodes and the central review/save node
- **And** the visual connection style does not emphasize square handle-to-handle routing

### Requirement: Keep Alert Authoring Node Positions Fixed
The system SHALL keep alert-authoring node positions fixed in the canvas and SHALL NOT allow users to reposition nodes.

#### Scenario: User attempts to reposition a node
- **Given** an authenticated user is creating or editing an alert
- **When** the user interacts with a node on the canvas
- **Then** the node remains in its defined layout position
- **And** the user does not gain the ability to rearrange the graph

### Requirement: Use The Same Canvas Model On Mobile And Desktop
The system SHALL use the same alert-authoring canvas model on mobile and desktop.

#### Scenario: User opens the flow on desktop
- **Given** an authenticated user opens alert creation or editing on a desktop-sized viewport
- **When** the canvas renders
- **Then** the system presents the fixed React Flow authoring flow in a desktop-appropriate viewport

#### Scenario: User opens the flow on mobile
- **Given** an authenticated user opens alert creation or editing on a mobile-sized viewport
- **When** the canvas renders
- **Then** the system presents the same fixed React Flow authoring flow adapted for the smaller viewport
- **And** the system does not switch to a separate stepper-based or stacked-only authoring mode

### Requirement: Keep The Main Authoring Nodes Persistently Visible
The system SHALL keep the main authoring nodes persistently visible in the canvas and SHALL NOT rely on one node becoming active while the others collapse into inactive summaries.

#### Scenario: User edits one part of the flow
- **Given** an authenticated user is creating or editing an alert
- **When** the user interacts with one authoring node
- **Then** the other main authoring nodes remain visible in the canvas
- **And** the node presentation does not depend on switching the rest of the graph into inactive collapsed states

### Requirement: Use A Compact Watchlist-Only Coin Picker In The Coin Node
The system SHALL render the coin-selection node as a compact watchlist-only picker with a combobox-style in-node search field and dropdown selection, and SHALL NOT require a separate inline add-to-watchlist panel inside the alert-authoring canvas.

#### Scenario: User searches within saved coins
- **Given** an authenticated user is creating or editing an alert
- **And** the user has one or more saved watchlist coins
- **When** the user focuses the coin-selection node
- **Then** the system shows a compact combobox-style search field for filtering only that user's watchlist coins
- **And** the system shows matching saved coins in a dropdown selection list

#### Scenario: User needs a coin outside the watchlist
- **Given** an authenticated user is creating or editing an alert
- **When** the user searches for a coin that is not already in the user's watchlist
- **Then** the coin-selection node does not expand into a separate inline add-to-watchlist panel inside the alert-authoring canvas

### Requirement: Combine Scenario Selection And Scenario Configuration In One Node
The system SHALL combine scenario selection and scenario-specific configuration into one compact node.

#### Scenario: User chooses a scenario
- **Given** an authenticated user is creating or editing an alert
- **When** the user focuses the scenario node
- **Then** the system shows a scenario combobox with the supported scenarios
- **And** each scenario option includes its associated icon

#### Scenario: User configures the selected scenario
- **Given** an authenticated user has selected a scenario in the scenario node
- **When** the scenario node updates
- **Then** the system shows configuration controls for that selected scenario in the same node
- **And** the user does not need to move into a separate dedicated configuration node

### Requirement: Open Recurring Date Selection Through A Modal Calendar Interaction
The system SHALL preserve the current timing behavior model and SHALL open recurring date selection through a modal-style calendar interaction instead of rendering the full recurring calendar inline inside the timing node.

#### Scenario: User chooses recurring timing
- **Given** an authenticated user is creating or editing an alert
- **And** the user selects the recurring timing behavior
- **When** the user activates the start date or end date control
- **Then** the system opens a modal-style calendar interaction for choosing the recurring dates
