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
  function! s:deoplete_lazy_enable()
    autocmd! deoplete_lazy_enable
    augroup! deoplete_lazy_enable
    call deoplete#enable()
  endfunction
  augroup deoplete_lazy_enable
    autocmd!
    autocmd CursorHold * call s:deoplete_lazy_enable()
    autocmd InsertEnter * call s:deoplete_lazy_enable()
          \ | silent! doautocmd <nomodeline> deoplete InsertEnter
  augroup END
endif
