"=============================================================================
" FILE: util.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license  {{{
"     Permission is hereby granted, free of charge, to any person obtaining
"     a copy of this software and associated documentation files (the
"     "Software"), to deal in the Software without restriction, including
"     without limitation the rights to use, copy, modify, merge, publish,
"     distribute, sublicense, and/or sell copies of the Software, and to
"     permit persons to whom the Software is furnished to do so, subject to
"     the following conditions:
"
"     The above copyright notice and this permission notice shall be included
"     in all copies or substantial portions of the Software.
"
"     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
"     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
"     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
"     CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
"     TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
"     SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
" }}}
"=============================================================================

function! deoplete#util#set_default(var, val, ...)  "{{{
  if !exists(a:var) || type({a:var}) != type(a:val)
    let alternate_var = get(a:000, 0, '')

    let {a:var} = exists(alternate_var) ?
          \ {alternate_var} : a:val
  endif
endfunction"}}}
function! deoplete#util#set_pattern(variable, keys, pattern) "{{{
  for key in split(a:keys, '\s*,\s*')
    if !has_key(a:variable, key)
      let a:variable[key] = a:pattern
    endif
  endfor
endfunction"}}}
function! deoplete#util#get_buffer_config(
      \ filetype, buffer_var, user_var, default_var, ...) "{{{
  let default_val = get(a:000, 0, '')
  return exists(a:buffer_var) ? a:buffer_var :
        \ get(a:user_var, a:filetype,
        \   get(a:default_var, a:filetype, default_val))
endfunction"}}}
function! deoplete#util#get_default_buffer_config(
      \ filetype, buffer_var, user_var, default_var, ...) "{{{
  let default_val = get(a:000, 0, '')
  return exists(a:buffer_var) || has_key(a:user_var, a:filetype)?
        \ deoplete#util#get_buffer_config(
        \  a:filetype, a:buffer_var, a:user_var, a:default_var, default_val) :
        \ deoplete#util#get_buffer_config(
        \  '_', a:buffer_var, a:user_var, a:default_var, default_val)
endfunction"}}}
function! deoplete#util#get_simple_buffer_config(buffer_var, user_var) "{{{
  return exists(a:buffer_var) ? a:buffer_var : a:user_var
endfunction"}}}
function! deoplete#util#print_error(string) "{{{
  echohl Error | echomsg '[deoplete] ' . a:string | echohl None
endfunction"}}}
function! deoplete#util#print_warning(string) "{{{
  echohl WarningMsg | echomsg '[deoplete] ' . a:string | echohl None
endfunction"}}}

function! deoplete#util#convert2list(expr) "{{{
  return type(a:expr) ==# type([]) ? a:expr : [a:expr]
endfunction"}}}

" vim: foldmethod=marker
