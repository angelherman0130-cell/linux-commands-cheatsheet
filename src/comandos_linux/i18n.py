"""Translations of the interface and of the command dataset.

El español es el idioma base (los datos viven en el JSON). El inglés se
guarda en ``i18n/en.json`` y se aplica sobre una copia del dataset, de modo
que la búsqueda, los filtros y los favoritos funcionan igual en ambos idiomas.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

IDIOMAS: dict[str, str] = {"es": "Español", "en": "English"}
BASE = "es"
RUTA_EN = Path(__file__).with_name("i18n") / "en.json"

_cache: dict[str, dict[str, Any]] = {}


def disponible(idioma: str) -> bool:
    return idioma in IDIOMAS


def cargar(idioma: str) -> dict[str, Any]:
    """Returns the translation dictionary of a language."""
    if idioma not in IDIOMAS:
        idioma = BASE
    if idioma in _cache:
        return _cache[idioma]
    if idioma == BASE:
        datos = {"meta": {}, "ui": {}, "categorias": {}, "grupos": {},
                 "comandos": {}, "ejemplos": {}, "peligros": {}}
    else:
        try:
            datos = json.loads(RUTA_EN.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            datos = {}
    _cache[idioma] = datos
    return datos


def textos(idioma: str) -> dict[str, str]:
    """Interface strings of a language."""
    return cargar(idioma).get("ui", {})


def meta(idioma: str) -> dict[str, str]:
    """Title, subtitle and note of the dataset in a language."""
    return cargar(idioma).get("meta", {})


# Strings of the exported HTML (Spanish is the base language).
HTML_BASE: dict[str, str] = {
    "todas": "Todas",
    "expandir": "Expandir todo",
    "contraer": "Contraer todo",
    "coincidencias": "categoría(s) coinciden",
    "buscar_placeholder": "Buscar comando, descripción o ejemplo…",
}


def textos_html(idioma: str) -> dict[str, str]:
    """Interface strings of the exported HTML."""
    textos = dict(HTML_BASE)
    textos.update(cargar(idioma).get("ui", {}))
    textos.update(cargar(idioma).get("meta", {}))
    return textos


def _clave(categoria: str, grupo: str, cmd: str) -> str:
    return f"{categoria}::{grupo}::{cmd}"


def aplicar(datos: dict[str, Any], idioma: str) -> dict[str, Any]:
    """Returns a copy of the dataset with the texts of the given language.

    Las traducciones se indexan por el texto original en español, así que
    solo hay que traducir cada frase una vez. Cada comando conserva además
    una clave estable (``clave``) calculada con los nombres originales, para
    que los favoritos no cambien al cambiar de idioma.
    """
    if idioma not in IDIOMAS or idioma == BASE:
        for categoria in datos.get("categorias", []):
            for grupo in categoria.get("grupos", []):
                for cmd in grupo.get("comandos", []):
                    cmd["clave"] = _clave(
                        categoria["nombre"], grupo["nombre"], cmd["cmd"]
                    )
        return datos

    t = cargar(idioma)
    copia = deepcopy(datos)

    for campo, valor in t.get("meta", {}).items():
        if valor:
            copia[campo] = valor

    for categoria in copia.get("categorias", []):
        slug = categoria.get("slug", "")
        nombre_cat_original = categoria["nombre"]
        categoria["nombre"] = t.get("categorias", {}).get(slug, categoria["nombre"])
        for grupo in categoria.get("grupos", []):
            nombre_original = grupo["nombre"]
            grupo["nombre"] = (
                t.get("grupos", {}).get(
                    f"{slug}::{nombre_original}", nombre_original
                )
            )
            for cmd in grupo.get("comandos", []):
                cmd["clave"] = _clave(
                    nombre_cat_original, nombre_original, cmd["cmd"]
                )
                cmd["desc"] = t.get("comandos", {}).get(
                    cmd.get("desc", ""), cmd.get("desc", "")
                )
                if "ejemplo" in cmd:
                    cmd["ejemplo"] = t.get("ejemplos", {}).get(
                        cmd["ejemplo"], cmd["ejemplo"]
                    )
                if "peligro" in cmd:
                    cmd["peligro"] = t.get("peligros", {}).get(
                        cmd["peligro"], cmd["peligro"]
                    )

    return copia
