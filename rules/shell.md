# Shell

- Always start with `#!/usr/bin/env bash` and `set -euo pipefail`.
- Quote all variables: `"$var"`, not `$var`.
- Use `[[ ]]` over `[ ]`. Use `$(command)` over backticks.
- No inline credentials or absolute paths to home directories.
