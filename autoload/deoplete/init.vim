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
    call deoplete#util#print_error(
          \ 'deoplete.nvim does not work with this version.')
    call deoplete#util#print_error(
          \ 'It requires Neovim with Python3 support("+python3").')
    return
  endif

  if &completeopt !~# 'noinsert\|noselect'
    let save_completeopt = &completeopt
    try
      set completeopt+=noselect
    catch
      call deoplete#util#print_error(
            \ 'deoplete.nvim does not work with this version.')
      call deoplete#util#print_error(
            \ 'Please update neovim to latest version.')
      return
    finally
      let &completeopt = save_completeopt
    endtry
  endif

  if !exists(':DeopleteInitializePython')
    call deoplete#util#print_error(
          \ 'deoplete.nvim is not registered as Neovim remote plugins.')
    call deoplete#util#print_error(
          \ 'Please execute :UpdateRemotePlugins command and restart Neovim.')
    return
  endif

  DeopleteInitializePython

  let s:is_enabled = 1

  call deoplete#init#_variables()
  call deoplete#handlers#_init()
  call deoplete#mappings#_init()
endfunction"}}}

function! deoplete#init#_variables() abort "{{{
  let g:deoplete#_context = {}

  " User vairables
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_ignore_case', &ignorecase)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_smart_case', &smartcase)
  call deoplete#util#set_default(
        \ 'g:deoplete#auto_completion_start_length', 2)
  call deoplete#util#set_default(
        \ 'g:deoplete#disable_auto_complete', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#delimiters', ['/', '.', '::', ':', '#'])

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

  " Source variables
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#input_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#_input_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#functions', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#_functions', { '_': '' })
  call deoplete#util#set_default(
        \ 'g:deoplete#member#prefix_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#member#_prefix_patterns', {})

  " Initialize default keyword pattern. "{{{
  call deoplete#util#set_pattern(
        \ g:deoplete#_keyword_patterns,
        \ '_',
        \ '[a-zA-Z_]\k*')
  "}}}

  " Initialize omni completion pattern. "{{{
  " Note: HTML omni func use search().
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'html,xhtml,xml,markdown,mkd', ['<', '<[^>]*\s[[:alnum:]-]*'])

  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'c', ['[^. \t0-9]\.\w*', '[^. \t0-9]->\w*'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'cpp', ['[^. \t0-9]\.\w*', '[^. \t0-9]->\w*',
        \         '[a-zA-Z_]\w*::\w*'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'go,java', ['[^. \t0-9]\.\w*'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'javascript,typescript', ['[^. \t0-9]\.([a-zA-Z_]\w*)?'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'css,scss,sass', ['^\s+\w+', '\w+[):;]?\s+\w*', '[@!]'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'python', ['[^. \t0-9]\.\w*', '^\s*@\w*',
        \            '^\s*from\s.+import \w*', '^\s*from \w*',
        \            '^\s*import \w*'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'ruby', ['[^. \t0-9]\.\w*', '[a-zA-Z_]\w*::\w*'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'lua', ['\w+[.:]', 'require\s*\(?["'']\w*'])
  "}}}

  " Initialize member prefix pattern. "{{{
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ '_', '\.')
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'c,objc', ['\.', '->'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'cpp,objcpp', ['\.', '->', '::'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'perl,php', ['->'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'ruby', ['\.', '::'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'lua', ['\.', ':'])
  "}}}
endfunction"}}}

function! deoplete#init#_context(event, sources) abort "{{{
  let filetype = (exists('*context_filetype#get_filetype') ?
        \   context_filetype#get_filetype() :
        \   (&filetype == '' ? 'nothing' : &filetype))
  let filetypes = exists('*context_filetype#get_filetypes') ?
        \   context_filetype#get_filetypes() :
        \   &filetype == '' ? ['nothing'] :
        \                     deoplete#util#uniq([&filetype]
        \                          + split(&filetype, '\.'))

  let sources = a:sources
  if a:event !=# 'Manual' && empty(sources)
    " Use default sources
    let sources = deoplete#util#get_buffer_config(
          \ filetype,
          \ 'b:deoplete_sources',
          \ 'g:deoplete#sources',
          \ '{}', [])
  endif

  let keyword_patterns = join(deoplete#util#convert2list(
        \   deoplete#util#get_buffer_config(
        \   filetype, 'b:deoplete_keyword_patterns',
        \   'g:deoplete#keyword_patterns',
        \   'g:deoplete#_keyword_patterns')), '|')

  " Convert keyword pattern.
  let pattern = deoplete#util#vimoption2python(
        \ &l:iskeyword . (&l:lisp ? ',-' : ''))
  let keyword_patterns = substitute(keyword_patterns,
        \ '\\k', '\=pattern', 'g')

  return {
        \ 'changedtick': b:changedtick,
        \ 'event': a:event,
        \ 'input': deoplete#util#get_input(a:event),
        \ 'next_input': deoplete#util#get_next_input(a:event),
        \ 'complete_str': '',
        \ 'position': getpos('.'),
        \ 'filetype': filetype,
        \ 'filetypes': filetypes,
        \ 'ignorecase': g:deoplete#enable_ignore_case,
        \ 'smartcase': g:deoplete#enable_smart_case,
        \ 'sources': sources,
        \ 'keyword_patterns': keyword_patterns,
        \ }
endfunction"}}}

" vim: foldmethod=marker
