## ADDED Requirements

### Requirement: User can change dashboard text size
The authenticated dashboard SHALL expose the existing Settings text-size control with supported values of 75%, 100%, 125%, and 150%, and changing the control SHALL visibly scale the dashboard shell.

#### Scenario: Change size with the Settings slider
- **WHEN** an authenticated user moves the text-size slider to 150%
- **THEN** the slider output reads `150%` and dashboard content has a larger rendered size than at 100%

#### Scenario: Return to the default size
- **WHEN** an authenticated user moves the text-size slider from 150% back to 100%
- **THEN** the output reads `100%` and the dashboard returns to its baseline scale without cumulative scaling

### Requirement: Text-size preference persists locally
The frontend SHALL store the selected supported value under a dedicated browser-local preference and SHALL restore it on reload without changing the font-family or dark-mode preferences.

#### Scenario: Restore a saved preference
- **WHEN** a user selects 125% and reloads the page in the same browser
- **THEN** the text-size output and rendered dashboard scale are 125%

#### Scenario: Handle missing or invalid saved data
- **WHEN** the dedicated preference is missing or contains a value other than 75, 100, 125, or 150
- **THEN** the dashboard starts at 100% and remains usable

### Requirement: Scaling preserves access to dashboard content
The scaled authenticated shell SHALL keep its existing navigation and internal main content scroll usable at the supported maximum scale.

#### Scenario: Use Settings at maximum scale
- **WHEN** an authenticated user selects 150% and navigates to Settings
- **THEN** the Settings control remains reachable and the main content can scroll to the lower Settings content
