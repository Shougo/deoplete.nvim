"=============================================================================
" FILE: deoplete.vim
" AUTHOR:  Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

if exists('g:loaded_deoplete')
  finish
endif
let g:loaded_deoplete = 1

" Global options definition.
if get(g:, 'deoplete#enable_at_startup', 0)
  if has('vim_starting')
    augroup deoplete
      autocmd!
      autocmd VimEnter * call deoplete#enable()
    augroup END
  else
    call deoplete#enable()
  endif
endif
