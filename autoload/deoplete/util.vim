"=============================================================================
" FILE: util.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#util#print_error(string, ...) abort
  let name = a:0 ? a:1 : 'deoplete'
  echohl Error | echomsg printf('[%s] %s', name,
        \ deoplete#util#string(a:string)) | echohl None
endfunction
function! deoplete#util#print_warning(string) abort
  echohl WarningMsg | echomsg '[deoplete] '
        \ . deoplete#util#string(a:string) | echohl None
endfunction
function! deoplete#util#print_debug(string) abort
  echomsg '[deoplete] ' . deoplete#util#string(a:string)
endfunction

function! deoplete#util#convert2list(expr) abort
  return type(a:expr) ==# v:t_list ? a:expr : [a:expr]
endfunction
function! deoplete#util#string(expr) abort
  return type(a:expr) ==# v:t_string ? a:expr : string(a:expr)
endfunction

function! deoplete#util#get_input(event) abort
  let mode = mode()
  if a:event ==# 'InsertEnter'
    let mode = 'i'
  endif
  let input = (mode ==# 'i' ? (col('.')-1) : col('.')) >= len(getline('.')) ?
        \      getline('.') :
        \      matchstr(getline('.'),
        \         '^.*\%' . (mode ==# 'i' ? col('.') : col('.') - 1)
        \         . 'c' . (mode ==# 'i' ? '' : '.'))

  if input =~# '^.\{-}\ze\S\+$'
    let complete_str = matchstr(input, '\S\+$')
    let input = matchstr(input, '^.\{-}\ze\S\+$')
  else
    let complete_str = ''
  endif

  if a:event ==# 'InsertCharPre'
    let complete_str .= v:char
  endif

  return input . complete_str
endfunction
function! deoplete#util#get_next_input(event) abort
  return getline('.')[len(deoplete#util#get_input(a:event)) :]
endfunction
function! deoplete#util#get_prev_event() abort
  return get(g:deoplete#_context, 'event', '')
endfunction

function! deoplete#util#vimoption2python(option) abort
  return '[a-zA-Z' . s:vimoption2python(a:option) . ']'
endfunction
function! deoplete#util#vimoption2python_not(option) abort
  return '[^a-zA-Z' . s:vimoption2python(a:option) . ']'
endfunction
function! s:vimoption2python(option) abort
  let has_dash = 0
  let patterns = []
  for pattern in split(a:option, ',')
    if pattern ==# ''
      " ,
      call add(patterns, ',')
    elseif pattern ==# '\'
      call add(patterns, '\\')
    elseif pattern ==# '-'
      let has_dash = 1
    elseif pattern =~# '\d\+'
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
endfunction

function! deoplete#util#uniq(list) abort
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
endfunction

function! deoplete#util#get_syn_names() abort
  if col('$') >= 200
    return []
  endif

  let names = []
  try
    " Note: synstack() seems broken in concealed text.
    for id in synstack(line('.'), (mode() ==# 'i' ? col('.')-1 : col('.')))
      let name = synIDattr(id, 'name')
      call add(names, name)
      if synIDattr(synIDtrans(id), 'name') !=# name
        call add(names, synIDattr(synIDtrans(id), 'name'))
      endif
    endfor
  catch
    " Ignore error
  endtry
  return names
endfunction

function! deoplete#util#neovim_version() abort
  redir => v
  silent version
  redir END
  return split(v, '\n')[0]
endfunction

function! deoplete#util#has_yarp() abort
  return !has('nvim') || deoplete#custom#_get_option('yarp')
endfunction

function! deoplete#util#get_context_filetype(input, event) abort
  if !exists('s:context_filetype')
    let s:context_filetype = {}

    " Force context_filetype call.
    try
      call context_filetype#get_filetype()
    catch
      " Ignore error
    endtry
  endif

  if empty(s:context_filetype)
        \ || s:context_filetype.prev_filetype !=# &filetype
        \ || s:context_filetype.line != line('.')
        \ || s:context_filetype.bufnr != bufnr('%')
        \ || (a:input =~# '\W$' &&
        \     substitute(a:input, '\s\zs\s\+$', '', '') !=#
        \     substitute(s:context_filetype.input, '\s\zs\s\+$', '', ''))
        \ || (a:input =~# '\w$' &&
        \     substitute(a:input, '\w\+$', '', '') !=#
        \     substitute(s:context_filetype.input, '\w\+$', '', ''))
        \ || a:event ==# 'InsertEnter'

    let s:context_filetype.line = line('.')
    let s:context_filetype.bufnr = bufnr('%')
    let s:context_filetype.input = a:input
    let s:context_filetype.prev_filetype = &filetype
    let s:context_filetype.filetype =
          \ (exists('*context_filetype#get_filetype') ?
          \   context_filetype#get_filetype() :
          \   (&filetype ==# '' ? 'nothing' : &filetype))
    let s:context_filetype.filetypes =
          \ exists('*context_filetype#get_filetypes') ?
          \   context_filetype#get_filetypes() :
          \   &filetype ==# '' ? ['nothing'] :
          \                     deoplete#util#uniq([&filetype]
          \                          + split(&filetype, '\.'))
    let s:context_filetype.same_filetypes =
          \ exists('*context_filetype#get_same_filetypes') ?
          \   context_filetype#get_same_filetypes() : []
  endif
  return [ s:context_filetype.filetype,
        \  s:context_filetype.filetypes, s:context_filetype.same_filetypes]
endfunction

function! deoplete#util#get_keyword_pattern(filetype, keyword_patterns) abort
  if empty(a:keyword_patterns)
    let patterns = deoplete#custom#_get_filetype_option(
        \   'keyword_patterns', a:filetype, '')
  else
    let filetype = has_key(a:keyword_patterns, a:filetype) ? a:filetype : '_'
    let patterns = get(a:keyword_patterns, filetype, '')
  endif
  let pattern = join(deoplete#util#convert2list(patterns), '|')

  " Convert keyword.
  let k_pattern = deoplete#util#vimoption2python(
        \ &l:iskeyword . (&l:lisp ? ',-' : ''))
  return substitute(pattern, '\\k', '\=k_pattern', 'g')
endfunction

function! deoplete#util#rpcnotify(event, context) abort
  if deoplete#init#_check_channel()
    return ''
  endif
  call s:notify(a:event, a:context)
  return ''
endfunction

function! s:notify(event, context) abort
  let a:context['rpc'] = a:event

  if deoplete#util#has_yarp()
    if g:deoplete#_yarp.job_is_dead
      return
    endif
    call g:deoplete#_yarp.notify(a:event, a:context)
  else
    call rpcnotify(g:deoplete#_channel_id, a:event, a:context)
  endif
endfunction

" Compare versions.  Return values is the distance between versions.  Each
" version integer (from right to left) is an ascending power of 100.
"
" Example:
" '0.1.10' is (1 * 100) + 10, or 110.
" '1.2.3' is (1 * 10000) + (2 * 100) + 3, or 10203.
"
" Returns:
" <0 if a < b
" >0 if a > b
" 0 if versions are equal.
function! deoplete#util#versioncmp(a, b) abort
  let a = map(split(a:a, '\.'), 'str2nr(v:val)')
  let b = map(split(a:b, '\.'), 'str2nr(v:val)')
  let l = min([len(a), len(b)])
  let d = 0

  " Only compare the parts that are common to both versions.
  for i in range(l)
    let d += (a[i] - b[i]) * pow(100, l - i - 1)
  endfor

  return d
endfunction

function! deoplete#util#split(string) abort
  return split(a:string, '\s*,\s*')
endfunction
