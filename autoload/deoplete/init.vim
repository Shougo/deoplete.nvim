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

  augroup deoplete
    autocmd!
  augroup END

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
  " User vairables
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_ignore_case', &ignorecase)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_smart_case', &ignorecase)
  call deoplete#util#set_default(
        \ 'g:deoplete#auto_completion_start_length', 2)
  call deoplete#util#set_default(
        \ 'g:deoplete#disable_auto_complete', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#keyword_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#_keyword_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#_omni_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#sources', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#ignore_sources', {})

  " Internal vairables
  call deoplete#util#set_default(
        \ 'g:deoplete#_skip_next_complete', 0)

  " Initialize default keyword pattern. "{{{
  call deoplete#util#set_pattern(
        \ g:deoplete#_keyword_patterns,
        \ '_',
        \ '[a-zA-Z_]\w*')
  "}}}

  " Initialize omni completion pattern. "{{{
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'html,xhtml,xml,markdown,mkd',
        \ '<[^>]*')
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'css,scss,sass',
        \ ['^\s+\w+', '\w+[):;]?\s+\w*|[@!]'])
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'javascript',
        \ '[^. \t]\.([a-zA-Z_]\w*)?')
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'python', '[^. \t]\.\w*')
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'ruby', ['[^. \t]\.\w*', '[a-zA-Z_]\w*::\w*'])
  "}}}
endfunction"}}}

function! deoplete#init#_context(event, sources) abort "{{{
  let filetype = (exists('*context_filetype#get_filetype') ?
        \   context_filetype#get_filetype() : &filetype)
  if filetype == ''
    let filetype = 'nothing'
  endif
  let sources = a:sources
  if a:event !=# 'Manual' && empty(sources)
    " Use default sources
    let sources = s:get_sources(filetype)
  endif

  let keyword_patterns = join(deoplete#util#convert2list(
        \   deoplete#util#get_default_buffer_config(
        \   filetype, 'b:deoplete_keyword_patterns',
        \   g:deoplete#keyword_patterns, g:deoplete#_keyword_patterns)), '|')

  return {
        \ 'changedtick': b:changedtick,
        \ 'event': a:event,
        \ 'input': deoplete#helpers#get_input(a:event),
        \ 'complete_str': '',
        \ 'position': getpos('.'),
        \ 'filetype': filetype,
        \ 'ignorecase': g:deoplete#enable_ignore_case,
        \ 'smartcase': g:deoplete#enable_smart_case,
        \ 'sources': sources,
        \ 'keyword_patterns': keyword_patterns,
        \ }
endfunction"}}}

function! s:get_sources(filetype) abort "{{{
  let sources = deoplete#util#get_default_buffer_config(a:filetype,
        \ 'b:deoplete_sources', g:deoplete#sources, {}, [])
  let ignore_sources = deoplete#util#get_default_buffer_config(a:filetype,
        \ 'b:deoplete_ignore_sources', g:deoplete#ignore_sources, {}, [])

  " Ignore sources
  return filter(sources, "index(ignore_sources, v:val) < 0")
endfunction"}}}

" vim: foldmethod=marker
