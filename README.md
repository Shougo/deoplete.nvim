deoplete
========

[![Join the chat at https://gitter.im/Shougo/deoplete.nvim](https://badges.gitter.im/Shougo/deoplete.nvim.svg)](https://gitter.im/Shougo/deoplete.nvim?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Deoplete is the abbreviation of "dark powered neo-completion".  It
provides an asynchronous keyword completion system in the
current buffer.
To view the current options, please consult the
[documentation](https://github.com/Shougo/deoplete.nvim/blob/master/doc%2Fdeoplete.txt).

## Installation

**Note:** deoplete requires Neovim(latest is recommended) with Python3 and
timers(neovim ver.0.1.5+) enabled.  See [requirements](#requirements) if you
aren't sure whether you have this.

1. Extract the files and put them in your Neovim directory
   (usually `$XDG_CONFIG_HOME/nvim/`).
2. Execute the `:UpdateRemotePlugins` and restart Neovim.
3. Write `call deoplete#enable()` or `let g:deoplete#enable_at_startup = 1` in
   your `init.vim`


For vim-plug

```viml
Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }
```

For dein.vim

```viml
call dein#add('Shougo/deoplete.nvim')
```


## Requirements

deoplete requires Neovim with if\_python3.
If `:echo has("python3")` returns `1`, then you're done; otherwise, see below.

You can enable Python3 interface with pip:

    pip3 install neovim

## Sources

deoplete will display completions via omnifunc by default.

Here are some [completion sources](https://github.com/Shougo/deoplete.nvim/wiki/Completion-Sources) specifically made for deoplete.nvim.


## Note: deoplete needs neovim-python ver.0.1.8+.
You need update neovim-python module.

    pip3 install --upgrade neovim

If you want to read the Neovim-python/python3 interface install documentation,
you should read `:help provider-python` and the Wiki.
https://github.com/zchee/deoplete-jedi/wiki/Setting-up-Python-for-Neovim

## Note: Python3 must be enabled before updating remote plugins
If Deoplete was installed prior to Python support being added to Neovim,
`:UpdateRemotePlugins` should be executed manually in order to enable
auto-completion.

## Screenshots

Deoplete for JavaScript
https://www.youtube.com/watch?v=oanoPTpiSF4

![File Name Completion](https://cloud.githubusercontent.com/assets/7141867/11717027/a99cac54-9f73-11e5-91ce-bce9274692e4.png)

![Omni Completion](https://cloud.githubusercontent.com/assets/7141867/11717030/ae809a28-9f73-11e5-8c12-79fe9c460401.png)

![Neosnippets and neco-ghc integration](https://cloud.githubusercontent.com/assets/7141867/11717032/b4159c0e-9f73-11e5-91ee-404e6390366a.png)

![deoplete + echodoc integration](https://github.com/archSeer/nvim-elixir/blob/master/autocomplete.gif)

![deoplete + deoplete-go integration](https://camo.githubusercontent.com/cfdefba43971bd44d466ead357bb296e38d7f88c/68747470733a2f2f6d656469612e67697068792e636f6d2f6d656469612f6c344b6930316d30314939424f485745302f67697068792e676966)

![deoplete + deoplete-typescript integration](https://github.com/mhartington/deoplete-typescript/blob/master/deoplete-tss.gif)

[Python completion using deoplete-jedi](https://cloud.githubusercontent.com/assets/3712731/17458493/8e10d1c0-5c44-11e6-8bd9-964f45365962.gif)

[C++ completion using clang_complete](https://cloud.githubusercontent.com/assets/3712731/17458501/cf88f89e-5c44-11e6-89a4-b4646aaa8021.gif)

[Java completion using vim-javacomplete2](https://cloud.githubusercontent.com/assets/3712731/17458504/f075e76a-5c44-11e6-97d5-c5525f61c4a9.gif)

[Vim Script completion using neco-vim](https://cloud.githubusercontent.com/assets/3712731/17461000/660e15be-5caf-11e6-8c02-eb9f9c169f3c.gif)

## Configuration Examples

```vim
" Use deoplete.
let g:deoplete#enable_at_startup = 1
```
