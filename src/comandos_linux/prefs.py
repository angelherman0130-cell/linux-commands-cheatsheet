"""Persistent preferences: favourites, last view and active family.

Se guardan en ``~/.config/linux-commands-cheatsheet/estado.json`` para que la
app retome donde quedó la última vez.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

NOMBRE_APP = "linux-commands-cheatsheet"
ARCHIVO = "estado.json"


def ruta_config() -> Path:
    """App configuration folder (honours XDG_CONFIG_HOME)."""
    base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / NOMBRE_APP


def _leer() -> dict[str, Any]:
    archivo = ruta_config() / ARCHIVO
    if not archivo.is_file():
        return {}
    try:
        return json.loads(archivo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _guardar(datos: dict[str, Any]) -> None:
    try:
        ruta_config().mkdir(parents=True, exist_ok=True)
        archivo = ruta_config() / ARCHIVO
        temporal = archivo.with_suffix(".tmp")
        temporal.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporal.replace(archivo)
    except OSError:
        pass  # la app sigue funcionando aunque no se pueda guardar


# --- favoritos -----------------------------------------------------------

def favoritos() -> list[str]:
    """Keys of the commands marked as favourites, in order."""
    return [str(c) for c in _leer().get("favoritos", [])]


def alternar_favorito(clave: str) -> bool:
    """Marks or unmarks a favourite. Returns True when it is marked."""
    datos = _leer()
    lista = [str(c) for c in datos.get("favoritos", [])]
    if clave in lista:
        lista.remove(clave)
        marcado = False
    else:
        lista.insert(0, clave)
        marcado = True
    datos["favoritos"] = lista
    _guardar(datos)
    return marcado


# --- preferencias simples ------------------------------------------------

def valor(nombre: str, defecto: Any = None) -> Any:
    return _leer().get(nombre, defecto)


def guardar(**opciones: Any) -> None:
    datos = _leer()
    datos.update(opciones)
    _guardar(datos)
