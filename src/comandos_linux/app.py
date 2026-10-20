"""Ventana principal (GTK4 + libadwaita)."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import datos as ds  # noqa: E402
from . import exportar  # noqa: E402

CSS = Path(__file__).with_name("estilo.css")

DISTROS = [("todas", "Todas"), ("u", "Ubuntu"), ("f", "Fedora"), ("a", "Arch")]


class ComandosApp(Adw.Application):
    """Aplicación: chuleta de comandos Linux por distro."""

    def __init__(self, datos: dict, **kwargs):
        super().__init__(
            application_id=ds.APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            **kwargs,
        )
        self.datos = datos
        self.ventana: "Ventana | None" = None
        self._registrar_acciones()

    # -- ciclo de vida ---------------------------------------------------
    def do_activate(self) -> None:
        if self.ventana is None:
            self.ventana = Ventana(self)
        self.ventana.present()

    # -- acciones --------------------------------------------------------
    def _registrar_acciones(self) -> None:
        acciones = {
            "expandir": self._accion_expandir,
            "contraer": self._accion_contraer,
            "exportar-html": self._accion_exportar_html,
            "exportar-md": self._accion_exportar_md,
            "about": self._accion_about,
        }
        for nombre, callback in acciones.items():
            accion = Gio.SimpleAction.new(nombre, None)
            accion.connect("activate", callback)
            self.add_action(accion)

    def _accion_expandir(self, *_a) -> None:
        if self.ventana:
            self.ventana.expandir(True)

    def _accion_contraer(self, *_a) -> None:
        if self.ventana:
            self.ventana.expandir(False)

    def _accion_exportar_html(self, *_a) -> None:
        if self.ventana:
            self.ventana.exportar("html")

    def _accion_exportar_md(self, *_a) -> None:
        if self.ventana:
            self.ventana.exportar("md")

    def _accion_about(self, *_a) -> None:
        if self.ventana:
            self.ventana.about()


class Ventana(Adw.ApplicationWindow):
    """Ventana con el árbol de comandos."""

    def __init__(self, app: ComandosApp):
        super().__init__(application=app, title="Comandos Linux")
        self.set_default_size(980, 780)
        self.app = app
        self.add_css_class("cheatsheet")

        self._texto = ""
        self._distro = "todas"
        # La primera categoría arranca abierta, igual que en la versión HTML.
        categorias = self.app.datos.get("categorias", [])
        self._expandidos: set[str] = {categorias[0]["nombre"]} if categorias else set()

        self._construir()
        self._cargar_css()
        self._conectar_tema()
        self._conectar_teclas()
        self.reconstruir()

    # -- construcción ----------------------------------------------------
    def _construir(self) -> None:
        self.toolbar = Adw.ToolbarView()

        header = Adw.HeaderBar()
        header.set_title_widget(
            Adw.WindowTitle(title="Comandos Linux", subtitle="Ubuntu · Fedora · Arch")
        )
        boton_menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
        boton_menu.set_menu_model(self._menu())
        boton_menu.set_tooltip_text("Menú")
        header.pack_end(boton_menu)
        self.toolbar.add_top_bar(header)

        contenido = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # --- fila superior: búsqueda + selector de distro ---
        fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        fila.set_margin_top(8)
        fila.set_margin_bottom(6)
        fila.set_margin_start(12)
        fila.set_margin_end(12)

        self.buscar = Gtk.SearchEntry()
        self.buscar.set_hexpand(True)
        self.buscar.set_placeholder_text("Buscar comando, descripción o ejemplo…")
        self.buscar.add_css_class("searchbar")
        self.buscar.connect("changed", self._al_buscar)
        fila.append(self.buscar)

        self.grupo_distro = Adw.ToggleGroup()
        for clave, etiqueta in DISTROS:
            toggle = Adw.Toggle(label=etiqueta)
            toggle.set_name(clave)
            self.grupo_distro.add(toggle)
        self.grupo_distro.set_active_name("todas")
        self.grupo_distro.connect("notify::active", self._al_cambiar_distro)
        fila.append(self.grupo_distro)
        contenido.append(fila)

        # --- nota ---
        self.nota = Gtk.Label(label=self.app.datos.get("nota", ""))
        self.nota.set_wrap(True)
        self.nota.set_xalign(0)
        self.nota.add_css_class("nota")
        self.nota.set_margin_start(12)
        self.nota.set_margin_end(12)
        self.nota.set_margin_bottom(6)
        contenido.append(self.nota)

        # --- árbol ---
        self.arbol = Gtk.ListBox()
        self.arbol.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self.arbol)
        contenido.append(scroll)

        self.toolbar.set_content(contenido)

        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(self.toolbar)
        self.set_content(self.toasts)

    def _menu(self) -> Gio.Menu:
        menu = Gio.Menu()

        arbol = Gio.Menu()
        arbol.append("Expandir todo", "app.expandir")
        arbol.append("Contraer todo", "app.contraer")
        menu.append_section(None, arbol)

        export = Gio.Menu()
        export.append("Exportar a HTML…", "app.exportar-html")
        export.append("Exportar a Markdown…", "app.exportar-md")
        menu.append_section(None, export)

        menu.append("Acerca de Comandos Linux", "app.about")
        return menu

    def _cargar_css(self) -> None:
        proveedor = Gtk.CssProvider()
        proveedor.load_from_string(CSS.read_text(encoding="utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), proveedor, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _conectar_tema(self) -> None:
        Adw.StyleManager.get_default().connect("notify::color-scheme", self._al_tema)
        ajustes = Gtk.Settings.get_default()
        if ajustes is not None:
            ajustes.connect(
                "notify::gtk-application-prefer-dark-theme", self._al_tema
            )
        self._al_tema()

    def _al_tema(self, *_a) -> None:
        esquema = Adw.StyleManager.get_default().get_color_scheme()
        if esquema == Adw.ColorScheme.FORCE_LIGHT:
            oscuro = False
        elif esquema == Adw.ColorScheme.FORCE_DARK:
            oscuro = True
        else:
            ajustes = Gtk.Settings.get_default()
            oscuro = bool(
                ajustes and ajustes.get_property("gtk-application-prefer-dark-theme")
            )
        if oscuro:
            self.add_css_class("dark")
        else:
            self.remove_css_class("dark")

    def _conectar_teclas(self) -> None:
        control = Gtk.EventControllerKey()
        control.connect("key-pressed", self._al_tecla)
        self.add_controller(control)

    def _al_tecla(self, _control, keyval, _keycode, state) -> bool:
        if keyval == Gdk.KEY_f and state & Gdk.ModifierType.CONTROL_MASK:
            self.buscar.grab_focus()
            return True
        if keyval == Gdk.KEY_Escape and self.buscar.has_focus():
            self.buscar.set_text("")
            return True
        return False

    # -- filtros ---------------------------------------------------------
    def _al_buscar(self, entry: Gtk.SearchEntry) -> None:
        self._texto = entry.get_text()
        self.reconstruir()

    def _al_cambiar_distro(self, grupo, _param) -> None:
        self._distro = grupo.get_active_name() or "todas"
        self.reconstruir()

    # -- árbol -----------------------------------------------------------
    def _expanders(self):
        """Itera los expanders reales (Gtk.ListBox los envuelve en filas)."""
        hijo = self.arbol.get_first_child()
        while hijo is not None:
            widget = hijo.get_child() if isinstance(hijo, Gtk.ListBoxRow) else hijo
            if isinstance(widget, Gtk.Expander):
                yield widget
            hijo = hijo.get_next_sibling()

    def reconstruir(self) -> None:
        hijo = self.arbol.get_first_child()
        while hijo is not None:
            siguiente = hijo.get_next_sibling()
            self.arbol.remove(hijo)
            hijo = siguiente

        categorias = ds.filtrar(self.app.datos, self._texto, self._distro)

        if not categorias:
            vacio = Gtk.Label(label="Sin resultados para la búsqueda.")
            vacio.add_css_class("dim")
            vacio.set_margin_top(30)
            caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            caja.append(vacio)
            self.arbol.append(caja)
            return

        for categoria in categorias:
            self.arbol.append(self._categoria(categoria))

    def _categoria(self, categoria: dict) -> Gtk.Expander:
        expander = Gtk.Expander()

        titulo = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        etiqueta = Gtk.Label(label=categoria["nombre"])
        etiqueta.add_css_class("cat-title")
        titulo.append(etiqueta)
        contador = Gtk.Label(
            label=str(sum(len(g["comandos"]) for g in categoria["grupos"]))
        )
        contador.add_css_class("count")
        titulo.append(contador)
        expander.set_label_widget(titulo)

        nombre = categoria["nombre"]
        expander.connect(
            "notify::expanded",
            lambda _w, _p, n=nombre: self._registrar_expansion(n, _w.get_expanded()),
        )

        cuerpo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        cuerpo.add_css_class("tree-body")
        for grupo in categoria["grupos"]:
            cuerpo.append(self._grupo(grupo))
        expander.set_child(cuerpo)
        expander.set_expanded(bool(self._texto) or nombre in self._expandidos)
        return expander

    def _registrar_expansion(self, nombre: str, abierto: bool) -> None:
        if abierto:
            self._expandidos.add(nombre)
        else:
            self._expandidos.discard(nombre)

    def _grupo(self, grupo: dict) -> Gtk.Box:
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        titulo = Gtk.Label(label=grupo["nombre"])
        titulo.add_css_class("grp")
        titulo.set_xalign(0)
        caja.append(titulo)
        for cmd in grupo["comandos"]:
            caja.append(self._comando(cmd))
        return caja

    def _comando(self, cmd: dict) -> Gtk.Box:
        fila = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        fila.add_css_class("cmd")

        arriba = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        arriba.add_css_class("cmd-row")

        codigo = Gtk.Label(label=cmd.get("cmd", ""))
        codigo.add_css_class("cmd-label")
        codigo.set_selectable(True)
        arriba.append(codigo)

        descripcion = Gtk.Label(label=cmd.get("desc", ""))
        descripcion.add_css_class("desc")
        descripcion.set_wrap(True)
        descripcion.set_xalign(0)
        descripcion.set_hexpand(True)
        arriba.append(descripcion)

        copiable = cmd.get("ejemplo") or cmd.get("cmd", "")
        if cmd.get("variantes"):
            copiable = cmd["variantes"].get(self._distro) or next(
                iter(cmd["variantes"].values())
            )
        boton = Gtk.Button(icon_name="edit-copy-symbolic")
        boton.add_css_class("copy-btn")
        boton.set_tooltip_text("Copiar al portapapeles")
        boton.connect("clicked", self._al_copiar, copiable)
        arriba.append(boton)

        fila.append(arriba)

        for clave, texto in ds.variantes_visibles(cmd, self._distro):
            if clave:
                caja = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                insignia = Gtk.Label(label=self.app.datos["distros"].get(clave, clave))
                insignia.add_css_class("distro-badge")
                caja.append(insignia)
                mono = self._mono(self._con_prefijo(texto))
                caja.append(mono)
                fila.append(caja)
            else:
                fila.append(self._mono(self._con_prefijo(texto)))

        return fila

    def _mono(self, texto: str) -> Gtk.Label:
        etiqueta = Gtk.Label(label=texto)
        etiqueta.add_css_class("mono")
        etiqueta.add_css_class("example")
        etiqueta.set_selectable(True)
        etiqueta.set_wrap(True)
        etiqueta.set_xalign(0)
        etiqueta.set_hexpand(True)
        return etiqueta

    @staticmethod
    def _con_prefijo(texto: str) -> str:
        """Los ejemplos que empiezan por '#' son comentarios, no comandos."""
        texto = texto.strip()
        if texto.startswith("#"):
            return texto
        return "$ " + texto

    # -- acciones de la interfaz ----------------------------------------
    def _al_copiar(self, _boton, texto: str) -> None:
        portapapeles = self.get_display().get_clipboard()
        portapapeles.set(texto)
        self.aviso("Copiado al portapapeles")

    def aviso(self, mensaje: str) -> None:
        toast = Adw.Toast(title=mensaje, timeout=2)
        self.toasts.add_toast(toast)

    def expandir(self, valor: bool) -> None:
        """Expande o contrae todas las categorías (el estado se guarda solo)."""
        for expander in self._expanders():
            expander.set_expanded(valor)

    def exportar(self, formato: str) -> None:
        titulo = "Exportar a HTML" if formato == "html" else "Exportar a Markdown"
        nombre = (
            "comandos-linux.html" if formato == "html" else "comandos-linux.md"
        )
        dialogo = Gtk.FileDialog(title=titulo, initial_name=nombre)

        def terminado(origen, resultado, _f=formato):
            try:
                archivo = origen.save_finish(resultado)
            except GLib.Error as error:
                if error.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    return
                self.aviso(f"No se pudo exportar: {error.message}")
                return
            ruta = archivo.get_path()
            if not ruta:
                return
            try:
                if _f == "html":
                    exportar.export_html(self.app.datos, ruta)
                else:
                    exportar.export_md(self.app.datos, ruta)
            except OSError as error:
                self.aviso(f"No se pudo escribir: {error}")
                return
            self.aviso(f"Exportado a {ruta}")

        dialogo.save_async(self, None, terminado)

    def about(self) -> None:
        ventana = Adw.AboutWindow(
            transient_for=self,
            application_name="Comandos Linux",
            application_icon="comandos-linux",
            version="1.0.0",
            developer="Angel Herman",
            comments="Chuleta de comandos Linux para Ubuntu, Fedora y Arch. "
            "Funciona sin conexión a internet.",
            license_type=Gtk.License.GPL_3_0,
        )
        ventana.present()
