"=============================================================================
" FILE: handler.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#handler#_init() abort "{{{
  augroup deoplete
    autocmd!
    autocmd InsertLeave * call s:on_insert_leave()
    autocmd CompleteDone * call s:complete_done()
    autocmd InsertCharPre * call s:on_insert_char_pre()

    autocmd TextChangedI * call s:completion_check('TextChangedI')
    autocmd InsertEnter * call s:completion_check('InsertEnter')
  augroup END

  for event in ['BufNewFile', 'BufNew', 'BufRead', 'BufWritePost']
    execute 'autocmd deoplete' event '* call s:on_event('.string(event).')'
  endfor

  call s:on_event('')
endfunction"}}}

function! s:completion_check(event) abort "{{{
  let delay = get(g:deoplete#_context, 'refresh', 0) ?
        \ g:deoplete#auto_refresh_delay : g:deoplete#auto_complete_delay
  if has('timers') && delay > 0
    if exists('s:timer')
      call timer_stop(s:timer.id)
    endif

    if a:event !=? 'Manual'
      let s:timer = { 'event': a:event, 'changedtick': b:changedtick }
      let s:timer.id = timer_start(delay, 's:completion_delayed')
      return
    endif
  endif

  return s:completion_begin(a:event)
endfunction"}}}

function! s:completion_delayed(timer) abort "{{{
  let timer = s:timer
  unlet! s:timer
  if b:changedtick == timer.changedtick
    call s:completion_begin(timer.event)
  endif
endfunction"}}}

function! s:completion_begin(event) abort "{{{
  let context = deoplete#init#_context(a:event, [])
  if s:is_skip(a:event, context)
    return
  endif

  " Save the previous position
  let g:deoplete#_context.position = context.position

  let g:deoplete#_context.refresh = 0

  " Call omni completion
  for filetype in context.filetypes
    for pattern in deoplete#util#convert2list(
          \ deoplete#util#get_buffer_config(filetype,
          \ 'b:deoplete_omni_patterns',
          \ 'g:deoplete#omni_patterns',
          \ 'g:deoplete#_omni_patterns'))
      if pattern !=# '' && &l:omnifunc !=# ''
            \ && context.input =~# '\%('.pattern.'\)$'
        call deoplete#mapping#_set_completeopt()
        call feedkeys("\<C-x>\<C-o>", 'n')
        return
      endif
    endfor
  endfor

  call deoplete#mapping#_set_completeopt()
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
        \ || mode() !=# 'i'
        \ || (a:event !=# 'Manual' && disable_auto_complete)
        \ || (&l:completefunc !=# '' && &l:buftype =~# 'nofile')
        \ || (a:event ==# 'InsertEnter'
        \     && has_key(g:deoplete#_context, 'position'))
    return 1
  endif

  if !get(g:deoplete#_context, 'refresh', 0)
        \ && a:context.position ==# get(g:deoplete#_context, 'position', [])
    let word = get(v:completed_item, 'word', '')
    let delimiters = filter(copy(g:deoplete#delimiters),
        \         'strridx(word, v:val) == (len(word) - len(v:val))')
    if word ==# '' || empty(delimiters)
      return 1
    endif
  endif

  return 0
endfunction"}}}
function! s:is_skip_textwidth(input) abort "{{{
  let displaywidth = strdisplaywidth(a:input) + 1

  if &l:formatoptions =~# '[tca]' && &l:textwidth > 0
        \     && displaywidth >= &l:textwidth
    if &l:formatoptions =~# '[ta]'
          \ || !empty(filter(deoplete#util#get_syn_names(),
          \                  'v:val ==# "Comment"'))
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
  if get(v:completed_item, 'word', '') !=# ''
    let word = v:completed_item.word
    if !has_key(g:deoplete#_rank, word)
      let g:deoplete#_rank[word] = 1
    else
      let g:deoplete#_rank[word] += 1
    endif
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
