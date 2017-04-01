"=============================================================================
" FILE: mapping.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#mapping#_init() abort
  inoremap <silent> <Plug>_
        \ <C-r>=deoplete#mapping#_complete()<CR>
  inoremap <silent> <Plug>(deoplete_auto_refresh)
        \ <C-r>=deoplete#refresh()<CR>
endfunction

function! deoplete#mapping#_completefunc(findstart, base) abort
  if a:findstart
    return g:deoplete#_context.complete_position
  else
    return g:deoplete#_context.candidates
  endif
endfunction
function! deoplete#mapping#_complete() abort
  call complete(g:deoplete#_context.complete_position + 1,
        \ g:deoplete#_context.candidates)

  return ''
endfunction
function! deoplete#mapping#_set_completeopt() abort
  if exists('g:deoplete#_saved_completeopt')
    return
  endif
  let g:deoplete#_saved_completeopt = &completeopt
  set completeopt-=longest
  set completeopt+=menuone
  set completeopt-=menu
  if &completeopt !~# 'noinsert\|noselect'
    set completeopt+=noselect
  endif
endfunction
function! deoplete#mapping#_restore_completeopt() abort
  if exists('g:deoplete#_saved_completeopt')
    let &completeopt = g:deoplete#_saved_completeopt
    unlet g:deoplete#_saved_completeopt
  endif
endfunction
function! deoplete#mapping#_rpcrequest_wrapper(sources) abort
  call rpcnotify(g:deoplete#_channel_id,
        \ 'deoplete_manual_completion_begin',
        \ deoplete#init#_context('Manual', a:sources))
  return ''
endfunction
