"""Reusable widget builders (rows, cards, chips)."""

from __future__ import annotations

from typing import Callable, Iterable

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Pango  # noqa: E402


# --- piezas --------------------------------------------------------------


def chip(texto: str) -> Gtk.Label:
    etiqueta = Gtk.Label(label=texto)
    etiqueta.add_css_class("cmd-chip")
    etiqueta.set_selectable(True)
    return etiqueta


def insignia(texto: str) -> Gtk.Label:
    etiqueta = Gtk.Label(label=texto)
    etiqueta.add_css_class("insignia")
    return etiqueta


def insignia_peligro(t: dict | None = None) -> Gtk.Label:
    etiqueta = Gtk.Label(label="⚠")
    etiqueta.add_css_class("insignia-peligro")
    etiqueta.set_tooltip_text(
        (t or {}).get(
            "tooltip_peligro",
            "Comando destructivo: lee el aviso antes de ejecutarlo",
        )
    )
    return etiqueta


def chip_boton(texto: str, al_copiar: Callable, t: dict | None = None) -> Gtk.Button:
    """The command itself: clicking it copies it."""
    boton = Gtk.Button()
    boton.add_css_class("chip-btn")
    boton.set_child(chip(texto))
    boton.set_tooltip_text((t or {}).get("tooltip_copiar_comando", "Copiar el comando"))
    boton.connect("clicked", al_copiar, texto)
    return boton


def ejemplo_boton(texto: str, al_copiar: Callable, t: dict | None = None) -> Gtk.Button:
    """An example line: clicking it copies it."""
    boton = Gtk.Button()
    boton.add_css_class("ejemplo-btn")
    etiqueta = Gtk.Label(label=texto)
    etiqueta.add_css_class("cmd-ejemplo")
    etiqueta.set_selectable(True)
    etiqueta.set_wrap(True)
    etiqueta.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    etiqueta.set_xalign(0)
    etiqueta.set_hexpand(True)
    boton.set_child(etiqueta)
    boton.set_hexpand(True)
    boton.set_tooltip_text((t or {}).get("tooltip_copiar_ejemplo", "Copiar el ejemplo"))
    boton.connect("clicked", al_copiar, texto)
    return boton


def boton_copiar(texto: str, al_copiar: Callable, t: dict | None = None) -> Gtk.Button:
    boton = Gtk.Button(icon_name="edit-copy-symbolic")
    boton.add_css_class("icono-btn")
    boton.set_tooltip_text((t or {}).get("tooltip_copiar", "Copiar al portapapeles"))
    boton.connect("clicked", al_copiar, texto)
    return boton


def boton_estrella(
    marcado: bool, clave: str, al_alternar: Callable, t: dict | None = None
) -> Gtk.Button:
    boton = Gtk.Button(
        icon_name="starred-symbolic" if marcado else "non-starred-symbolic"
    )
    boton.add_css_class("icono-btn")
    boton.add_css_class("estrella-btn")
    if marcado:
        boton.add_css_class("marcado")
    textos = t or {}
    boton.set_tooltip_text(
        textos.get(
            "tooltip_quitar_favorito" if marcado else "tooltip_anadir_favorito",
            "Quitar de favoritos" if marcado else "Añadir a favoritos",
        )
    )
    boton.connect("clicked", al_alternar, clave)
    return boton


# --- filas y tarjetas ----------------------------------------------------


def fila_comando(
    cmd: dict,
    clave: str,
    marcado: bool,
    distro: str,
    al_copiar: Callable,
    al_alternar: Callable,
    variantes: list[tuple[str, str]],
    t: dict | None = None,
) -> Gtk.Box:
    """Full command row: star, chip, description and examples."""
    fila = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    fila.add_css_class("fila-comando")

    arriba = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    arriba.add_css_class("fila-principal")

    arriba.append(boton_estrella(marcado, clave, al_alternar, t))
    if cmd.get("peligro"):
        arriba.append(insignia_peligro(t))
    arriba.append(chip_boton(cmd.get("cmd", ""), al_copiar, t))

    descripcion = Gtk.Label(label=cmd.get("desc", ""))
    descripcion.add_css_class("cmd-desc")
    descripcion.set_wrap(True)
    descripcion.set_xalign(0)
    descripcion.set_hexpand(True)
    arriba.append(descripcion)

    copiable = cmd.get("ejemplo") or cmd.get("cmd", "")
    if cmd.get("variantes"):
        copiable = cmd["variantes"].get(distro) or next(
            iter(cmd["variantes"].values())
        )
    arriba.append(boton_copiar(copiable, al_copiar, t))
    fila.append(arriba)

    ejemplos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    ejemplos.add_css_class("fila-ejemplos")
    for clave_distro, texto in variantes:
        linea = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        if clave_distro:
            linea.append(insignia(clave_distro))
        linea.append(ejemplo_boton(_con_prefijo(texto), al_copiar, t))
        ejemplos.append(linea)
    if variantes:
        fila.append(ejemplos)

    aviso = cmd.get("peligro")
    if aviso:
        linea = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        linea.add_css_class("aviso-peligro")
        icono = Gtk.Label(label="⚠")
        linea.append(icono)
        texto = Gtk.Label(label=aviso)
        texto.add_css_class("aviso-texto")
        texto.set_wrap(True)
        texto.set_xalign(0)
        linea.append(texto)
        fila.append(linea)

    return fila


