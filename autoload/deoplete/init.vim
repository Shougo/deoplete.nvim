"=============================================================================
" FILE: init.vim
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

if !exists('s:is_enabled')
  let s:is_enabled = 0
endif

let s:base_directory = escape(expand('<sfile>:p:h'), '\')

function! deoplete#init#enable() abort "{{{
  if deoplete#init#is_enabled()
    return
  endif

  if !has('nvim') || !has('python3')
    echomsg 'deoplete.nvim does not work with this version.'
    echomsg 'It requires neovim with Python3 support ("+python3").'
    return
  endif

  let s:is_enabled = 1

  call deoplete#handlers#init()

  " Python3 initialization
  python3 import sys
  python3 import deoplete.deoplete
  execute 'python3 deoplete = deoplete.deoplete.Deoplete("'
        \ . s:base_directory . '")'

  doautocmd <nomodeline> deoplete InsertEnter
endfunction"}}}

function! deoplete#init#is_enabled() abort "{{{
  return s:is_enabled
endfunction"}}}

" vim: foldmethod=marker
