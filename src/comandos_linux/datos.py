"""Carga y filtrado del dataset de comandos."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_ID = "io.github.angelherman0130.LinuxCommandsCheatsheet"


def _candidatos() -> list[Path]:
    """Rutas donde puede vivir `comandos.json`, en orden de prioridad."""
    paquete = Path(__file__).resolve().parent
    raices = [
        Path(os.environ["COMANDOS_LINUX_DATA"]).parent
        if os.environ.get("COMANDOS_LINUX_DATA")
        else None,
        # Layout instalado y layout del repo: <...>/comandos_linux/datos/comandos.json
        paquete,
        # Layout del repo: src/comandos_linux/ -> ../../datos
        paquete.parent.parent,
        Path.home() / ".local" / "share" / "linux-commands-cheatsheet",
        Path("/usr/share/linux-commands-cheatsheet"),
    ]
    vistos: set[Path] = set()
    salida: list[Path] = []
    for raiz in raices:
        if raiz is None:
            continue
        ruta = raiz / "datos" / "comandos.json"
        if ruta not in vistos:
            vistos.add(ruta)
            salida.append(ruta)
    return salida


def ruta_datos() -> Path:
    """Devuelve la ruta del dataset, lanzando un error claro si no existe."""
    for ruta in _candidatos():
        if ruta.is_file():
            return ruta
    raise FileNotFoundError(
        "No se encontró comandos.json. Rutas probadas:\n  "
        + "\n  ".join(str(r) for r in _candidatos())
    )


def cargar() -> dict[str, Any]:
    """Carga el dataset completo."""
    with ruta_datos().open(encoding="utf-8") as fh:
        return json.load(fh)


def _texto_comando(cmd: dict[str, Any]) -> str:
    """Todo el texto buscable de un comando (incluye variantes)."""
    partes = [cmd.get("cmd", ""), cmd.get("desc", ""), cmd.get("ejemplo", "")]
    for valor in cmd.get("variantes", {}).values():
        partes.append(valor)
    return " ".join(partes).lower()


def filtrar(
    datos: dict[str, Any], texto: str = "", distro: str = "todas"
) -> list[dict[str, Any]]:
    """Filtra categorías/grupos/comandos.

    - `texto`: busca en comando, descripción, ejemplo, variantes y nombres.
    - `distro`: "todas" muestra las tres variantes; "u"/"f"/"a" solo la suya.
    """
    texto = (texto or "").strip().lower()
    salida: list[dict[str, Any]] = []

    for categoria in datos.get("categorias", []):
        coincide_categoria = texto in categoria.get("nombre", "").lower()
        grupos_salida: list[dict[str, Any]] = []

        for grupo in categoria.get("grupos", []):
            coincide_grupo = coincide_categoria or texto in grupo.get("nombre", "").lower()
            cmds_salida: list[dict[str, Any]] = []

            for cmd in grupo.get("comandos", []):
                if coincide_grupo or texto in _texto_comando(cmd):
                    cmds_salida.append(cmd)

            if cmds_salida:
                grupos_salida.append({"nombre": grupo.get("nombre", ""), "comandos": cmds_salida})

        if grupos_salida:
            salida.append({"nombre": categoria.get("nombre", ""), "grupos": grupos_salida})

    return salida


def variantes_visibles(cmd: dict[str, Any], distro: str) -> list[tuple[str, str]]:
    """Devuelve [(clave_distro, texto)] visibles según el filtro de distro.

    Para comandos con variantes muestra la(s) correspondiente(s); para el resto,
    devuelve el ejemplo normal como ("", texto).
    """
    variantes = cmd.get("variantes")
    if not variantes:
        ejemplo = cmd.get("ejemplo")
        return [("", ejemplo)] if ejemplo else []

    claves = ["u", "f", "a"] if distro == "todas" else [distro]
    return [(k, variantes[k]) for k in claves if k in variantes]


def total_comandos(datos: dict[str, Any]) -> int:
    return sum(
        len(grupo.get("comandos", []))
        for categoria in datos.get("categorias", [])
        for grupo in categoria.get("grupos", [])
    )


def clave_de(categoria: str, grupo: str, cmd: str) -> str:
    """Clave estable de un comando (se usa para los favoritos)."""
    return f"{categoria}::{grupo}::{cmd}"


def indice(datos: dict[str, Any]) -> dict[str, tuple[dict, dict, dict]]:
    """Mapa clave -> (categoría, grupo, comando) de todos los comandos."""
    salida: dict[str, tuple[dict, dict, dict]] = {}
    for categoria in datos.get("categorias", []):
        for grupo in categoria.get("grupos", []):
            for cmd in grupo.get("comandos", []):
                clave = clave_de(categoria["nombre"], grupo["nombre"], cmd["cmd"])
                salida[clave] = (categoria, grupo, cmd)
    return salida
