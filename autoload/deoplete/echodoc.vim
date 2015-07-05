"=============================================================================
" FILE: echodoc.vim
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

" For echodoc. "{{{
let s:doc_dict = {
      \ 'name' : 'deoplete',
      \ 'rank' : 10,
      \ }
function! s:doc_dict.search(cur_text) "{{{
  let item = v:completed_item

  if empty(item) || type(item) != type({})
    return []
  endif

  let ret = []

  let abbr = (has_key(item, 'abbr') && item.word !=# item.abbr) ?
        \ item.abbr : get(split(item.info, '\n'), 0)
  if abbr == ''
    return []
  endif
  if has_key(item, 'abbr')
        \ && abbr ==# item.abbr && len(get(item, 'menu', '')) > 5
    " Combine menu.
    let abbr .= ' ' . item.menu
  endif

  " Skip
  if len(abbr) < len(item.word) + 2
    return []
  endif

  let match = stridx(abbr, item.word)
  if match < 0
    call add(ret, { 'text' : abbr })
  else
    call add(ret, { 'text' : item.word, 'highlight' : 'Identifier' })
    call add(ret, { 'text' : abbr[match+len(item.word) :] })
  endif

  return ret
endfunction"}}}
"}}}

function! deoplete#echodoc#init() "{{{
  if get(g:, 'loaded_echodoc')
    call echodoc#register(s:doc_dict.name, s:doc_dict)
  endif
endfunction"}}}

" vim: foldmethod=marker
