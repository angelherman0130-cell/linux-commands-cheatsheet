"""Entry point: `comandos-linux`."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from . import __version__
from . import datos as ds
from . import exportar


def _ruta_por_defecto(nombre: str) -> Path:
    return Path.cwd() / nombre


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="comandos-linux",
        description="Linux command cheat sheet for Ubuntu, Fedora and Arch (offline).",
    )
    parser.add_argument(
        "--export-html",
        nargs="?",
        const="",
        metavar="PATH",
        help="Export the cheat sheet to a standalone HTML file and exit.",
    )
    parser.add_argument(
        "--export-md",
        nargs="?",
        const="",
        metavar="PATH",
        help="Export the cheat sheet to Markdown and exit.",
    )
    parser.add_argument(
        "--list",
        "--listar",
        dest="listar",
        action="store_true",
        help="Print the categories and exit.",
    )
    parser.add_argument(
        "--lang",
        "--idioma",
        dest="idioma",
        choices=["es", "en"],
        default="es",
        help="Language of the export (default: es).",
    )
    parser.add_argument(
        "--version", action="version", version=f"comandos-linux {__version__}"
    )
    args = parser.parse_args(argv)

    try:
        datos = ds.cargar()
    except FileNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.listar:
        for categoria in datos.get("categorias", []):
            total = sum(len(g["comandos"]) for g in categoria["grupos"])
            print(f"{categoria['nombre']} ({total} commands)")
        print(f"\nTotal: {ds.total_comandos(datos)} commands")
        return 0

    if args.export_html is not None:
        destino = Path(args.export_html) if args.export_html else _ruta_por_defecto(
            "comandos-linux.html"
        )
        exportar.export_html(datos, destino)
        print(f"HTML exported to {destino}")
        return 0

    if args.export_md is not None:
        destino = Path(args.export_md) if args.export_md else _ruta_por_defecto(
            "comandos-linux.md"
        )
        exportar.export_md(datos, destino, idioma=args.idioma)
        print(f"Markdown exported to {destino}")
        return 0

    return _abrir_gui(datos)


def _abrir_gui(datos: dict) -> int:
    """Opens the app; without GTK4/libadwaita it falls back to the HTML file."""
    try:
        from .app import ComandosApp
    except (ImportError, ValueError) as error:
        print(
            f"Could not start the graphical interface ({error}).\n"
            "Opening the HTML version in your browser…",
            file=sys.stderr,
        )
        return _fallback_html(datos)

    app = ComandosApp(datos)
    return app.run([])


def _fallback_html(datos: dict) -> int:
    destino = Path(tempfile.gettempdir()) / "comandos-linux.html"
    exportar.export_html(datos, destino)
    try:
        subprocess.run(["xdg-open", str(destino)], check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Open it manually: {destino} ({error})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
