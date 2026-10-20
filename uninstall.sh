#!/usr/bin/env bash
# Uninstalls Comandos Linux (does not touch the repository).
set -euo pipefail

NOMBRE="linux-commands-cheatsheet"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_HOME="${XDG_BIN_HOME:-$HOME/.local/bin}"

info()  { echo ":: $*"; }

rm -f  "$BIN_HOME/comandos-linux"
rm -rf "$DATA_HOME/$NOMBRE"
rm -f  "$DATA_HOME/applications/comandos-linux.desktop"
rm -f  "$DATA_HOME/icons/hicolor/scalable/apps/comandos-linux.svg"
rm -f  "${XDG_DESKTOP_DIR:-$HOME/Desktop}/Comandos Linux.desktop"

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$DATA_HOME/applications" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
  gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

info "Linux Commands has been uninstalled."