def _con_prefijo(texto: str) -> str:
    """Examples starting with '#' are comments, not commands."""
    texto = texto.strip()
    if texto.startswith("#"):
        return texto
    return "$ " + texto


def tarjeta(titulo: str, filas: Iterable[Gtk.Widget]) -> Gtk.Box:
    """Card for a group of commands, with thin separators between rows."""
    caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    if titulo:
        encabezado = Gtk.Label(label=titulo)
        encabezado.add_css_class("grupo-titulo")
        encabezado.set_xalign(0)
        caja.append(encabezado)
    caja.append(bloque(filas))
    return caja


def tarjeta_sin_titulo(filas: Iterable[Gtk.Widget]) -> Gtk.Box:
    """Card without a heading (favourites and results)."""
    caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    caja.append(bloque(filas))
    return caja


def bloque(filas: Iterable[Gtk.Widget]) -> Gtk.Box:
    """Stacked rows with thin separators, inside a card."""
    contenedor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    contenedor.add_css_class("tarjeta")
    for indice, fila in enumerate(filas):
        fila.add_css_class("fila-tarjeta")
        if indice:
            fila.add_css_class("fila-separada")
        contenedor.append(fila)
    return contenedor


def fila_lateral(
    titulo: str,
    subtitulo: str,
    icono: str | None,
    al_favorito: Callable | None = None,
    clave: str = "",
    marcado: bool = False,
) -> Gtk.ListBoxRow:
    """Sidebar row (favourites or categories).

    Navigation is handled by the sidebar through ``row-activated``;
    here we only build the content.
    """
    fila = Gtk.ListBoxRow()
    fila.set_activatable(True)
    fila.add_css_class("fila-lateral")

    caja = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    if icono:
        imagen = Gtk.Image.new_from_icon_name(icono)
        imagen.add_css_class("icono-lateral")
        caja.append(imagen)

    textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    etiqueta = Gtk.Label(label=titulo)
    etiqueta.add_css_class("lateral-titulo")
    etiqueta.set_xalign(0)
    textos.append(etiqueta)
    if subtitulo:
        detalle = Gtk.Label(label=subtitulo)
        detalle.add_css_class("lateral-detalle")
        detalle.set_xalign(0)
        textos.append(detalle)
    caja.append(textos)

    if al_favorito is not None:
        caja.append(boton_estrella(marcado, clave, al_favorito))

    fila.set_child(caja)
    return fila


def seccion_lateral(titulo: str) -> Gtk.Label:
    etiqueta = Gtk.Label(label=titulo)
    etiqueta.add_css_class("lateral-seccion")
    etiqueta.set_xalign(0)
    return etiqueta


def estado_vacio(icono: str, titulo: str, texto: str) -> Gtk.Box:
    """Compact empty state (icon + title + description)."""
    caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    caja.add_css_class("estado-vacio")
    caja.set_halign(Gtk.Align.CENTER)
    caja.set_valign(Gtk.Align.CENTER)
    caja.set_vexpand(True)

    imagen = Gtk.Image.new_from_icon_name(icono)
    imagen.add_css_class("estado-icono")
    caja.append(imagen)

    etiqueta = Gtk.Label(label=titulo)
    etiqueta.add_css_class("estado-titulo")
    caja.append(etiqueta)

    detalle = Gtk.Label(label=texto)
    detalle.add_css_class("estado-texto")
    detalle.set_wrap(True)
    detalle.set_justify(Gtk.Justification.CENTER)
    detalle.set_max_width_chars(44)
    caja.append(detalle)

    return caja
