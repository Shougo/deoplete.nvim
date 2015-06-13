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

function! deoplete#init#is_enabled() abort "{{{
  return s:is_enabled
endfunction"}}}

function! deoplete#init#enable() abort "{{{
  if deoplete#init#is_enabled()
    return
  endif

  if !has('nvim') || !has('python3')
    echomsg '[deoplete] deoplete.nvim does not work with this version.'
    echomsg '[deoplete] It requires Neovim with Python3 support ("+python3").'
    return
  endif

  if &completeopt !~# 'noinsert\|noselect'
    try
      set completeopt+=noinsert,noselect
    catch
      echomsg '[deoplete] deoplete.nvim does not work with this version.'
      echomsg '[deoplete] Please update neovim to latest version.'
      return
    endtry
  endif

  if !exists(':DeopleteInitializePython')
    UpdateRemotePlugins
    echomsg '[deoplete] Please restart Neovim.'
    return
  endif

  DeopleteInitializePython

  let s:is_enabled = 1

  call deoplete#init#_variables()
  call deoplete#handlers#_init()
  call deoplete#mappings#_init()
  call deoplete#echodoc#init()

  doautocmd <nomodeline> deoplete InsertEnter
endfunction"}}}

function! deoplete#init#_variables() abort "{{{
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_ignore_case', &ignorecase)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_smart_case', &ignorecase)
  call deoplete#util#set_default(
        \ 'g:deoplete#auto_completion_start_length', &ignorecase)
endfunction"}}}

function! deoplete#init#_context(event, sources) abort "{{{
  return {
        \ 'changedtick': b:changedtick,
        \ 'event': a:event,
        \ 'input': deoplete#helpers#get_input(a:event),
        \ 'complete_str':
        \   matchstr(deoplete#helpers#get_input(a:event), '\h\w*$'),
        \ 'position': getpos('.'),
        \ 'filetype': &filetype,
        \ 'ignorecase': g:deoplete#enable_ignore_case,
        \ 'smartcase': g:deoplete#enable_smart_case,
        \ 'sources': a:sources,
        \ }
endfunction"}}}

" vim: foldmethod=marker
