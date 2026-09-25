# Deployment

- Never `rsync --delete` without verifying exclusion of runtime files (.token-override, state files, .env).
- Run the project test suite before any deploy. No untested deploys.
- Ansible playbooks: always `--check` (dry-run) first on production targets.
- Verify target directory exists and is non-empty before destructive sync.
