deoplete
========

Deoplete is the abbreviation of "dark powered neo-completion".  It
provides an asynchronous keyword completion system in the
current buffer.  Deoplete currently has few features and limited customization.
To view the current options, please consult the
[documentation](https://github.com/Shougo/deoplete.nvim/blob/master/doc%2Fdeoplete.txt).

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

![File Name Completion](https://cloud.githubusercontent.com/assets/7141867/11717027/a99cac54-9f73-11e5-91ce-bce9274692e4.png)

![Omni Completion](https://cloud.githubusercontent.com/assets/7141867/11717030/ae809a28-9f73-11e5-8c12-79fe9c460401.png)

![Neosnippets and neco-ghc integration](https://cloud.githubusercontent.com/assets/7141867/11717032/b4159c0e-9f73-11e5-91ee-404e6390366a.png)

![deoplete + echodoc integration](https://github.com/archSeer/nvim-elixir/blob/master/autocomplete.gif)

## Configuration Examples

```vim
" Use deoplete.
let g:deoplete#enable_at_startup = 1
```
