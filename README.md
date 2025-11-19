<h1 align="center">
  <br>
    <img src="./logo.png" alt= "friman" width="200px">
</h1>
<h2 align="center">
    <b>friman</b>
<h2>

<p align="center">
    <a href="./README.md"><img src="https://img.shields.io/badge/Documentation-complete-green.svg?style=flat"></a>
    <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg"></a>
</p>

Do you ever feel that finding the right Frida version for the job is like threading a needle? With different projects, devices, and debugging scenarios all requiring specific builds, keeping track of Frida versions can quickly become a tedious balancing act. `friman` (pronounced "free man") is designed to solve exactly this problem.

## Overview

[Frida](https://github.com/frida/frida) evolves rapidly, and different projects or devices often require different versions. Switching manually can be error-prone, especially when juggling multiple environments, server binaries, and gadgets.

`friman` provides:

- Version installation and seamless switching
- Local version tracking
- A clean, isolated directory structure (`$HOME/.friman`)
- Helpers for downloading release assets (currently `frida-gadget` and `frida-server` assets)
- Convenience utilities for actions like pushing Frida server binaries to *Android* devices

Its goal is to make *Frida* version management **as frictionless as possible**.

## Install

The recommended installation method is directly from *GitHub*:

```sh
# With pipx (recommended)
pipx install git+https://github.com/thelicato/friman

# Or with pip
pip install git+https://github.com/thelicato/friman
```

After installing run the following:

```sh
friman ensurepath # Setup PATH and PYTHONPATH
friman update # Update the local list of available Frida versions
```

## Usage

`friman` provides a command-line interface for installing, switching, and managing multiple versions of Frida. The following is the main help output:

```sh
Usage: friman [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --version  Show the application's version and exit.
  -d, --debug    Show debug output.
  -h, --help     Show this message and exit.

Commands:
  update       Update the local list of available Frida versions.
  install      Install a <version> of Frida.
  uninstall    Uninstall a <version> of Frida.
  use          Use <version>.
  disable      Disable friman.
  current      Display the currently activated version of Frida.
  list         List all the installed versions.
  ensurepath   Ensure friman directories are correctly set.
  download     Download a specific release file (only server and gadget).
  push-server  Pushes a the Frida server into the selected ANDROID device.
```

Specific help commands are available in the below sections.

<details>
<summary>
WIP
</summary>

### `update` command
</details>

<details>
<summary>
WIP
</summary>

### `install` command
</details>

<details>
<summary>
WIP
</summary>

### `uninstall` command
</details>

<details>
<summary>
WIP
</summary>

### `use` command
</details>

<details>
<summary>
WIP
</summary>

### `disable` command
</details>

<details>
<summary>
WIP
</summary>

### `current` command
</details>

<details>
<summary>
WIP
</summary>

### `list` command
</details>

<details>
<summary>
WIP
</summary>

### `ensurepath` command
</details>

<details>
<summary>
WIP
</summary>

### `download` command
</details>

<details>
<summary>
WIP
</summary>

### `push-server` command
</details>

## Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

## License

_friman_ is released under the [MIT LICENSE](./LICENSE)