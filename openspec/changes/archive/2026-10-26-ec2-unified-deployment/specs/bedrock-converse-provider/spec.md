# Capability: Amazon Bedrock Converse Runtime Provider

## ADDED Requirements

### Requirement: Zero-Credential IAM Role Authentication
The Bedrock LLM Provider SHALL resolve authentication credentials dynamically via the EC2 Instance Metadata Service (IMDSv2) using the attached IAM Role (`MainEC2Role`), prohibiting any static AWS Access Keys, Secret Keys, or AWS Profiles from being present in code, configuration, or environment files.

#### Scenario: Inference executes via IMDSv2 IAM credentials on EC2
- **GIVEN** an EC2 instance launched with instance profile `MainEC2Role`
- **AND** the environment variable `COPILOT_DEFAULT_PROVIDER=bedrock`
- **AND** no `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` variables are defined
- **WHEN** the Copilot processes a chat inquiry via `POST /api/v1/copilot/chat`
- **THEN** `boto3` queries IMDSv2 for temporary STS role credentials
- **AND** dispatches signed Signature Version 4 requests to `bedrock-runtime.us-east-1.amazonaws.com`
- **AND** returns conversational responses from Amazon Bedrock Nova Micro without credential errors

### Requirement: Cross-Region Bedrock Model Targeting
The provider SHALL explicitly target AWS Region `us-east-1` for Bedrock Runtime inference regardless of the host instance's deployment region (`ap-southeast-1`), with default model identifier `us.amazon.nova-micro-v1:0`.

#### Scenario: Inference routes to us-east-1 from ap-southeast-1 host
- **GIVEN** the application hosted in AWS Region `ap-southeast-1`
- **WHEN** `BedrockLLMProvider` initializes the `bedrock-runtime` client
- **THEN** the client configuration explicitly sets `region_name="us-east-1"`
- **AND** model ID defaults to `us.amazon.nova-micro-v1:0`

### Requirement: RFC 7807 Structured Problem Translation
Any exceptions originating from Amazon Bedrock Runtime SHALL be caught and transformed into RFC 7807 Problem payloads rather than raising unhandled 500 exceptions or exposing internal AWS tracebacks.

#### Scenario: Bedrock AccessDenied translated to RFC 7807 Forbidden
- **GIVEN** an EC2 instance where the IAM Role lacks `bedrock:InvokeModel` permissions
- **WHEN** a user initiates a chat turn
- **THEN** the provider catches the client error
- **AND** raises a `ProblemException` with status HTTP 403 Forbidden and code `FORBIDDEN`
- **AND** returns `application/problem+json` detailing required IAM role permissions
