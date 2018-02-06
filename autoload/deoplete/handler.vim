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
    autocmd InsertLeave * call s:completion_timer_stop()
  augroup END

  for event in ['BufNewFile', 'BufRead', 'BufWritePost', 'VimLeavePre']
    call s:define_on_event(event)
  endfor

  if exists('##DirChanged')
    call s:define_on_event('DirChanged')
  endif

  if g:deoplete#enable_on_insert_enter
    autocmd deoplete InsertEnter *
          \ call s:completion_begin('InsertEnter')
  endif
  if g:deoplete#enable_refresh_always
    autocmd deoplete InsertCharPre *
          \ call s:completion_begin('InsertCharPre')
  endif

  " Note: Vim 8 GUI is broken
  " dummy timer call is needed before complete()
  if !has('nvim') && has('gui_running')
    let s:dummy_timer = timer_start(200, {timer -> 0}, {'repeat': -1})
  endif
endfunction

function! s:do_complete(timer) abort
  let context = g:deoplete#_context
  let event = get(context, 'event', '')
  let modes = (event ==# 'InsertEnter') ? ['n', 'i'] : ['i']
  if s:is_exiting() || index(modes, mode()) < 0
    call s:completion_timer_stop()
    return
  endif

  if empty(get(context, 'candidates', []))
        \ || deoplete#util#get_input(context.event) !=# context.input
    return
  endif

  let prev = g:deoplete#_prev_completion
  if context.event !=# 'Manual'
        \ && prev.complete_position == getpos('.')
        \ && prev.candidates ==# context.candidates
    return
  endif

  let prev.event = context.event
  let prev.candidates = context.candidates
  let prev.complete_position = getpos('.')

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

function! deoplete#handler#_completion_timer_start() abort
  if exists('s:completion_timer')
    call s:completion_timer_stop()
  endif

  let delay = max([20, g:deoplete#auto_complete_delay])
  let s:completion_timer = timer_start(delay, function('s:do_complete'))
endfunction
function! s:completion_timer_stop() abort
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
        \ max([20, g:deoplete#auto_refresh_delay]),
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

  if g:deoplete#_prev_completion.event !=# 'Manual'
    " Call omni completion
    for filetype in context.filetypes
      for pattern in deoplete#util#convert2list(
            \ deoplete#util#get_buffer_config(filetype,
            \ 'b:deoplete_omni_patterns',
            \ 'g:deoplete#omni_patterns',
            \ 'g:deoplete#_omni_patterns'))
        let blacklist = ['LanguageClient#complete']
        if pattern !=# '' && &l:omnifunc !=# ''
              \ && context.input =~# '\%('.pattern.'\)$'
              \ && index(blacklist, &l:omnifunc) < 0
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

function! s:define_on_event(event) abort
  execute 'autocmd deoplete' a:event
        \ '* call deoplete#util#rpcnotify("deoplete_on_event",'
        \.'deoplete#init#_context('.string(a:event).', []))'
endfunction

function! s:on_insert_leave() abort
  call deoplete#mapping#_restore_completeopt()
  let g:deoplete#_context = {}
  let g:deoplete#_prev_completion = {
        \ 'complete_position': [],
        \ 'candidates': [],
        \ 'event': '',
        \ }
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
