"""Loading and filtering of the command dataset."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_ID = "io.github.angelherman0130.LinuxCommandsCheatsheet"

# Distribution families: the dataset key and its short name.
FAMILIAS: dict[str, str] = {"d": "Debian", "f": "Fedora", "a": "Arch"}

# Full names, for tooltips and texts.
FAMILIAS_LARGAS: dict[str, str] = {
    "d": "Debian/Ubuntu",
    "f": "Fedora/RHEL",
    "a": "Arch",
}

# Keywords of /etc/os-release used to detect the system family.
DETECCION: list[tuple[tuple[str, ...], str]] = [
    (("arch", "manjaro", "endeavouros", "cachyos", "steamos"), "a"),
    (("debian", "ubuntu", "mint", "pop", "zorin", "elementary", "kali"), "d"),
    (("fedora", "rhel", "centos", "nobara", "rocky", "alma"), "f"),
]


def detectar_familia(ruta: str | Path | None = None) -> str | None:
    """Detecta la familia de distribuciones del sistema (None si es desconocida).

    Lee /etc/os-release y usa tanto ``ID`` como ``ID_LIKE`` para que
    Omarchy (ID=omarchy, ID_LIKE=arch) se detecte como Arch.
    """
    try:
        texto = Path(ruta or "/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        return None

    campos: dict[str, str] = {}
    for linea in texto.splitlines():
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            campos[clave.strip()] = valor.strip().strip('"').lower()

    candidatos = (
        campos.get("ID", ""),
        campos.get("ID_LIKE", ""),
    )
    for palabras, familia in DETECCION:
        for candidato in candidatos:
            if candidato in palabras:
                return familia
            for palabra in candidato.split():
                if palabra in palabras:
                    return familia
    return None


def _candidatos() -> list[Path]:
    """Places where `comandos.json` may live, in priority order."""
    paquete = Path(__file__).resolve().parent
    raices = [
        Path(os.environ["COMANDOS_LINUX_DATA"]).parent
        if os.environ.get("COMANDOS_LINUX_DATA")
        else None,
        # Installed layout and repo layout: <...>/comandos_linux/datos/comandos.json
        paquete,
        # Repo layout: src/comandos_linux/ -> ../../datos
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
    """Returns the dataset path, raising a clear error when missing."""
    for ruta in _candidatos():
        if ruta.is_file():
            return ruta
    raise FileNotFoundError(
        "No se encontró comandos.json. Rutas probadas:\n  "
        + "\n  ".join(str(r) for r in _candidatos())
    )


def cargar() -> dict[str, Any]:
    """Loads the whole dataset."""
    with ruta_datos().open(encoding="utf-8") as fh:
        return json.load(fh)


def _texto_comando(cmd: dict[str, Any]) -> str:
    """All the searchable text of a command (variants included)."""
    partes = [cmd.get("cmd", ""), cmd.get("desc", ""), cmd.get("ejemplo", "")]
    for valor in cmd.get("variantes", {}).values():
        partes.append(valor)
    return " ".join(partes).lower()


def filtrar(
    datos: dict[str, Any], texto: str = "", distro: str = "todas"
) -> list[dict[str, Any]]:
    """Filters categories/groups/commands.

    - `texto`: busca en comando, descripción, ejemplo, variantes y nombres.
    - `distro`: "todas" muestra las tres variantes; "d"/"f"/"a" solo la suya.
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
    """Returns the visible [(family_key, text)] pairs for a family filter.

    Para comandos con variantes muestra la(s) correspondiente(s); para el resto,
    devuelve el ejemplo normal como ("", texto).
    """
    variantes = cmd.get("variantes")
    if not variantes:
        ejemplo = cmd.get("ejemplo")
        return [("", ejemplo)] if ejemplo else []

    claves = ["d", "f", "a"] if distro == "todas" else [distro]
    return [(k, variantes[k]) for k in claves if k in variantes]


def total_comandos(datos: dict[str, Any]) -> int:
    return sum(
        len(grupo.get("comandos", []))
        for categoria in datos.get("categorias", [])
        for grupo in categoria.get("grupos", [])
    )


def clave_de(categoria: str, grupo: str, cmd: str) -> str:
    """Stable key of a command (used for favourites)."""
    return f"{categoria}::{grupo}::{cmd}"


def indice(datos: dict[str, Any]) -> dict[str, tuple[dict, dict, dict]]:
    """Map from key -> (category, group, command) for every command.

    La clave es estable entre idiomas (se calcula con los nombres originales).
    """
    salida: dict[str, tuple[dict, dict, dict]] = {}
    for categoria in datos.get("categorias", []):
        for grupo in categoria.get("grupos", []):
            for cmd in grupo.get("comandos", []):
                clave = cmd.get("clave") or clave_de(
                    categoria["nombre"], grupo["nombre"], cmd["cmd"]
                )
                salida[clave] = (categoria, grupo, cmd)
    return salida
