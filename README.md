deoplete
========

Deoplete is the abbreviation of "dark powered neo-completion".  It
provides an asynchronous keyword completion system in the
current buffer.  Deoplete cannot be customized and doesn't currently have many
features.  It is provided for testing purposes.

**Note:** It is still an alpha version!  It is not for production use.

## Installation

**Note:** deoplete requires Neovim(latest is recommended) with Python3 enabled.
See [requirements](#requirements) if you aren't sure whether you have this.

1. Extract the files and put them in your Neovim directory
   (usually `~/.config/nvim`).
2. Execute the `:UpdateRemotePlugins` or `:NeoBundleRemotePlugins` (for using
   NeoBundle) and restart Neovim.
3. Execute the `:DeopleteEnable` command or set `let g:deoplete#enable_at_startup = 1`
   in your `$XDG_CONFIG_HOME/nvim/init.vim`

## Requirements

deoplete requires Neovim with if\_python3.
If `:echo has("python3")` returns `1`, then you're done; otherwise, see below.

You can enable Python3 interface with pip:

    sudo pip3 install neovim

If you want to read the Neovim-python/python3 interface install documentation,
you should read `:help nvim-python`.

## Screenshots

Nothing...

## Configuration Examples

```vim
" Use deoplete.
let g:deoplete#enable_at_startup = 1
```
