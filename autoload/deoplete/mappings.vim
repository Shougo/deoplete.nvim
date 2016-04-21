"=============================================================================
" FILE: mappings.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#mappings#_init() abort "{{{
  inoremap <silent> <Plug>(deoplete_start_complete)
        \ <C-r>=deoplete#mappings#_do_complete(g:deoplete#_context)<CR>
  inoremap <silent> <Plug>(deoplete_auto_refresh)
        \ <C-r>=deoplete#mappings#refresh()<CR>
endfunction"}}}

function! deoplete#mappings#_do_complete(context) abort "{{{
  if b:changedtick == get(a:context, 'changedtick', -1)
    call complete(a:context.complete_position + 1, a:context.candidates)
  endif

  return ''
endfunction"}}}
function! deoplete#mappings#_set_completeopt() abort "{{{
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
endfunction"}}}

function! deoplete#mappings#manual_complete(...) abort "{{{
  if deoplete#initialize()
    return
  endif

  " Start complete.
  return (pumvisible() ? "\<C-e>" : '')
        \ . "\<C-r>=deoplete#mappings#_rpcnotify_wrapper("
        \ . string(get(a:000, 0, [])) . ")\<CR>"
endfunction"}}}
function! deoplete#mappings#_rpcnotify_wrapper(sources) abort "{{{
  call rpcrequest(g:deoplete#_channel_id,
        \ 'deoplete_manual_completion_begin',
        \ deoplete#init#_context('Manual', a:sources))
  return ''
endfunction"}}}

function! deoplete#mappings#close_popup() abort "{{{
  let g:deoplete#_context.position = getpos('.')
  return pumvisible() ? "\<C-y>" : ''
endfunction"}}}
function! deoplete#mappings#smart_close_popup() abort "{{{
  let g:deoplete#_context.position = getpos('.')
  return pumvisible() ? "\<C-e>" : ''
endfunction"}}}
function! deoplete#mappings#cancel_popup() abort "{{{
  let g:deoplete#_context.position = getpos('.')
  return pumvisible() ? "\<C-e>" : ''
endfunction"}}}
function! deoplete#mappings#refresh() abort "{{{
  let g:deoplete#_context.refresh = 1
  return pumvisible() ? "\<C-e>" : ''
endfunction"}}}

function! deoplete#mappings#undo_completion() abort "{{{
  if !exists('v:completed_item') || empty(v:completed_item)
    return ''
  endif

  let input = deoplete#util#get_input('')
  if strridx(input, v:completed_item.word) !=
        \ len(input) - len(v:completed_item.word)
    return ''
  endif

  return deoplete#mappings#smart_close_popup() .
        \  repeat("\<C-h>", strchars(v:completed_item.word))
endfunction"}}}

" vim: foldmethod=marker
