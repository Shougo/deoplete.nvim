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
    autocmd InsertLeave * call s:completion_timer_stop()
  augroup END

  for event in ['InsertEnter', 'BufWritePost', 'DirChanged']
    call s:define_on_event(event)
  endfor

  call s:define_completion_via_timer('TextChangedI')
  if deoplete#custom#_get_option('on_insert_enter')
    call s:define_completion_via_timer('InsertEnter')
  endif
  if deoplete#custom#_get_option('refresh_always')
    call s:define_completion_via_timer('InsertCharPre')
  endif

  " Note: Vim 8 GUI(MacVim and Win32) is broken
  " dummy timer call is needed before complete()
  if !has('nvim') && has('gui_running')
        \ && (has('gui_macvim') || has('win32') || has('win64'))
    let s:dummy_timer = timer_start(200, {timer -> 0}, {'repeat': -1})
  endif

  if deoplete#util#has_yarp()
    " To fix "RuntimeError: Event loop is closed" issue
    " Note: Workaround
    autocmd deoplete VimLeavePre * call s:kill_yarp()
  endif
endfunction

function! deoplete#handler#_do_complete() abort
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
  let prev.event = context.event
  let prev.candidates = context.candidates
  let prev.complete_position = getpos('.')

  if context.event ==# 'Manual'
    let context.event = ''
  elseif !exists('g:deoplete#_saved_completeopt')
    call deoplete#mapping#_set_completeopt()
  endif

  let complete_method = deoplete#custom#_get_option('complete_method')
  if complete_method ==# 'complete'
    call feedkeys("\<Plug>_", 'i')
  elseif complete_method ==# 'completefunc'
    let &l:completefunc = 'deoplete#mapping#_completefunc'
    call feedkeys("\<C-x>\<C-u>", 'in')
  elseif complete_method ==# 'omnifunc'
    let &l:omnifunc = 'deoplete#mapping#_completefunc'
    call feedkeys("\<C-x>\<C-o>", 'in')
  endif
endfunction

function! s:completion_timer_start(event) abort
  if exists('s:completion_timer')
    call s:completion_timer_stop()
  endif

  let delay = max([20, deoplete#custom#_get_option('auto_complete_delay')])
  let s:completion_timer = timer_start(
        \ delay, {-> s:completion_begin(a:event)})
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

  let delay = deoplete#custom#_get_option('auto_refresh_delay')
  if delay <= 0
    return
  endif

  let s:async_timer = { 'event': 'Async', 'changedtick': b:changedtick }
  let s:async_timer.id = timer_start(
        \ max([20, delay]),
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
  if s:is_skip(a:event)
    call deoplete#mapping#_restore_completeopt()
    let g:deoplete#_context.candidates = []
    return
  endif

  let context = deoplete#init#_context(a:event, [])
  if s:check_omnifunc(context)
    return
  endif

  call deoplete#util#rpcnotify(
        \ 'deoplete_auto_completion_begin', context)
endfunction
function! s:is_skip(event) abort
  if s:is_skip_text(a:event)
    return 1
  endif

  let auto_complete = deoplete#custom#_get_option('auto_complete')

  if &paste
        \ || (a:event !=# 'Manual' && a:event !=# 'Async' && !auto_complete)
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

  let skip_chars = deoplete#custom#_get_option('skip_chars')

  return (!pumvisible() && virtcol('.') != displaywidth)
        \ || (a:event !=# 'Manual' && input !=# ''
        \     && index(skip_chars, input[-1:]) >= 0)
endfunction
function! s:check_omnifunc(context) abort
  let prev = g:deoplete#_prev_completion
  let blacklist = ['LanguageClient#complete']
  if prev.event ==# 'Manual'
        \ || &l:omnifunc ==# ''
        \ || index(blacklist, &l:omnifunc) >= 0
        \ || prev.complete_position ==# getpos('.')
    return
  endif

  for filetype in a:context.filetypes
    for pattern in deoplete#util#convert2list(
          \ deoplete#custom#_get_filetype_option(
          \   'omni_patterns', filetype, ''))
      if pattern !=# '' && a:context.input =~# '\%('.pattern.'\)$'
        let g:deoplete#_context.candidates = []

        let prev.event = a:context.event
        let prev.candidates = []
        let prev.complete_position = getpos('.')

        call deoplete#mapping#_set_completeopt()
        call feedkeys("\<C-x>\<C-o>", 'in')
        return 1
      endif
    endfor
  endfor
endfunction

function! s:define_on_event(event) abort
  if !exists('##' . a:event)
    return
  endif

  execute 'autocmd deoplete' a:event
        \ '* call deoplete#send_event('.string(a:event).')'
endfunction
function! s:define_completion_via_timer(event) abort
  if !exists('##' . a:event)
    return
  endif

  execute 'autocmd deoplete' a:event
        \ '* call s:completion_timer_start('.string(a:event).')'
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
  if get(v:completed_item, 'word', '') ==# ''
    return
  endif

  let word = v:completed_item.word
  if !has_key(g:deoplete#_rank, word)
    let g:deoplete#_rank[word] = 1
  else
    let g:deoplete#_rank[word] += 1
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

function! s:kill_yarp() abort
  if g:deoplete#_yarp.job_is_dead
    return
  endif

  let job = g:deoplete#_yarp.job
  if !has('nvim') && !exists('g:yarp_jobstart')
    " Get job object from vim-hug-neovim-rpc
    let job = g:_neovim_rpc_jobs[job].job
  endif

  if has('nvim')
    call jobstop(job)
  else
    call job_stop(job, 'kill')
  endif

  let g:deoplete#_yarp.job_is_dead = 1
endfunction
