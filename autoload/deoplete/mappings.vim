"=============================================================================
" FILE: mappings.vim
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

function! deoplete#mappings#_init() abort "{{{
  inoremap <silent> <Plug>(deoplete_start_complete)
        \ <C-r>=deoplete#mappings#_do_complete(g:deoplete#_context)<CR>
endfunction"}}}

function! deoplete#mappings#_do_complete(context) abort "{{{
  " Deoplete does not work if completeopt contains longest and menu options
  set completeopt-=longest
  set completeopt+=menuone
  if &completeopt !~# 'noinsert\|noselect'
    set completeopt+=noselect
  endif

  if b:changedtick == get(a:context, 'changedtick', -1)
    " Unescape is needed for the candidates.
    for candidate in a:context.candidates
      call map(filter(candidate,
            \ 'type(v:val) == type("")'), "substitute(v:val,
            \ '\\\\\\\\', '\\\\', 'g')")
    endfor
    call complete(a:context.complete_position + 1, a:context.candidates)
  endif
  return ''
endfunction"}}}

function! deoplete#mappings#manual_complete(...) abort "{{{
  " Start complete.
  return "\<C-o>:call rpcnotify(g:deoplete#_channel_id, 'completion_begin',
        \  deoplete#init#_context(
        \    'Manual'," . string(get(a:000, 0, [])) . "))\<CR>"
endfunction"}}}

function! deoplete#mappings#close_popup() "{{{
  let g:deoplete#_context.position = getpos('.')
  return pumvisible() ? "\<C-y>" : ''
endfunction
"}}}
function! deoplete#mappings#smart_close_popup() "{{{
  let g:deoplete#_context.position = getpos('.')
  return pumvisible() ? "\<C-e>" : ''
endfunction
"}}}
function! deoplete#mappings#cancel_popup() "{{{
  let g:deoplete#_context.position = getpos('.')
  return pumvisible() ? "\<C-e>" : ''
endfunction
"}}}

" vim: foldmethod=marker
