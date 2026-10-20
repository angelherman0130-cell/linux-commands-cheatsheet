"""Ventana principal (GTK4 + libadwaita): barra lateral + panel de contenido."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import datos as ds  # noqa: E402
from . import i18n  # noqa: E402
from . import exportar  # noqa: E402
from . import prefs  # noqa: E402
from . import vistas  # noqa: E402

CSS = Path(__file__).with_name("estilo.css")

# (clave, etiqueta corta, tooltip con el nombre completo)
DISTROS = [
    ("todas", "Todas", "Show every variant"),
    ("d", "Debian", "Debian/Ubuntu"),
    ("f", "Fedora", "Fedora/RHEL"),
    ("a", "Arch", "Arch"),
]


class ComandosApp(Adw.Application):
    """Aplicación: chuleta de comandos Linux por distro."""

    def __init__(self, datos: dict, **kwargs):
        super().__init__(
            application_id=ds.APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            **kwargs,
        )
        self.datos_base = datos
        self.idioma: str = prefs.valor("idioma", i18n.BASE) or i18n.BASE
        if not i18n.disponible(self.idioma):
            self.idioma = i18n.BASE
        self.datos = i18n.aplicar(datos, self.idioma)
        self.ventana: "Ventana | None" = None
        self.familia_detectada: str | None = ds.detectar_familia()
        guardada = prefs.valor("distro")
        if guardada in ds.FAMILIAS or guardada == "todas":
            self.distro: str = guardada
        else:
            # Primera ejecución: se usa la familia detectada del sistema.
            self.distro = self.familia_detectada or "todas"
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
            "detectar": self._accion_detectar,
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

    def _accion_detectar(self, *_a) -> None:
        if self.ventana:
            self.ventana.detectar_distro()

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

    # -- idioma ----------------------------------------------------------
    def texto(self, clave: str, defecto: str = "") -> str:
        """Cadena de la interfaz en el idioma actual."""
        return i18n.textos(self.idioma).get(clave, defecto)

    def meta(self, clave: str, defecto: str = "") -> str:
        return i18n.meta(self.idioma).get(clave, defecto)

    def cambiar_idioma(self, idioma: str) -> None:
        """Cambia el idioma de la interfaz y de los datos."""
        if not i18n.disponible(idioma) or idioma == self.idioma:
            return
        self.idioma = idioma
        prefs.guardar(idioma=idioma)
        self.datos = i18n.aplicar(self.datos_base, idioma)
        if self.ventana:
            self.ventana.recargar()

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

    @property
    def t(self) -> dict:
        """Cadenas de la interfaz en el idioma actual."""
        return i18n.textos(self.app.idioma)

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
        for clave, etiqueta, detalle in DISTROS:
            toggle = Adw.Toggle(label=etiqueta)
            toggle.set_name(clave)
            toggle.set_tooltip(detalle)
            self.grupo_distro.add(toggle)
        self.grupo_distro.set_active_name(self.app.distro)
        self.grupo_distro.connect("notify::active", self._al_cambiar_distro)
        self.grupo_distro.add_css_class("filtro-distro")

        etiqueta_filtro = Gtk.Label(
            label=self.t.get("seccion_distribucion", "DISTRIBUCIÓN")
        )
        etiqueta_filtro.add_css_class("lateral-seccion")
        etiqueta_filtro.set_xalign(0)
        self.etiqueta_distribucion = etiqueta_filtro
        caja.append(etiqueta_filtro)
        caja.append(self.grupo_distro)

        self.lista_lateral = Gtk.ListBox()
        self.lista_lateral.set_selection_mode(Gtk.SelectionMode.NONE)
        self.lista_lateral.add_css_class("lista-lateral")
        self.lista_lateral.connect("row-activated", self._al_activar_lateral)
        caja.append(self.lista_lateral)

        # Selector de idioma
        pie = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pie.add_css_class("pie-lateral")
        icono = Gtk.Image.new_from_icon_name("preferences-desktop-locale-symbolic")
        icono.add_css_class("icono-lateral")
        pie.append(icono)
        etiqueta_idioma = Gtk.Label(label=self.t.get("seccion_idioma", "IDIOMA"))
        etiqueta_idioma.add_css_class("lateral-detalle")
        pie.append(etiqueta_idioma)
        self.etiqueta_idioma = etiqueta_idioma
        self.selector_idioma = Gtk.DropDown.new_from_strings(
            [i18n.IDIOMAS["es"], i18n.IDIOMAS["en"]]
        )
        self.selector_idioma.set_selected(0 if self.app.idioma == "es" else 1)
        self.selector_idioma.set_hexpand(True)
        self.selector_idioma.connect("notify::selected", self._al_seleccionar_idioma)
        pie.append(self.selector_idioma)
        caja.append(pie)

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
        self.buscador.set_placeholder_text(
            self.t.get("buscar_placeholder", "Buscar comando, descripción o ejemplo…")
        )
        self.buscador.connect("search-changed", self._al_buscar)

        pila_titulo = Gtk.Stack()
        pila_titulo.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        pila_titulo.add_named(self.titulo_pagina, "titulo")
        pila_titulo.add_named(self.buscador, "buscar")
        header.set_title_widget(pila_titulo)
        self.pila_titulo = pila_titulo

        boton_buscar = Gtk.ToggleButton(icon_name="system-search-symbolic")
        boton_buscar.add_css_class("flat-round")
        boton_buscar.set_tooltip_text(self.t.get("tooltip_buscar", "Buscar (Ctrl+K)"))
        boton_buscar.connect("toggled", self._al_toggle_busqueda)
        self.boton_buscar = boton_buscar

        boton_menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
        boton_menu.set_menu_model(self._menu())
        boton_menu.set_tooltip_text(self.t.get("tooltip_menu", "Menú"))
        self.boton_menu = boton_menu

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
        t = self.t
        menu = Gio.Menu()

        navegacion = Gio.Menu()
        navegacion.append(t.get("menu_buscar", "Buscar…"), "app.buscar")
        navegacion.append(t.get("menu_favoritos", "Favoritos"), "app.favoritos")
        navegacion.append(
            t.get("menu_detectar", "Detectar mi distro"), "app.detectar"
        )
        menu.append_section(None, navegacion)

        export = Gio.Menu()
        export.append(t.get("menu_exportar_html", "Exportar a HTML…"), "app.exportar-html")
        export.append(t.get("menu_exportar_md", "Exportar a Markdown…"), "app.exportar-md")
        menu.append_section(None, export)

        menu.append(t.get("menu_acerca", "Acerca de Comandos Linux"), "app.about")
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

    def detectar_distro(self) -> None:
        """Vuelve al modo automático: usa la familia detectada del sistema."""
        self.app.familia_detectada = ds.detectar_familia()
        familia = self.app.familia_detectada
        if familia is None:
            self.app.distro = "todas"
            self.aviso(self.t.get("aviso_sin_deteccion", "No se pudo detectar tu distro"))
        else:
            self.app.distro = familia
            self.aviso(
                self.t.get("aviso_detectada", "Usando los comandos de {familia}").format(
                    familia=ds.FAMILIAS_LARGAS[familia]
                )
            )
        prefs.guardar(distro=self.app.distro)
        self.grupo_distro.set_active_name(self.app.distro)
        self._rellenar()
        self._actualizar_titulo()

    def recargar(self) -> None:
        """Recarga la ventana tras un cambio de idioma."""
        self.indices = ds.indice(self.app.datos)
        self.etiqueta_distribucion.set_label(
            self.t.get("seccion_distribucion", "DISTRIBUCIÓN")
        )
        self.etiqueta_idioma.set_label(self.t.get("seccion_idioma", "IDIOMA"))
        self.buscador.set_placeholder_text(
            self.t.get("buscar_placeholder", "Buscar comando, descripción o ejemplo…")
        )
        self.boton_menu.set_menu_model(self._menu())
        self.selector_idioma.set_selected(0 if self.app.idioma == "es" else 1)
        self._rellenar()
        self._actualizar_titulo()

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
            self.titulo_pagina.set_title(self.t.get("titulo_favoritos", "Favoritos"))
            self.titulo_pagina.set_subtitle(
                self.t.get("subtitulo_favoritos", "{n} comandos guardados").format(
                    n=len(self.app.favoritos)
                )
            )
        elif slug == "resultados":
            self.titulo_pagina.set_title(self.t.get("titulo_resultados", "Resultados"))
            self.titulo_pagina.set_subtitle(
                self.t.get("subtitulo_resultados", "{n} coincidencias").format(
                    n=self._cuenta_resultados()
                )
            )
        else:
            for categoria in self.app.datos["categorias"]:
                if categoria["slug"] == slug:
                    total = sum(len(g["comandos"]) for g in categoria["grupos"])
                    self.titulo_pagina.set_title(categoria["nombre"])
                    self.titulo_pagina.set_subtitle(
                        self.t.get("subtitulo_comandos", "{n} comandos").format(n=total)
                    )
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
            lista.append(vistas.seccion_lateral(self.t.get("seccion_favoritos", "FAVORITOS")))
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

        lista.append(vistas.seccion_lateral(self.t.get("seccion_categorias", "CATEGORÍAS")))
        for categoria in self.app.datos["categorias"]:
            total = sum(len(g["comandos"]) for g in categoria["grupos"])
            fila = vistas.fila_lateral(
                categoria["nombre"],
                f"{total} comandos",
                categoria.get("icono"),
            )
            fila.slug = categoria["slug"]
            lista.append(fila)

    def _al_seleccionar_idioma(self, selector: Gtk.DropDown, _param) -> None:
        nuevo = "es" if selector.get_selected() == 0 else "en"
        if nuevo != self.app.idioma:
            self.app.cambiar_idioma(nuevo)

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
                    self.t.get("vacio_favoritos_titulo", "Sin favoritos todavía"),
                    self.t.get(
                        "vacio_favoritos_texto",
                        "Pulsa la estrella de un comando para guardarlo aquí.",
                    ),
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
                self.t.get("vacio_buscar_titulo", "Busca un comando"),
                self.t.get(
                    "vacio_buscar_texto",
                    "Escribe arriba para filtrar los comandos por nombre, "
                    "descripción o ejemplo.",
                ),
            )
            return

        if not coincidencias:
            self._mostrar_estado(
                "system-search-symbolic",
                self.t.get("vacio_sin_resultados_titulo", "Sin resultados"),
                self.t.get(
                    "vacio_sin_resultados_texto",
                    "No hay ningún comando que coincida con «{texto}».",
                ).format(texto=self.app.texto),
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
            self.t,
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
        self.aviso(self.t.get("copiado", "Copiado al portapapeles"))

    def _al_alternar_favorito(self, _boton, clave: str) -> None:
        marcado = self.app.alternar_favorito(clave)
        self._rellenar()
        self.aviso(
            self.t.get(
                "anadido_favorito" if marcado else "quitado_favorito",
                "Añadido a favoritos" if marcado else "Quitado de favoritos",
            )
        )

    def aviso(self, mensaje: str) -> None:
        toast = Adw.Toast(title=mensaje, timeout=2)
        self.toasts.add_toast(toast)

    def exportar(self, formato: str) -> None:
        titulo = (
            self.t.get("dialogo_html", "Exportar a HTML")
            if formato == "html"
            else self.t.get("dialogo_md", "Exportar a Markdown")
        )
        nombre = "comandos-linux.html" if formato == "html" else "comandos-linux.md"
        dialogo = Gtk.FileDialog(title=titulo, initial_name=nombre)

        def terminado(origen, resultado, _f=formato):
            try:
                archivo = origen.save_finish(resultado)
            except GLib.Error as error:
                if error.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    return
                self.aviso(
                    self.t.get("error_exportar", "No se pudo exportar: {error}").format(
                        error=error.message
                    )
                )
                return
            ruta = archivo.get_path()
            if not ruta:
                return
            try:
                if _f == "html":
                    exportar.export_html(
                        self.app.datos, ruta, base=self.app.datos_base
                    )
                else:
                    exportar.export_md(self.app.datos, ruta)
            except OSError as error:
                self.aviso(
                    self.t.get("error_escribir", "No se pudo escribir: {error}").format(
                        error=error
                    )
                )
                return
            self.aviso(self.t.get("exportado", "Exportado a {ruta}").format(ruta=ruta))

        dialogo.save_async(self, None, terminado)

    def about(self) -> None:
        ventana = Adw.AboutWindow(
            transient_for=self,
            application_name="Comandos Linux",
            application_icon="comandos-linux",
            version="1.4.0",
            developer="Angel Herman",
            comments=self.t.get(
                "about_comentarios",
                "Chuleta de comandos Linux para Ubuntu, Fedora y Arch. "
                "Funciona sin conexión a internet.",
            ),
            license_type=Gtk.License.GPL_3_0,
        )
        ventana.present()
