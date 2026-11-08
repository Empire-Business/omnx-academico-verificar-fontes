#!/usr/bin/env bash
# Instala a skill omnx-academico-verificar-fontes no Claude Code, copiando esta pasta para ~/.claude/skills/omnx-academico-verificar-fontes.
# Mac ou Linux. No Windows, veja o README.md.
set -euo pipefail
NOME="omnx-academico-verificar-fontes"
ORIGEM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESTINO="$HOME/.claude/skills/$NOME"
if [ "$ORIGEM" = "$DESTINO" ]; then
  echo "Esta pasta já é a skill instalada em $DESTINO. Nada a fazer."
  exit 0
fi
mkdir -p "$DESTINO"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude='.DS_Store' --exclude='__pycache__' --exclude='install.sh' "$ORIGEM/" "$DESTINO/"
else
  ( cd "$ORIGEM" && tar --exclude='.DS_Store' --exclude='__pycache__' --exclude='./install.sh' -cf - . ) | ( cd "$DESTINO" && tar -xf - )
fi
echo "Skill $NOME instalada em $DESTINO"
echo "Abra uma conversa nova no Claude Code para ela aparecer."
