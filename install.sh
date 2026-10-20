#!/usr/bin/env bash
# Instala Comandos Linux en el usuario actual.
#   ./install.sh            -> instala (pide sudo solo si faltan dependencias)
#   ./install.sh --sin-deps -> no intenta instalar dependencias del sistema
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOMBRE="linux-commands-cheatsheet"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_HOME="${XDG_BIN_HOME:-$HOME/.local/bin}"
DESTINO="$DATA_HOME/$NOMBRE"
APLICACIONES="$DATA_HOME/applications"
ICONOS="$DATA_HOME/icons/hicolor/scalable/apps"

VERDE=$'\033[32m'; AMARILLO=$'\033[33m'; ROJO=$'\033[31m'; FIN=$'\033[0m'

info()  { echo "${VERDE}::${FIN} $*"; }
aviso() { echo "${AMARILLO}::${FIN} $*"; }
error() { echo "${ROJO}::${FIN} $*" >&2; }

CON_DEPS=1
ACCESO_DIRECTO=0

uso() {
  cat <<'EOF'
Uso: ./install.sh [opciones]

  --escritorio   Además crea un acceso directo en el Escritorio
                 (solo útil en escritorios que muestran iconos: GNOME, KDE…)
  --sin-deps     No intenta instalar dependencias del sistema
  -h, --help     Muestra esta ayuda
EOF
}

for arg in "$@"; do
  case "$arg" in
    --sin-deps)   CON_DEPS=0 ;;
    --escritorio) ACCESO_DIRECTO=1 ;;
    -h|--help)    uso; exit 0 ;;
    *) aviso "Opción desconocida: $arg"; uso; exit 1 ;;
  esac
done

echo
echo "  Comandos Linux — instalador"
echo "  ---------------------------"
echo

# --- 1. sistema ---------------------------------------------------------
[[ -f /etc/os-release ]] && . /etc/os-release
DISTRO="${ID:-desconocido}"
FAMILIA="${ID_LIKE:-$DISTRO}"

info "Sistema detectado: $PRETTY_NAME"

# --- 2. dependencias ----------------------------------------------------
tiene_gui() {
  python3 - <<'PY' >/dev/null 2>&1
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw  # noqa: F401
PY
}

paquetes_para() {
  # Se prueba el ID y también ID_LIKE (Omarchy: ID=omarchy, ID_LIKE=arch).
  for id in "$1" "$2"; do
    case "$id" in
      arch|archlinux|endeavouros|manjaro) echo "python-gobject gtk4 libadwaita"; return ;;
      ubuntu|debian|linuxmint|pop|elementary|zorin) echo "python3-gi gir1.2-gtk-4.0 gir1.2-adw-1"; return ;;
      fedora|rhel|centos|nobara) echo "python3-gobject gtk4 libadwaita"; return ;;
    esac
  done
  echo ""
}

if tiene_gui; then
  info "Dependencias GTK4/libadwaita: ya instaladas"
elif [[ $CON_DEPS -eq 0 ]]; then
  aviso "Faltan las dependencias y se pidió --sin-deps; la app usará el modo HTML."
else
  PAQUETES="$(paquetes_para "$DISTRO" "$FAMILIA")"
  if [[ -z "$PAQUETES" ]]; then
    aviso "Distro no reconocida ($DISTRO). Instala a mano:"
    aviso "  - python3 con PyGObject (gi), GTK 4 y libadwaita"
  else
    echo
    aviso "Faltan dependencias. Se instalarán: $PAQUETES"
    read -r -p "¿Continuar? [s/N] " respuesta
    if [[ "${respuesta,,}" == "s" ]]; then
      if command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed $PAQUETES
      elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y $PAQUETES
      elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y $PAQUETES
      else
        error "No se encontró un gestor de paquetes conocido."
        exit 1
      fi
    else
      aviso "Continuando sin dependencias; la app funcionará en modo HTML."
    fi
  fi
fi

# --- 3. copiar el programa ---------------------------------------------
mkdir -p "$DESTINO"
rm -rf "$DESTINO/comandos_linux"
cp -r "$RAIZ/src/comandos_linux" "$DESTINO/comandos_linux"
find "$DESTINO" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
info "Programa copiado a $DESTINO"

# --- 4. lanzador --------------------------------------------------------
mkdir -p "$BIN_HOME"
cat > "$BIN_HOME/comandos-linux" <<EOF
#!/usr/bin/env python3
"""Lanzador de Comandos Linux (generado por install.sh)."""
import os
import sys

RUTA = os.path.join("$DESTINO")
if RUTA not in sys.path:
    sys.path.insert(0, RUTA)

from comandos_linux.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
EOF
chmod +x "$BIN_HOME/comandos-linux"
info "Lanzador: $BIN_HOME/comandos-linux"

# --- 5. entrada de menú e icono ---------------------------------------
mkdir -p "$APLICACIONES" "$ICONOS"
cp "$RAIZ/assets/desktop/comandos-linux.desktop" "$APLICACIONES/comandos-linux.desktop"
chmod +x "$APLICACIONES/comandos-linux.desktop"
cp "$RAIZ/assets/iconos/comandos-linux.svg" "$ICONOS/comandos-linux.svg"
info "Entrada de menú e icono instalados"

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$APLICACIONES" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
  gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

# --- 5b. acceso directo en el escritorio (opcional) ---------------------
if [[ $ACCESO_DIRECTO -eq 1 ]]; then
  ESCRITORIO="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
  mkdir -p "$ESCRITORIO"
  ACCESO="$ESCRITORIO/Comandos Linux.desktop"
  cp "$RAIZ/assets/desktop/comandos-linux.desktop" "$ACCESO"
  chmod +x "$ACCESO"
  # GNOME exige marcar el archivo como confiable para poder lanzarlo con doble clic.
  command -v gio >/dev/null 2>&1 && \
    gio set "$ACCESO" metadata::trusted true >/dev/null 2>&1 || true
  info "Acceso directo en el escritorio: $ACCESO"
fi

# --- 6. comprobar -------------------------------------------------------
echo
if [[ ":$PATH:" == *":$BIN_HOME:"* ]]; then
  info "Listo. Abre la app con:  comandos-linux"
else
  aviso "Instala esta línea en tu ~/.bashrc para poder usar 'comandos-linux':"
  echo "    export PATH=\"\$PATH:$BIN_HOME\""
fi
info "También aparecerá en el menú de aplicaciones como «Comandos Linux»."
aviso "Si no la ves enseguida, reinicia sesión (algunos lanzadores solo leen las"
aviso "entradas de menú al arrancar)."
echo

"$BIN_HOME/comandos-linux" --version 2>/dev/null || true
