<div align="center">

# Comandos Linux

**Chuleta de comandos para Ubuntu, Fedora y Arch — en una app de escritorio que funciona sin internet.**

![App Comandos Linux](docs/captura-app.png)

</div>

---

## ¿Qué es?

Una aplicación de escritorio nativa (GTK4 + libadwaita) con **91 comandos** Linux
organizados en **10 categorías** y **34 grupos**. Los comandos que cambian entre
distribuciones (instalar paquetes, activar servicios, herramientas de red…)
muestran la variante de **Ubuntu**, **Fedora** o **Arch** y tú eliges cuál ver.

- **100 % offline** — no hace ni una sola petición de red.
- **Búsqueda en vivo** por comando, descripción o ejemplo.
- **Copiar al portapapeles** con un clic en cada comando.
- **Modo oscuro/claro automático**, siguiendo el tema del sistema.
- Los mismos datos se pueden exportar a **HTML** (standalone) y a **Markdown**.

## ✨ Funciones

| | |
|---|---|
| 🔍 Buscar | Escribe en la barra superior; filtra al instante |
| 🧩 Filtrar por distro | Ubuntu · Fedora · Arch · Todas |
| 📋 Copiar | Botón en cada comando (o `Ctrl+C` sobre el ejemplo) |
| ⌨️ Atajo | `Ctrl+F` enfoca la búsqueda, `Esc` la limpia |
| 📤 Exportar | A HTML autocontenido o a Markdown, desde el menú ☰ |

## 📦 Instalación

```bash
git clone https://github.com/angelherman0130-cell/linux-commands-cheatsheet.git
cd linux-commands-cheatsheet
./install.sh
```

El instalador detecta tu distribución, instala las dependencias que falten
(solo pide `sudo` si de verdad son necesarias), deja el comando
`comandos-linux` en el `PATH` y añade la entrada al menú de aplicaciones.

> **¿No aparece en el menú?** Algunos lanzadores (como el Spotlight de Omarchy)
> solo leen las entradas `.desktop` al arrancar. Cierra sesión y vuelve a
> entrar, o reinicia el shell, y aparecerá. El comando `comandos-linux`
> funciona siempre.

### Dependencias

| Distribución | Paquetes |
|---|---|
| Arch / Omarchy / Manjaro | `python-gobject gtk4 libadwaita` |
| Ubuntu / Debian / Mint | `python3-gi gir1.2-gtk-4.0 gir1.2-adw-1` |
| Fedora / RHEL / Nobara | `python3-gobject gtk4 libadwaita` |

Si las dependencias no se pueden instalar, la app **no se rompe**: cae
automáticamente al modo HTML y abre la chuleta en el navegador.

### Desinstalar

```bash
./uninstall.sh
```

## 🚀 Uso

```bash
comandos-linux              # abre la app
comandos-linux --listar     # lista las categorías en la terminal
comandos-linux --export-html comandos-linux.html
comandos-linux --export-md comandos-linux.md
comandos-linux --version
```

También puedes abrirla desde el menú de aplicaciones como **«Comandos Linux»**.

## ✏️ Añadir o corregir comandos

Todos los datos viven en **un solo archivo**:

```
src/comandos_linux/datos/comandos.json
```

```jsonc
{
  "nombre": "Redes",
  "grupos": [
    {
      "nombre": "Instalar si falta",
      "comandos": [
        { "cmd": "dig", "desc": "consultas DNS", "ejemplo": "dig example.com" },

        // Si cambia según la distro, usa "variantes":
        { "cmd": "wget", "desc": "descargas", "variantes": {
          "u": "sudo apt install wget",
          "f": "sudo dnf install wget",
          "a": "sudo pacman -S wget"
        }}
      ]
    }
  ]
}
```

- `cmd` → el comando (monoespaciado).
- `desc` → descripción corta.
- `ejemplo` → ejemplo de uso. Si empieza por `#` se muestra como comentario.
- `variantes` → en lugar de `ejemplo` cuando el comando difiere por distro
  (`u` = Ubuntu, `f` = Fedora, `a` = Arch).

Guarda el archivo, reinicia la app y listo: la app, el HTML y el Markdown se
generan siempre desde esta misma fuente.

## 🗂️ Estructura

```
linux-commands-cheatsheet/
├── install.sh / uninstall.sh     # instalación en el usuario
├── pyproject.toml                # metadatos (permite pip install .)
├── src/comandos_linux/
│   ├── __main__.py               # CLI: --export-html, --export-md, --listar
│   ├── app.py                    # ventana GTK4 + libadwaita
│   ├── datos.py                  # carga, búsqueda y filtrado
│   ├── exportar.py               # exportadores HTML y Markdown
│   ├── estilo.css                # paleta y estilos
│   └── datos/comandos.json       # ← el dataset (fuente única)
├── assets/
│   ├── desktop/comandos-linux.desktop
│   └── iconos/comandos-linux.svg
└── docs/                         # capturas para el README
```

## 🛠️ Desarrollo

```bash
git clone https://github.com/angelherman0130-cell/linux-commands-cheatsheet.git
cd linux-commands-cheatsheet
PYTHONPATH=src python3 -m comandos_linux          # ejecutar sin instalar
PYTHONPATH=src python3 -m comandos_linux --export-md /tmp/prueba.md
```

Para una instalación de desarrollo también vale:

```bash
pip install -e .      # instala el comando `comandos-linux` en modo editable
```

---

## English summary

**Comandos Linux** is a native desktop app (GTK4 + libadwaita) that works
completely offline. It bundles 91 Linux commands in 10 categories for Ubuntu,
Fedora and Arch — including the distro-specific variants (package managers,
service activation, network tools). It offers live search, a distro filter,
one-click copy to the clipboard, automatic light/dark theming, and can export
the whole cheat sheet to a standalone HTML file or to Markdown.

The dataset lives in a single JSON file, so adding or fixing a command is a
one-line edit — the app, the HTML export and the Markdown export are all
generated from it.

## 📄 Licencia

MIT — ver [LICENSE](LICENSE).
