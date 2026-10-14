## Description
<!-- Provide a concise summary of the change. Do not include verbose narrative filler. -->

## Type of Change
- [ ] `feat`: New feature or capability
- [ ] `fix`: Bug fix
- [ ] `refactor`: Code change that neither fixes a bug nor adds a feature
- [ ] `docs`: Documentation updates only
- [ ] `chore`: Tooling, workflow, or dependency maintenance

## Diff & Workspace Hygiene Checklist
- [ ] I have personally inspected the unified diff (`git diff`) top-to-bottom.
- [ ] I removed all conversational AI commentary, self-explanatory comments, and debug statements (`console.log`, `print()`, `debugger`).
- [ ] Workspace hygiene check passes locally (`python scripts/check_workspace_hygiene.py`).
- [ ] No temporary files, spike scripts, or unrequested docs exist in the repository root.
- [ ] All new specifications and permanent documentation are located in `openspec/` or `docs/`.

## Browser Verification Evidence
- [ ] Interactive browser tool used: record tool name, URL/scenario, and result.
- [ ] Automated Playwright used: record command, result, and report/artifact link.
- [ ] Both interactive browser and automated Playwright used.
- [ ] Browser verification unverified or not applicable: explain why; do not mark this as passing browser evidence.
