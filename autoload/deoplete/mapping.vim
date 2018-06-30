"=============================================================================
" FILE: mapping.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#mapping#_init() abort
  " Note: The dummy function is needed for cpoptions bug in neovim
  " inoremap <expr><silent> <Plug>_ deoplete#mapping#_dummy_complete(v:false)
  inoremap <silent> <Plug>_ <C-r>=deoplete#mapping#_refresh()<CR>
  inoremap <silent> <Plug>+ <C-r>=deoplete#mapping#_complete()<CR>

  let s:prev_pos = -1
  let s:prev_candidates = []
endfunction

function! deoplete#mapping#_completefunc(findstart, base) abort
  if a:findstart
    return g:deoplete#_context.complete_position
  else
    return g:deoplete#_context.candidates
  endif
endfunction
function! deoplete#mapping#_dummy_complete(is_refresh) abort
  return (pumvisible() ? "\<C-e>" : '')
        \ . (a:is_refresh ? "\<C-r>=deoplete#mapping#_refresh()\<CR>"
        \                 : "\<C-r>=deoplete#mapping#_complete()\<CR>")
endfunction
function! deoplete#mapping#_complete() abort
  if s:prev_pos == g:deoplete#_context.complete_position + 1
    call complete(s:prev_pos, s:prev_candidates)
    call timer_start(15, {_ -> feedkeys("\<Plug>+", 'i')})
  else
    call deoplete#mapping#_refresh()
  endif

  return ''
endfunction
function! deoplete#mapping#_refresh() abort
  let pos = g:deoplete#_context.complete_position + 1
  let candidates = g:deoplete#_context.candidates
  " let candidates = [strftime("%c")]
  call complete(pos, candidates)
  let s:prev_pos = pos
  let s:prev_candidates = copy(candidates)
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
  return deoplete#util#rpcnotify(
        \ 'deoplete_manual_completion_begin',
        \ deoplete#init#_context('Manual', a:sources))
endfunction
function! deoplete#mapping#_undo_completion() abort
  if empty(v:completed_item)
    return ''
  endif

  let input = deoplete#util#get_input('')
  if strridx(input, v:completed_item.word) !=
        \ len(input) - len(v:completed_item.word)
    return ''
  endif

  return deoplete#smart_close_popup() .
        \  repeat("\<C-h>", strchars(v:completed_item.word))
endfunction
function! deoplete#mapping#_complete_common_string() abort
  if !deoplete#is_enabled()
    return ''
  endif

  " Get cursor word.
  let complete_str = matchstr(deoplete#util#get_input(''), '\w*$')

  if complete_str ==# '' || !has_key(g:deoplete#_context, 'candidates')
    return ''
  endif

  let candidates = filter(copy(g:deoplete#_context.candidates),
        \ 'stridx(tolower(v:val.word), tolower(complete_str)) == 0')

  if empty(candidates)
    return ''
  endif

  let common_str = candidates[0].word
  for candidate in candidates[1:]
    while stridx(tolower(candidate.word), tolower(common_str)) != 0
      let common_str = common_str[: -2]
    endwhile
  endfor

  if common_str ==# '' || complete_str ==? common_str
    return ''
  endif

  return (pumvisible() ? "\<C-e>" : '')
        \ . repeat("\<BS>", strchars(complete_str)) . common_str
endfunction
