"=============================================================================
" FILE: handler.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#handler#_init() abort
  augroup deoplete
    autocmd!
    autocmd InsertLeave * call s:on_insert_leave()
    autocmd CompleteDone * call s:on_complete_done()
    autocmd TextChangedI * call s:completion_begin('TextChangedI')
    autocmd InsertEnter *
          \ call s:completion_begin('InsertEnter') | call s:timer_begin()
    autocmd InsertLeave * call s:timer_end()
  augroup END

  for event in ['BufNewFile', 'BufRead', 'BufWritePost', 'VimLeavePre']
    execute 'autocmd deoplete' event '* call s:on_event('.string(event).')'
  endfor

  if g:deoplete#enable_refresh_always
    autocmd deoplete InsertCharPre * call s:completion_begin('InsertCharPre')
  endif

  call s:timer_begin()
endfunction

function! s:do_complete(timer) abort
  let context = g:deoplete#_context
  if s:is_exiting()
        \ || (get(context, 'event', '') !=# 'InsertEnter' && mode() !=# 'i')
    call s:timer_end()
    return
  endif

  if empty(get(context, 'candidates', []))
        \ || deoplete#util#get_input(context.event) !=# context.input
    return
  endif

  if context.event !=# 'Manual'
        \ && s:prev_completion.complete_position == getpos('.')
        \ && s:prev_completion.candidates ==# context.candidates
    return
  endif

  let s:prev_completion.event = context.event
  let s:prev_completion.candidates = context.candidates
  let s:prev_completion.complete_position = getpos('.')

  if context.event ==# 'Manual'
    let context.event = ''
  elseif !exists('g:deoplete#_saved_completeopt')
    call deoplete#mapping#_set_completeopt()
  endif

  if g:deoplete#complete_method ==# 'complete'
    call feedkeys("\<Plug>_", 'i')
  elseif g:deoplete#complete_method ==# 'completefunc'
    let &l:completefunc = 'deoplete#mapping#_completefunc'
    call feedkeys("\<C-x>\<C-u>", 'in')
  elseif g:deoplete#complete_method ==# 'omnifunc'
    let &l:omnifunc = 'deoplete#mapping#_completefunc'
    call feedkeys("\<C-x>\<C-o>", 'in')
  endif
endfunction

function! s:timer_begin() abort
  if exists('s:completion_timer')
    return
  endif

  let delay = max([50, g:deoplete#auto_complete_delay])
  let s:completion_timer = timer_start(delay,
            \ function('s:do_complete'), {'repeat': -1})

  let s:prev_completion = {
        \ 'complete_position': [], 'candidates': [], 'event': ''
        \ }
endfunction
function! s:timer_end() abort
  if !exists('s:completion_timer')
    return
  endif

  call timer_stop(s:completion_timer)
  unlet s:completion_timer
endfunction

function! deoplete#handler#_async_timer_start() abort
  if exists('s:async_timer')
    call deoplete#handler#_async_timer_stop()
  endif

  let s:async_timer = { 'event': 'Async', 'changedtick': b:changedtick }
  let s:async_timer.id = timer_start(
        \ max([50, g:deoplete#auto_refresh_delay]),
        \ function('s:completion_async'), {'repeat': -1})
endfunction
function! deoplete#handler#_async_timer_stop() abort
  if exists('s:async_timer')
    call timer_stop(s:async_timer.id)
    unlet s:async_timer
  endif
endfunction
function! s:completion_async(timer) abort
  if mode() !=# 'i' || s:is_exiting()
    call deoplete#handler#_async_timer_stop()
    return
  endif

  call s:completion_begin(s:async_timer.event)
endfunction

function! s:completion_begin(event) abort
  let context = deoplete#init#_context(a:event, [])
  if s:is_skip(a:event, context)
    call deoplete#mapping#_restore_completeopt()
    let g:deoplete#_context.candidates = []
    return
  endif

  if exists('s:prev_completion') && s:prev_completion.event !=# 'Manual'
    " Call omni completion
    for filetype in context.filetypes
      for pattern in deoplete#util#convert2list(
            \ deoplete#util#get_buffer_config(filetype,
            \ 'b:deoplete_omni_patterns',
            \ 'g:deoplete#omni_patterns',
            \ 'g:deoplete#_omni_patterns'))
        if pattern !=# '' && &l:omnifunc !=# ''
              \ && context.input =~# '\%('.pattern.'\)$'
          let g:deoplete#_context.candidates = []
          call deoplete#mapping#_set_completeopt()
          call feedkeys("\<C-x>\<C-o>", 'in')
          return
        endif
      endfor
    endfor
  endif

  call deoplete#util#rpcnotify(
        \ 'deoplete_auto_completion_begin', context)
endfunction
function! s:is_skip(event, context) abort
  if s:is_skip_text(a:event)
    return 1
  endif

  let disable_auto_complete =
        \ deoplete#util#get_simple_buffer_config(
        \   'b:deoplete_disable_auto_complete',
        \   'g:deoplete#disable_auto_complete')

  if &paste
        \ || (a:event !=# 'Manual' && disable_auto_complete)
        \ || (&l:completefunc !=# '' && &l:buftype =~# 'nofile')
        \ || (a:event !=# 'InsertEnter' && mode() !=# 'i')
    return 1
  endif

  return 0
endfunction
function! s:is_skip_text(event) abort
  let context = g:deoplete#_context
  let input = deoplete#util#get_input(a:event)

  if has_key(context, 'input')
        \ && a:event !=# 'Manual'
        \ && a:event !=# 'Async'
        \ && input ==# context.input
    return 1
  endif

  let displaywidth = strdisplaywidth(input) + 1
  if &l:formatoptions =~# '[tca]' && &l:textwidth > 0
        \     && displaywidth >= &l:textwidth
    if &l:formatoptions =~# '[ta]'
          \ || !empty(filter(deoplete#util#get_syn_names(),
          \                  "v:val ==# 'Comment'"))
      return 1
    endif
  endif

  let skip_chars = deoplete#util#get_simple_buffer_config(
        \   'b:deoplete_skip_chars', 'g:deoplete#skip_chars')

  return (!pumvisible() && virtcol('.') != displaywidth)
        \ || (a:event !=# 'Manual' && input !=# ''
        \     && index(skip_chars, input[-1:]) >= 0)
endfunction

function! s:on_event(event) abort
  call deoplete#util#rpcnotify('deoplete_on_event',
        \ deoplete#init#_context(a:event, []))
endfunction

function! s:on_insert_leave() abort
  call deoplete#mapping#_restore_completeopt()
  let g:deoplete#_context = {}
endfunction

function! s:on_complete_done() abort
  if get(v:completed_item, 'word', '') !=# ''
    let word = v:completed_item.word
    if !has_key(g:deoplete#_rank, word)
      let g:deoplete#_rank[word] = 1
    else
      let g:deoplete#_rank[word] += 1
    endif
  endif

  if !g:deoplete#enable_refresh_always
    call deoplete#handler#_skip_next_completion()
  endif
endfunction

function! deoplete#handler#_skip_next_completion() abort
  if !exists('g:deoplete#_context')
    return
  endif

  let input = deoplete#util#get_input('CompleteDone')
  if input[-1:] !=# '/'
    let g:deoplete#_context.input = input
  endif
endfunction

function! s:is_exiting() abort
  return exists('v:exiting') && v:exiting != v:null
endfunction
