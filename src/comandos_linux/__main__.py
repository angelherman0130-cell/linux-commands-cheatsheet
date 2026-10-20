"""Punto de entrada: `comandos-linux`."""

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
        description="Chuleta de comandos Linux para Ubuntu, Fedora y Arch (offline).",
    )
    parser.add_argument(
        "--export-html",
        nargs="?",
        const="",
        metavar="RUTA",
        help="Exporta la chuleta a un HTML autocontenido y termina.",
    )
    parser.add_argument(
        "--export-md",
        nargs="?",
        const="",
        metavar="RUTA",
        help="Exporta la chuleta a Markdown y termina.",
    )
    parser.add_argument(
        "--listar", action="store_true", help="Muestra las categorías y termina."
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
            print(f"{categoria['nombre']} ({total} comandos)")
        print(f"\nTotal: {ds.total_comandos(datos)} comandos")
        return 0

    if args.export_html is not None:
        destino = Path(args.export_html) if args.export_html else _ruta_por_defecto(
            "comandos-linux.html"
        )
        exportar.export_html(datos, destino)
        print(f"HTML exportado a {destino}")
        return 0

    if args.export_md is not None:
        destino = Path(args.export_md) if args.export_md else _ruta_por_defecto(
            "comandos-linux.md"
        )
        exportar.export_md(datos, destino)
        print(f"Markdown exportado a {destino}")
        return 0

    return _abrir_gui(datos)


def _abrir_gui(datos: dict) -> int:
    """Abre la app; si faltan GTK4/libadwaita, cae al HTML en el navegador."""
    try:
        from .app import ComandosApp
    except (ImportError, ValueError) as error:
        print(
            f"No se pudo iniciar la interfaz gráfica ({error}).\n"
            "Abriendo la versión HTML en el navegador…",
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
        print(f"Abre manualmente: {destino} ({error})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
