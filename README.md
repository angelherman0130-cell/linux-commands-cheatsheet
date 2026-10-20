<div align="center">

# Linux Commands

**A Linux command cheat sheet for Ubuntu, Fedora and Arch — as a native desktop app that works completely offline.**

> The app is called *Comandos Linux* in Spanish and *Linux Commands* in English;
> it shows its own name in the language you pick.

![Linux Commands app](docs/captura-app.png)

</div>

---

## What is it?

A native desktop app (GTK4 + libadwaita) with **263 Linux commands** across
**15 categories**. Commands that differ between distributions (package
managers, service activation, firewalls…) show the **Ubuntu**, **Fedora** or
**Arch** variant, and you pick which one to see.

- **100 % offline** — it never makes a single network request.
- **Sidebar** with every category, its icon and a command count.
- **Instant search** by command, description or example, with flat results.
- **Favourites ⭐**: mark the commands you use daily and keep them saved.
- **Copy to the clipboard** with a single click (on the command or its example).
- **⚠️ Warnings on destructive commands**, so you never paste one blindly.
- **Distribution families**, auto-detected from your own system.
- **Spanish and English**, switchable at any time.
- The same data can be exported to **HTML** (standalone) and **Markdown**.

## 📚 What's inside

| Category | Commands | Category | Commands |
|---|---:|---|---:|
| 📁 Files and directories | 23 | 💽 Disks and mounts | 12 |
| 🔍 Search and text | 27 | ℹ️ System info | 21 |
| 📦 Compression and checksums | 15 | 🌿 Git | 17 |
| 🔒 Permissions and users | 17 | 🐳 Docker | 13 |
| ⚙️ Processes | 20 | 💻 Environment and shell | 12 |
| 🛠️ Services (systemd) | 15 | 🧰 Modern tools | 12 |
| 📥 Packages | 14 | ⌨️ Shortcuts | 14 |
| 🌐 Networking | 31 | **Total** | **263** |

### System services

![systemd services](docs/captura-servicios.png)

### Destructive commands come with a warning

![destructive command warnings](docs/captura-peligro.png)

## 🧭 Distribution families, not distributions

Of the 263 commands, **234 are identical** on any Linux and only **29 change**
depending on the package manager. So the app does not ask "Ubuntu, Fedora or
Arch?", it asks **which family does your system belong to?**:

| Family | Package manager | Also covers |
|---|---|---|
| **Debian/Ubuntu** | `apt`, `dpkg`, `ufw` | Debian, Mint, Pop!_OS, Zorin, elementary, Kali |
| **Fedora/RHEL** | `dnf`, `firewall-cmd` | RHEL, Rocky, Alma, CentOS Stream, Nobara |
| **Arch** | `pacman`, `nft` | Manjaro, EndeavourOS, SteamOS, CachyOS |

**And it detects it for you**: on startup the app reads `/etc/os-release`
(`ID` and `ID_LIKE`) and selects your family automatically. If you prefer to
always see the manual list, the ☰ menu has a **"Detect my distro"** entry to
go back to automatic mode.

The selector keeps four short buttons (`All │ Debian │ Fedora │ Arch`) so it
fits in the sidebar; the full name shows in the tooltip.

## 🌍 Two languages

The app is **in Spanish and English** — not just the buttons, but the
descriptions, examples, warnings and category names. The selector sits at the
**bottom of the sidebar** and your choice is remembered between sessions.

![The app in English](docs/captura-ingles.png)

Search follows the selected language too: type `permissions` in English and it
finds `chmod`, `chown`… even though the commands themselves stay the same.

The exported HTML carries its own language selector and accepts the `?lang=en`
(or `#lang=en`) parameter to open it directly in English.

## ✨ Features

| | |
|---|---|
| 🧭 Sidebar | Categories with icon and command count, favourites on top, distro filter |
| 🖧 Auto-detection | Detects your distribution family on startup and selects its commands |
| 🔍 Search | Type above; the view switches to flat results with each command's category |
| ⭐ Favourites | Star any command; they are saved between sessions |
| 📋 Copy | Click the command or its example; the clipboard is updated instantly |
| ⚠️ Warnings | Destructive commands are flagged with an amber warning |
| 🌍 Languages | Spanish and English, switchable instantly without restarting |
| ⌨️ Shortcuts | `Ctrl+K` search · `Ctrl+1..9` jump to category N · `Ctrl+C` copy the selected |
| 📤 Export | To a standalone HTML file or to Markdown, from the ☰ menu |
| 🌓 Theme | Light/dark automatically, following the system |

## 📦 Installation

```bash
git clone https://github.com/angelherman0130-cell/linux-commands-cheatsheet.git
cd linux-commands-cheatsheet
./install.sh
```

The installer detects your distribution, installs the missing dependencies
(it only asks for `sudo` when they are really needed), puts the
`comandos-linux` command in your `PATH` and adds the entry to the application
menu.

### Installer options

```bash
./install.sh                 # standard install
./install.sh --desktop       # also create a desktop shortcut
./install.sh --no-deps       # don't touch system dependencies
```

