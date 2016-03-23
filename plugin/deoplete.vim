"=============================================================================
" FILE: deoplete.vim
" AUTHOR:  Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

if exists('g:loaded_deoplete')
  finish
endif
let g:loaded_deoplete = 1

command! -nargs=0 -bar DeopleteEnable call deoplete#init#enable()

" Global options definition. "{{{
if get(g:, 'deoplete#enable_at_startup', 0)
  augroup deoplete
    autocmd CursorHold * call deoplete#init#enable()
    autocmd InsertEnter * call deoplete#init#enable()
          \ | doautocmd <nomodeline> deoplete InsertEnter
  augroup END
endif
"}}}

" vim: foldmethod=marker
