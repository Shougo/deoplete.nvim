"=============================================================================
" FILE: mapping.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#mapping#_init() abort
  " Note: The dummy function is needed for cpoptions bug in neovim
  inoremap <expr><silent> <Plug>_
        \ deoplete#mapping#_dummy('deoplete#mapping#_complete')
  inoremap <expr><silent> <Plug>+
        \ deoplete#mapping#_dummy('deoplete#mapping#_prev_complete')
endfunction
function! deoplete#mapping#_dummy(func) abort
  return "\<C-r>=".a:func."()\<CR>"
endfunction
function! deoplete#mapping#_complete() abort
  call complete(g:deoplete#_context.complete_position + 1,
        \ g:deoplete#_context.candidates)

  return ''
endfunction
function! deoplete#mapping#_prev_complete() abort
  call complete(g:deoplete#_filtered_prev.complete_position + 1,
        \ g:deoplete#_filtered_prev.candidates)

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
        \ {
        \  'event': 'Manual',
        \  'sources': deoplete#util#convert2list(a:sources)
        \ })
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
  let prev = g:deoplete#_prev_completion
  if empty(prev)
    return ''
  endif

  let complete_str = prev.input[prev.complete_position :]
  let candidates = filter(copy(prev.candidates),
        \ 'stridx(tolower(v:val.word), tolower(complete_str)) == 0')

  if empty(candidates) || complete_str ==# ''
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
function! deoplete#mapping#_insert_candidate(number) abort
  let prev = g:deoplete#_prev_completion
  let candidates = get(prev, 'candidates', [])
  let word = get(candidates, a:number, {'word': ''}).word
  if word ==# ''
    return ''
  endif

  " Get cursor word.
  let complete_str = prev.input[prev.complete_position :]
  return (pumvisible() ? "\<C-e>" : '')
        \ . repeat("\<BS>", strchars(complete_str)) . word
endfunction
