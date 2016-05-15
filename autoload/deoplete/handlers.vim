"=============================================================================
" FILE: handlers.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#handlers#_init() abort "{{{
  augroup deoplete
    autocmd!
    autocmd InsertLeave * call s:on_insert_leave()
    autocmd CompleteDone * call s:complete_done()
    autocmd InsertCharPre * call s:on_insert_char_pre()

    autocmd TextChangedI * call s:completion_begin("TextChangedI")
    autocmd InsertEnter * call s:completion_begin("InsertEnter")
  augroup END

  for event in [
        \ 'BufEnter', 'BufRead', 'BufNewFile', 'BufNew', 'BufWinEnter',
        \ 'BufWritePost'
        \ ]
    execute 'autocmd deoplete' event '* call s:on_event('.string(event).')'
  endfor
endfunction"}}}

function! s:completion_begin(event) abort "{{{
  let context = deoplete#init#_context(a:event, [])

  if s:is_skip(a:event, context)
    return
  endif

  " Save the previous position
  let g:deoplete#_context.position = context.position

  " Call omni completion
  for filetype in context.filetypes
    for pattern in deoplete#util#convert2list(
          \ deoplete#util#get_buffer_config(filetype,
          \ 'b:deoplete_omni_patterns',
          \ 'g:deoplete#omni_patterns',
          \ 'g:deoplete#_omni_patterns'))
      if pattern != '' && &l:omnifunc != ''
            \ && context.input =~# '\%('.pattern.'\)$'
        call deoplete#mappings#_set_completeopt()
        call feedkeys("\<C-x>\<C-o>", 'n')
        return
      endif
    endfor
  endfor

  call rpcnotify(g:deoplete#_channel_id,
        \ 'deoplete_auto_completion_begin', context)
endfunction"}}}
function! s:is_skip(event, context) abort "{{{
  if s:is_skip_textwidth(deoplete#util#get_input(a:event))
    return 1
  endif

  let disable_auto_complete =
        \ deoplete#util#get_simple_buffer_config(
        \   'b:deoplete_disable_auto_complete',
        \   'g:deoplete#disable_auto_complete')

  if &paste
        \ || (a:event !=# 'Manual' && disable_auto_complete)
        \ || (&l:completefunc != '' && &l:buftype =~# 'nofile')
        \ || (a:event ==# 'InsertEnter'
        \     && has_key(g:deoplete#_context, 'position'))
    return 1
  endif

  if a:context.position ==# get(g:deoplete#_context, 'position', [])
    let word = get(v:completed_item, 'word', '')
    let delimiters = filter(copy(g:deoplete#delimiters),
        \         'strridx(word, v:val) == (len(word) - len(v:val))')
    if word == '' || empty(delimiters)
      return 1
    endif
  endif

  " Detect foldmethod.
  if a:event !=# 'Manual' && a:event !=# 'InsertEnter'
        \ && !exists('b:deoplete_detected_foldmethod')
        \ && (&l:foldmethod ==# 'expr' || &l:foldmethod ==# 'syntax')
    let b:deoplete_detected_foldmethod = 1
    call deoplete#util#print_error(
          \ printf('foldmethod = "%s" is detected.', &foldmethod))
    for msg in split(deoplete#util#redir(
          \ 'verbose setlocal foldmethod?'), "\n")
      call deoplete#util#print_error(msg)
    endfor
    call deoplete#util#print_error(
          \ 'You should disable it or install FastFold plugin.')
  endif

  return 0
endfunction"}}}
function! s:is_skip_textwidth(input) abort "{{{
  let displaywidth = strdisplaywidth(a:input) + 1

  if &l:formatoptions =~# '[tca]' && &l:textwidth > 0
        \     && displaywidth >= &l:textwidth
    if &l:formatoptions =~# '[ta]'
          \ || deoplete#util#get_syn_name() ==# 'Comment'
      return 1
    endif
  endif
  return !pumvisible() && virtcol('.') != displaywidth
endfunction"}}}

function! s:on_event(event) abort "{{{
  let context = deoplete#init#_context(a:event, [])
  call rpcnotify(g:deoplete#_channel_id, 'deoplete_on_event', context)
endfunction"}}}

function! s:on_insert_leave() abort "{{{
  if exists('g:deoplete#_saved_completeopt')
    let &completeopt = g:deoplete#_saved_completeopt
    unlet g:deoplete#_saved_completeopt
  endif
  let g:deoplete#_context = {}
endfunction"}}}

function! s:complete_done() abort "{{{
  if get(v:completed_item, 'word', '') != ''
    let word = v:completed_item.word
    if !has_key(g:deoplete#_rank, word)
      let g:deoplete#_rank[word] = 1
    else
      let g:deoplete#_rank[word] += 1
    endif
  endif

  if get(g:deoplete#_context, 'refresh', 0)
    " Don't skip completion
    let g:deoplete#_context.refresh = 0
    if deoplete#util#get_prev_event() ==# 'Manual'
      let g:deoplete#_context.event = 'refresh'
    endif
    return
  endif

  let g:deoplete#_context.position = getpos('.')
endfunction"}}}

function! s:on_insert_char_pre() abort "{{{
  if !pumvisible()
        \ || !g:deoplete#enable_refresh_always
        \ || s:is_skip_textwidth(deoplete#util#get_input('InsertCharPre'))
    return 1
  endif

  " Auto refresh
  call feedkeys("\<Plug>(deoplete_auto_refresh)")
endfunction"}}}

" vim: foldmethod=marker