> **Not showing up in the menu?** Some launchers (such as Omarchy's Spotlight)
> only read `.desktop` entries at startup. Log out and back in, or restart the
> shell, and it will appear. The `comandos-linux` command always works.

### Dependencies

| Distribution | Packages |
|---|---|
| Arch / Omarchy / Manjaro | `python-gobject gtk4 libadwaita` |
| Ubuntu / Debian / Mint | `python3-gi gir1.2-gtk-4.0 gir1.2-adw-1` |
| Fedora / RHEL / Nobara | `python3-gobject gtk4 libadwaita` |

If the dependencies cannot be installed, the app **does not break**: it falls
back to HTML mode and opens the cheat sheet in your browser.

### Uninstalling

```bash
./uninstall.sh
```

### Shortcut

On Linux the equivalent of a Windows shortcut is the **application menu
entry**: it is installed in `~/.local/share/applications/` and shows up in any
launcher (Spotlight, the Omarchy menu, GNOME, KDE…). If your desktop shows
icons, `./install.sh --desktop` also leaves a ready-to-double-click icon in
`~/Desktop/`.

## 🚀 Usage

```bash
comandos-linux              # opens the app
comandos-linux --list       # prints the categories in the terminal
comandos-linux --export-html commands-linux.html
comandos-linux --export-md commands-linux.md
comandos-linux --export-md commands-linux-en.md --lang en
comandos-linux --version
```

You can also open it from the application menu as **"Linux Commands"**.

### Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+K` / `Ctrl+F` | Focus the search box |
| `Esc` | Clear the search / close the search box |
| `Ctrl+1` … `Ctrl+9` | Jump to category N |
| `Ctrl+C` | Copy the selected result |

## ✏️ Adding or fixing commands

All the data lives in **a single file**:

```
src/comandos_linux/datos/comandos.json
```

```jsonc
{
  "nombre": "Redes",
  "icono": "network-transmit-receive-symbolic",   // a system icon
  "slug": "redes",                                 // internal identifier
  "grupos": [
    {
      "nombre": "Instalar si falta",
      "comandos": [
        { "cmd": "dig", "desc": "consultas DNS", "ejemplo": "dig example.com" },

        // If it changes per family, use "variantes":
        { "cmd": "wget", "desc": "descargas", "variantes": {
          "d": "sudo apt install wget",      // Debian / Ubuntu
          "f": "sudo dnf install wget",      // Fedora / RHEL
          "a": "sudo pacman -S wget"         // Arch
        }},

        // If it is destructive, add "peligro" and the app flags it with a warning:
        { "cmd": "rm -rf dir", "desc": "recursivo y forzado",
          "ejemplo": "rm -rf build/",
          "peligro": "Borra todo el contenido sin preguntar" }
      ]
    }
  ]
}
```

- `cmd` → the command (monospaced).
- `desc` → short description.
- `ejemplo` → usage example. If it starts with `#` it is shown as a comment.
- `variantes` → instead of `ejemplo` when the command differs per family
  (`d` = Debian/Ubuntu, `f` = Fedora/RHEL, `a` = Arch).
- `peligro` → warning text for destructive commands (optional).
- `icono` → any icon from the system theme (`folder-symbolic`,
  `network-server-symbolic`, `edit-find-symbolic`…).

Save the file, restart the app and you're done: the app, the HTML and the
Markdown are all generated from this single source.

### The dataset is the Spanish base

The JSON holds the Spanish text; `src/comandos_linux/i18n/en.json` holds the
English translation, applied on top of it at runtime.

## 🗂️ Layout

```
linux-commands-cheatsheet/
├── install.sh / uninstall.sh     # per-user installation
├── pyproject.toml                # metadata (allows `pip install .`)
├── src/comandos_linux/
│   ├── __main__.py               # CLI: --export-html, --export-md, --lang, --list
│   ├── app.py                    # window: sidebar + content panel
│   ├── vistas.py                 # widget builders (rows, cards, chips)
│   ├── i18n.py                   # translation loading and dataset rewriting
│   ├── i18n/en.json              # ← the English translations
│   ├── prefs.py                  # favourites, language and other preferences
│   ├── datos.py                  # loading, searching and filtering
│   ├── exportar.py               # HTML and Markdown exporters
│   ├── estilo.css                # palette and styles
│   └── datos/comandos.json       # ← the dataset (single source of truth)
├── assets/
│   ├── desktop/comandos-linux.desktop
│   └── iconos/comandos-linux.svg
└── docs/                         # screenshots for the README
```

Favourites, the last visited category and the selected language are stored in
`~/.config/linux-commands-cheatsheet/estado.json` (created automatically).

### Adding a third language

1. Copy `src/comandos_linux/i18n/en.json` as `i18n/fr.json` and translate its
   sections (`meta`, `ui`, `categorias`, `grupos`, `comandos`, `ejemplos`,
   `peligros`).
2. Register the language in `i18n.py`:

```python
IDIOMAS = {"es": "Español", "en": "English", "fr": "Français"}
```

3. Add its name to `HTML_BASE` for the exported HTML.

Translations are indexed **by the original text**, so each phrase only has to
be translated once even when it shows up in several commands.

## 🛠️ Development

```bash
git clone https://github.com/angelherman0130-cell/linux-commands-cheatsheet.git
cd linux-commands-cheatsheet
PYTHONPATH=src python3 -m comandos_linux          # run without installing
PYTHONPATH=src python3 -m comandos_linux --export-md /tmp/test.md
```

For a development install you can also use:

```bash
pip install -e .      # installs the `comandos-linux` command in editable mode
```

## 📄 License

MIT — see [LICENSE](LICENSE).
