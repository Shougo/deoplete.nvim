"=============================================================================
" FILE: util.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#util#set_default(var, val, ...)  abort "{{{
  if !exists(a:var) || type({a:var}) != type(a:val)
    let alternate_var = get(a:000, 0, '')

    let {a:var} = exists(alternate_var) ?
          \ {alternate_var} : a:val
  endif
endfunction"}}}
function! deoplete#util#set_pattern(variable, keys, pattern) abort "{{{
  for key in split(a:keys, '\s*,\s*')
    if !has_key(a:variable, key)
      let a:variable[key] = a:pattern
    endif
  endfor
endfunction"}}}
function! deoplete#util#get_buffer_config(
      \ filetype, buffer_var, user_var, default_var, ...) abort "{{{
  let default_val = get(a:000, 0, '')

  if exists(a:buffer_var)
    return {a:buffer_var}
  endif

  let filetype = !has_key({a:user_var}, a:filetype)
        \ && !has_key(eval(a:default_var), a:filetype) ? '_' : a:filetype

  return get({a:user_var}, filetype,
        \   get(eval(a:default_var), filetype, default_val))
endfunction"}}}
function! deoplete#util#get_simple_buffer_config(buffer_var, user_var) abort "{{{
  return exists(a:buffer_var) ? {a:buffer_var} : {a:user_var}
endfunction"}}}
function! deoplete#util#print_error(string) abort "{{{
  echohl Error | echomsg '[deoplete] ' . a:string | echohl None
endfunction"}}}
function! deoplete#util#print_warning(string) abort "{{{
  echohl WarningMsg | echomsg '[deoplete] ' . a:string | echohl None
endfunction"}}}

function! deoplete#util#convert2list(expr) abort "{{{
  return type(a:expr) ==# type([]) ? a:expr : [a:expr]
endfunction"}}}

function! deoplete#util#get_input(event) abort "{{{
  let input = ((a:event ==# 'InsertEnter' || mode() ==# 'i') ?
        \   (col('.')-1) : col('.')) >= len(getline('.')) ?
        \      getline('.') :
        \      matchstr(getline('.'),
        \         '^.*\%' . (mode() ==# 'i' ? col('.') : col('.') - 1)
        \         . 'c' . (mode() ==# 'i' ? '' : '.'))

  if input =~ '^.\{-}\ze\S\+$'
    let complete_str = matchstr(input, '\S\+$')
    let input = matchstr(input, '^.\{-}\ze\S\+$')
  else
    let complete_str = ''
  endif

  if a:event ==# 'InsertCharPre'
    let complete_str .= v:char
  endif

  return input . complete_str
endfunction"}}}
function! deoplete#util#get_next_input(event) abort "{{{
  return getline('.')[len(deoplete#util#get_input(a:event)) :]
endfunction"}}}
function! deoplete#util#get_prev_event() abort "{{{
  return get(g:deoplete#_context, 'event', '')
endfunction"}}}

function! deoplete#util#vimoption2python(option) abort "{{{
  return '[a-zA-Z' . s:vimoption2python(a:option) . ']'
endfunction"}}}
function! deoplete#util#vimoption2python_not(option) abort "{{{
  return '[^a-zA-Z' . s:vimoption2python(a:option) . ']'
endfunction"}}}
function! s:vimoption2python(option) abort "{{{
  let has_dash = 0
  let patterns = []
  for pattern in split(a:option, ',')
    if pattern == ''
      " ,
      call add(patterns, ',')
    elseif pattern == '-'
      let has_dash = 1
    elseif pattern =~ '\d\+'
      call add(patterns, substitute(pattern, '\d\+',
            \ '\=nr2char(submatch(0))', 'g'))
    else
      call add(patterns, pattern)
    endif
  endfor

  " Dash must be last.
  if has_dash
    call add(patterns, '-')
  endif

  return join(deoplete#util#uniq(patterns), '')
endfunction"}}}

function! deoplete#util#uniq(list) abort "{{{
  let list = map(copy(a:list), '[v:val, v:val]')
  let i = 0
  let seen = {}
  while i < len(list)
    let key = string(list[i][1])
    if has_key(seen, key)
      call remove(list, i)
    else
      let seen[key] = 1
      let i += 1
    endif
  endwhile
  return map(list, 'v:val[0]')
endfunction"}}}

function! deoplete#util#redir(cmd) abort "{{{
  let [save_verbose, save_verbosefile] = [&verbose, &verbosefile]
  set verbose=0 verbosefile=
  redir => res
  silent! execute a:cmd
  redir END
  let [&verbose, &verbosefile] = [save_verbose, save_verbosefile]
  return res
endfunction"}}}

function! deoplete#util#get_syn_name() abort "{{{
  return len(getline('.')) < 200 ?
        \ synIDattr(synIDtrans(synID(line('.'), mode() ==# 'i' ?
        \          col('.')-1 : col('.'), 1)), 'name') : ''
endfunction"}}}

function! deoplete#util#neovim_version() abort "{{{
  redir => v
  silent version
  redir END
  return split(v, '\n')[0]
endfunction"}}}

" vim: foldmethod=marker
