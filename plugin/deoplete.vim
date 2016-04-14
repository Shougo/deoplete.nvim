"=============================================================================
" FILE: deoplete.vim
" AUTHOR:  Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

if exists('g:loaded_deoplete')
  finish
endif
let g:loaded_deoplete = 1

" Global options definition. "{{{
if get(g:, 'deoplete#enable_at_startup', 0) && !exists('#deoplete')
  augroup deoplete
    autocmd CursorHold * call deoplete#enable()
    autocmd InsertEnter * call deoplete#enable()
          \ | doautocmd <nomodeline> deoplete InsertEnter
  augroup END
endif
"}}}

" vim: foldmethod=marker
