"=============================================================================
" FILE: mappings.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

" For compatibility.

function! deoplete#mappings#manual_complete(...) abort
  return call('deoplete#manual_complete', a:000)
endfunction

function! deoplete#mappings#close_popup() abort
  return deoplete#close_popup()
endfunction
function! deoplete#mappings#smart_close_popup() abort
  return deoplete#smart_close_popup()
endfunction
function! deoplete#mappings#cancel_popup() abort
  return deoplete#cancel_popup()
endfunction
function! deoplete#mappings#refresh() abort
  return deoplete#refresh()
endfunction

function! deoplete#mappings#undo_completion() abort
  return deoplete#undo_completion()
endfunction
