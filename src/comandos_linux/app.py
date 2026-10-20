"""Ventana principal (GTK4 + libadwaita): barra lateral + panel de contenido."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import datos as ds  # noqa: E402
from . import exportar  # noqa: E402
from . import prefs  # noqa: E402
from . import vistas  # noqa: E402

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
        self.distro: str = prefs.valor("distro", "todas") or "todas"
        self.favoritos: list[str] = prefs.favoritos()
        self.texto: str = ""
        self._registrar_acciones()

    # -- ciclo de vida ---------------------------------------------------
    def do_activate(self) -> None:
        if self.ventana is None:
            self.ventana = Ventana(self)
        self.ventana.present()

    # -- acciones --------------------------------------------------------
    def _registrar_acciones(self) -> None:
        acciones = {
            "buscar": self._accion_buscar,
            "favoritos": self._accion_favoritos,
            "exportar-html": self._accion_exportar_html,
            "exportar-md": self._accion_exportar_md,
            "about": self._accion_about,
        }
        for nombre, callback in acciones.items():
            accion = Gio.SimpleAction.new(nombre, None)
            accion.connect("activate", callback)
            self.add_action(accion)

    def _accion_buscar(self, *_a) -> None:
        if self.ventana:
            self.ventana.focar_busqueda()

    def _accion_favoritos(self, *_a) -> None:
        if self.ventana:
            self.ventana.ir_a("favoritos")

    def _accion_exportar_html(self, *_a) -> None:
        if self.ventana:
            self.ventana.exportar("html")

    def _accion_exportar_md(self, *_a) -> None:
        if self.ventana:
            self.ventana.exportar("md")

    def _accion_about(self, *_a) -> None:
        if self.ventana:
            self.ventana.about()

    # -- estado ----------------------------------------------------------
    def alternar_favorito(self, clave: str) -> bool:
        marcado = prefs.alternar_favorito(clave)
        if marcado:
            if clave not in self.favoritos:
                self.favoritos.insert(0, clave)
        elif clave in self.favoritos:
            self.favoritos.remove(clave)
        return marcado

    def es_favorito(self, clave: str) -> bool:
        return clave in self.favoritos


class Ventana(Adw.ApplicationWindow):
    """Ventana con barra lateral de navegación y panel de contenido."""

    def __init__(self, app: ComandosApp):
        super().__init__(application=app, title="Comandos Linux")
        self.set_default_size(1080, 780)
        self.app = app
        self.add_css_class("cheatsheet")

        self.menu = self._menu()
        self.paginas: dict[str, Gtk.Widget] = {}
        self.contenedores: dict[str, Gtk.Box] = {}
        self.indices: dict[str, tuple[dict, dict, dict]] = ds.indice(app.datos)

        self._construir()
        self._cargar_css()
        self._conectar_tema()
        self._conectar_teclas()
        self._rellenar()

        ultima = prefs.valor("pagina", "favoritos")
        self.ir_a(ultima if ultima in self.paginas else "favoritos")

    # -- construcción ----------------------------------------------------
    def _construir(self) -> None:
        self.split = Adw.NavigationSplitView()
        self.split.set_min_sidebar_width(280)
        self.split.set_max_sidebar_width(340)
        self.split.set_sidebar(self._construir_sidebar())

        self.pila = Gtk.Stack()
        self.pila.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.split.set_content(self._construir_contenido())

        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(self.split)
        self.set_content(self.toasts)

    def _construir_sidebar(self) -> Adw.NavigationPage:
        pagina = Adw.NavigationPage(title="Comandos Linux")

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.add_css_class("sidebar-header")
        header.set_title_widget(
            Adw.WindowTitle(title="Comandos Linux", subtitle="Ubuntu · Fedora · Arch")
        )
        toolbar.add_top_bar(header)

        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Filtro global de distribución
        self.grupo_distro = Adw.ToggleGroup()
        for clave, etiqueta in DISTROS:
            toggle = Adw.Toggle(label=etiqueta)
            toggle.set_name(clave)
            self.grupo_distro.add(toggle)
        self.grupo_distro.set_active_name(self.app.distro)
        self.grupo_distro.connect("notify::active", self._al_cambiar_distro)
        self.grupo_distro.add_css_class("filtro-distro")

        etiqueta_filtro = Gtk.Label(label="DISTRIBUCIÓN")
        etiqueta_filtro.add_css_class("lateral-seccion")
        etiqueta_filtro.set_xalign(0)
        caja.append(etiqueta_filtro)
        caja.append(self.grupo_distro)

        self.lista_lateral = Gtk.ListBox()
        self.lista_lateral.set_selection_mode(Gtk.SelectionMode.NONE)
        self.lista_lateral.add_css_class("lista-lateral")
        self.lista_lateral.connect("row-activated", self._al_activar_lateral)
        caja.append(self.lista_lateral)
        toolbar.set_content(caja)

        pagina.set_child(toolbar)
        return pagina

    def _construir_contenido(self) -> Adw.NavigationPage:
        pagina = Adw.NavigationPage(title="Comandos Linux")

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()

        # Título que se sustituye por el buscador al pulsar 🔍
        self.titulo_pagina = Adw.WindowTitle(title="Comandos Linux", subtitle="")
        self.buscador = Gtk.SearchEntry()
        self.buscador.set_hexpand(True)
        self.buscador.set_placeholder_text("Buscar comando, descripción o ejemplo…")
        self.buscador.connect("search-changed", self._al_buscar)

        pila_titulo = Gtk.Stack()
        pila_titulo.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        pila_titulo.add_named(self.titulo_pagina, "titulo")
        pila_titulo.add_named(self.buscador, "buscar")
        header.set_title_widget(pila_titulo)
        self.pila_titulo = pila_titulo

        boton_buscar = Gtk.ToggleButton(icon_name="system-search-symbolic")
        boton_buscar.add_css_class("flat-round")
        boton_buscar.set_tooltip_text("Buscar (Ctrl+K)")
        boton_buscar.connect("toggled", self._al_toggle_busqueda)
        self.boton_buscar = boton_buscar

        boton_menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
        boton_menu.set_menu_model(self.menu)
        boton_menu.set_tooltip_text("Menú")

        # El orden de pack_end es inverso: el último empaquetado queda a la derecha.
        header.pack_end(boton_menu)
        header.pack_end(boton_buscar)

        toolbar.add_top_bar(header)

        # Páginas de contenido
        self.pila.add_named(self._pagina_favoritos(), "favoritos")
        self.paginas["favoritos"] = self.pila.get_child_by_name("favoritos")

        for categoria in self.app.datos["categorias"]:
            slug = categoria["slug"]
            self.pila.add_named(self._pagina_categoria(categoria), slug)
            self.paginas[slug] = self.pila.get_child_by_name(slug)

        self.pila.add_named(self._pagina_resultados(), "resultados")
        self.paginas["resultados"] = self.pila.get_child_by_name("resultados")

        toolbar.set_content(self.pila)
        pagina.set_child(toolbar)
        return pagina

    def _pagina_categoria(self, categoria: dict) -> Gtk.ScrolledWindow:
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        caja.add_css_class("pagina")
        self.contenedores[categoria["slug"]] = caja
        return self._scroll(caja)

    def _pagina_favoritos(self) -> Gtk.ScrolledWindow:
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        caja.add_css_class("pagina")
        self.contenedores["favoritos"] = caja
        return self._scroll(caja)

    def _pagina_resultados(self) -> Gtk.ScrolledWindow:
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        caja.add_css_class("pagina")
        self.lista_resultados = Gtk.ListBox()
        self.lista_resultados.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.lista_resultados.add_css_class("tarjeta")
        self.lista_resultados.connect("row-activated", self._al_activar_resultado)
        caja.append(self.lista_resultados)
        self.estado_resultados = Gtk.Box()
        caja.append(self.estado_resultados)
        self.contenedores["resultados"] = caja
        return self._scroll(caja)

    def _scroll(self, caja: Gtk.Box) -> Gtk.ScrolledWindow:
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(caja)
        return scroll

    def _pagina_vacia(self) -> Gtk.ScrolledWindow:
        return self._pagina_favoritos()

    def _menu(self) -> Gio.Menu:
        menu = Gio.Menu()

        navegacion = Gio.Menu()
        navegacion.append("Buscar…", "app.buscar")
        navegacion.append("Favoritos", "app.favoritos")
        menu.append_section(None, navegacion)

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

    def _al_tecla(self, _control, keyval, _code, state) -> bool:
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        if ctrl and keyval in (Gdk.KEY_f, Gdk.KEY_k):
            self.focar_busqueda()
            return True
        if ctrl and keyval == Gdk.KEY_c:
            return self._copiar_seleccion()
        if ctrl and Gdk.KEY_0 <= keyval <= Gdk.KEY_9:
            indice = keyval - Gdk.KEY_0 - 1
            categorias = self.app.datos["categorias"]
            if 0 <= indice < len(categorias):
                self.ir_a(categorias[indice]["slug"])
            return True
        if keyval == Gdk.KEY_Escape:
            if self.buscador.get_text():
                self.buscador.set_text("")
                return True
            if self.boton_buscar.get_active():
                self.boton_buscar.set_active(False)
                return True
        return False

    # -- navegación ------------------------------------------------------
    def ir_a(self, slug: str) -> None:
        if slug not in self.paginas:
            return
        self.pila.set_visible_child_name(slug)
        self.split.set_show_content(True)
        prefs.guardar(pagina=slug)
        self._actualizar_titulo()

    def _actualizar_titulo(self) -> None:
        slug = self.pila.get_visible_child_name() or "favoritos"
        if slug == "favoritos":
            self.titulo_pagina.set_title("Favoritos")
            self.titulo_pagina.set_subtitle(
                f"{len(self.app.favoritos)} comandos guardados"
            )
        elif slug == "resultados":
            self.titulo_pagina.set_title("Resultados")
            self.titulo_pagina.set_subtitle(
                f"{self._cuenta_resultados()} coincidencias"
            )
        else:
            for categoria in self.app.datos["categorias"]:
                if categoria["slug"] == slug:
                    total = sum(len(g["comandos"]) for g in categoria["grupos"])
                    self.titulo_pagina.set_title(categoria["nombre"])
                    self.titulo_pagina.set_subtitle(f"{total} comandos")
                    break

    def _cuenta_resultados(self) -> int:
        return len(ds.filtrar(self.app.datos, self.app.texto, self.app.distro))

    # -- búsqueda --------------------------------------------------------
    def _al_toggle_busqueda(self, boton: Gtk.ToggleButton) -> None:
        self.pila_titulo.set_visible_child_name(
            "buscar" if boton.get_active() else "titulo"
        )
        if boton.get_active():
            self.buscador.grab_focus()

    def foco_busqueda(self) -> None:
        self.boton_buscar.set_active(True)
        self.buscador.grab_focus()

    def _al_buscar(self, entrada: Gtk.SearchEntry) -> None:
        self.app.texto = entrada.get_text()
        self._rellenar_resultados()
        if self.app.texto.strip():
            self.ir_a("resultados")
        else:
            self._actualizar_titulo()

    # -- distro ----------------------------------------------------------
    def _al_cambiar_distro(self, grupo: Adw.ToggleGroup, _param) -> None:
        nombre = grupo.get_active_name() or "todas"
        if nombre == self.app.distro:
            return
        self.app.distro = nombre
        prefs.guardar(distro=nombre)
        self._rellenar()

    # -- contenido -------------------------------------------------------
    def _rellenar(self) -> None:
        self._rellenar_sidebar()
        self._rellenar_favoritos()
        for categoria in self.app.datos["categorias"]:
            self._rellenar_categoria(categoria)
        self._rellenar_resultados()
        self._actualizar_titulo()

    def _rellenar_sidebar(self) -> None:
        lista = self.lista_lateral
        hijo = lista.get_first_child()
        while hijo is not None:
            siguiente = hijo.get_next_sibling()
            lista.remove(hijo)
            hijo = siguiente

        if self.app.favoritos:
            lista.append(vistas.seccion_lateral("FAVORITOS"))
            for clave in self.app.favoritos:
                entrada = self.indices.get(clave)
                if not entrada:
                    continue
                categoria, grupo, cmd = entrada
                fila = vistas.fila_lateral(
                    cmd["cmd"],
                    f"{categoria['nombre']} › {grupo['nombre']}",
                    "starred-symbolic",
                    self._al_alternar_favorito,
                    clave,
                    True,
                )
                fila.slug = categoria["slug"]
                lista.append(fila)

        lista.append(vistas.seccion_lateral("CATEGORÍAS"))
        for categoria in self.app.datos["categorias"]:
            total = sum(len(g["comandos"]) for g in categoria["grupos"])
            fila = vistas.fila_lateral(
                categoria["nombre"],
                f"{total} comandos",
                categoria.get("icono"),
            )
            fila.slug = categoria["slug"]
            lista.append(fila)

    def _al_activar_lateral(self, _lista, fila: Gtk.ListBoxRow) -> None:
        slug = fila.slug
        if slug:
            self.ir_a(slug)

    def _rellenar_favoritos(self) -> None:
        caja = self.contenedores["favoritos"]
        self._vaciar(caja)

        if not self.app.favoritos:
            caja.append(
                self._estado_vacio(
                    "starred-symbolic",
                    "Sin favoritos todavía",
                    "Pulsa la estrella de un comando para guardarlo aquí.",
                )
            )
            return

        filas = []
        for clave in self.app.favoritos:
            entrada = self.indices.get(clave)
            if not entrada:
                continue
            categoria, grupo, cmd = entrada
            filas.append(self._fila(cmd, categoria, grupo, clave, con_ruta=True))
        if filas:
            caja.append(vistas.tarjeta_sin_titulo(filas))

    def _rellenar_categoria(self, categoria: dict) -> None:
        caja = self.contenedores[categoria["slug"]]
        self._vaciar(caja)
        for grupo in categoria["grupos"]:
            filas = []
            for cmd in grupo["comandos"]:
                clave = ds.clave_de(categoria["nombre"], grupo["nombre"], cmd["cmd"])
                filas.append(self._fila(cmd, categoria, grupo, clave))
            if filas:
                caja.append(vistas.tarjeta(grupo["nombre"], filas))

    def _rellenar_resultados(self) -> None:
        self._vaciar(self.lista_resultados)

        coincidencias = ds.filtrar(self.app.datos, self.app.texto, self.app.distro)
        if not self.app.texto.strip():
            self._mostrar_estado(
                "system-search-symbolic",
                "Busca un comando",
                "Escribe arriba para filtrar los 91 comandos por nombre, "
                "descripción o ejemplo.",
            )
            return

        if not coincidencias:
            self._mostrar_estado(
                "system-search-symbolic",
                "Sin resultados",
                f"No hay ningún comando que coincida con «{self.app.texto}».",
            )
            return

        self.estado_resultados.set_visible(False)
        self.lista_resultados.set_visible(True)

        primero = True
        for categoria in coincidencias:
            for grupo in categoria["grupos"]:
                for cmd in grupo["comandos"]:
                    clave = ds.clave_de(
                        categoria["nombre"], grupo["nombre"], cmd["cmd"]
                    )
                    fila = self._fila(cmd, categoria, grupo, clave, con_ruta=True)
                    fila.add_css_class("fila-tarjeta")
                    if not primero:
                        fila.add_css_class("fila-separada")
                    primero = False
                    copiable = cmd.get("ejemplo") or cmd.get("cmd", "")
                    if cmd.get("variantes"):
                        copiable = cmd["variantes"].get(self.app.distro) or next(
                            iter(cmd["variantes"].values())
                        )
                    fila.copiar = copiable
                    self.lista_resultados.append(fila)

    def _mostrar_estado(self, icono: str, titulo: str, texto: str) -> None:
        self.lista_resultados.set_visible(False)
        self.estado_resultados.set_visible(True)
        self._vaciar(self.estado_resultados)
        self.estado_resultados.append(vistas.estado_vacio(icono, titulo, texto))

    def _al_activar_resultado(self, _lista, fila: Gtk.ListBoxRow) -> None:
        texto = fila.copiar
        if texto:
            self._al_copiar(None, texto)

    def _copiar_seleccion(self) -> bool:
        fila = self.lista_resultados.get_selected_row()
        if fila is None:
            return False
        texto = fila.copiar
        if texto:
            self._al_copiar(None, texto)
        return True

    def _fila(
        self,
        cmd: dict,
        categoria: dict,
        grupo: dict,
        clave: str,
        con_ruta: bool = False,
    ) -> Gtk.Box:
        nombres = self.app.datos.get("distros", {})
        variantes = [
            (nombres.get(k, k), texto)
            for k, texto in ds.variantes_visibles(cmd, self.app.distro)
        ]
        fila = vistas.fila_comando(
            cmd,
            clave,
            self.app.es_favorito(clave),
            self.app.distro,
            self._al_copiar,
            self._al_alternar_favorito,
            variantes,
        )
        if con_ruta:
            ruta = Gtk.Label(label=f"{categoria['nombre']}  ›  {grupo['nombre']}")
            ruta.add_css_class("cmd-ruta")
            ruta.set_xalign(0)
            fila.prepend(ruta)
        return fila

    def _estado_vacio(self, icono: str, titulo: str, texto: str) -> Gtk.Box:
        return vistas.estado_vacio(icono, titulo, texto)

    @staticmethod
    def _vaciar(caja: Gtk.Box) -> None:
        hijo = caja.get_first_child()
        while hijo is not None:
            siguiente = hijo.get_next_sibling()
            caja.remove(hijo)
            hijo = siguiente

    # -- acciones de la interfaz ----------------------------------------
    def _al_copiar(self, _boton, texto: str) -> None:
        portapapeles = self.get_display().get_clipboard()
        portapapeles.set(texto)
        self.aviso("Copiado al portapapeles")

    def _al_alternar_favorito(self, _boton, clave: str) -> None:
        marcado = self.app.alternar_favorito(clave)
        self._rellenar()
        self.aviso(
            "Añadido a favoritos" if marcado else "Quitado de favoritos"
        )

    def aviso(self, mensaje: str) -> None:
        toast = Adw.Toast(title=mensaje, timeout=2)
        self.toasts.add_toast(toast)

    def exportar(self, formato: str) -> None:
        titulo = "Exportar a HTML" if formato == "html" else "Exportar a Markdown"
        nombre = "comandos-linux.html" if formato == "html" else "comandos-linux.md"
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
            version="1.1.0",
            developer="Angel Herman",
            comments="Chuleta de comandos Linux para Ubuntu, Fedora y Arch. "
            "Funciona sin conexión a internet.",
            license_type=Gtk.License.GPL_3_0,
        )
        ventana.present()
