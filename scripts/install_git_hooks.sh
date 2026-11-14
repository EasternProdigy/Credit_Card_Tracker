#!/usr/bin/env bash
# One-time setup: git repo + a pre-commit hook that blocks secrets.
# Run from the repo root:  bash scripts/install_git_hooks.sh
set -euo pipefail
cd "$(dirname "$0")/.."

[ -d .git ] || git init -b main
mkdir -p secrets measurements/inbox
touch measurements/inbox/.gitkeep

if ! command -v gitleaks >/dev/null; then
  echo "Installing gitleaks (Fedora)..."
  sudo dnf install -y gitleaks || echo "Install gitleaks manually: https://github.com/gitleaks/gitleaks"
fi

cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
# Block commits that contain secrets.
if command -v gitleaks >/dev/null; then
  gitleaks protect --staged --redact -v || {
    echo "gitleaks found a possible secret. Commit blocked."; exit 1; }
else
  echo "warning: gitleaks not installed, secret scan skipped"
fi
# Block anything staged from secrets/ even if .gitignore was bypassed.
if git diff --cached --name-only | grep -q '^secrets/'; then
  echo "Refusing to commit files from secrets/."; exit 1
fi
HOOK
chmod +x .git/hooks/pre-commit
echo "Done. Pre-commit secret scan installed."
