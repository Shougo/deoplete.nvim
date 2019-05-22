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
  augroup END

  for event in [
        \ 'InsertEnter', 'BufReadPost', 'BufWritePost', 'VimLeavePre',
        \ ]
    call s:define_on_event(event)
  endfor

  if deoplete#custom#_get_option('on_text_changed_i')
    call s:define_completion_via_timer('TextChangedI')
  endif
  if deoplete#custom#_get_option('on_insert_enter')
    call s:define_completion_via_timer('InsertEnter')
  endif
  if deoplete#custom#_get_option('refresh_always')
    if exists('##TextChangedP')
      call s:define_completion_via_timer('TextChangedP')
    else
      call s:define_completion_via_timer('InsertCharPre')
    endif
  endif

  " Note: Vim 8 GUI(MacVim and Win32) is broken
  " dummy timer call is needed before complete()
  if !has('nvim') && has('gui_running')
        \ && (has('gui_macvim') || has('win32'))
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
    return
  endif

  if empty(get(context, 'candidates', []))
        \ || deoplete#util#get_input(context.event) !=# context.input
    return
  endif

  let prev = g:deoplete#_prev_completion
  let prev.event = context.event
  let prev.input = context.input
  let prev.candidates = context.candidates
  let prev.complete_position = context.complete_position
  let prev.linenr = line('.')

  if context.event ==# 'Manual'
    let context.event = ''
  elseif !exists('g:deoplete#_saved_completeopt')
    call deoplete#mapping#_set_completeopt()
  endif

  call feedkeys("\<Plug>_", 'i')
endfunction

function! deoplete#handler#_check_omnifunc(context) abort
  let prev = g:deoplete#_prev_completion
  let blacklist = ['LanguageClient#complete']
  if a:context.event ==# 'Manual'
        \ || &l:omnifunc ==# ''
        \ || index(blacklist, &l:omnifunc) >= 0
        \ || prev.input ==# a:context.input
    return
  endif

  for filetype in a:context.filetypes
    for pattern in deoplete#util#convert2list(
          \ deoplete#custom#_get_filetype_option(
          \   'omni_patterns', filetype, ''))
      if pattern !=# '' && a:context.input =~# '\%('.pattern.'\)$'
        let g:deoplete#_context.candidates = []

        let prev.event = a:context.event
        let prev.input = a:context.input
        let prev.candidates = []

        call deoplete#mapping#_set_completeopt()
        call feedkeys("\<C-x>\<C-o>", 'in')
        return 1
      endif
    endfor
  endfor
endfunction

function! s:completion_timer_start(event) abort
  if exists('s:completion_timer')
    call s:completion_timer_stop()
  endif

  let delay = deoplete#custom#_get_option('auto_complete_delay')
  if delay > 0
    let s:completion_timer = timer_start(
          \ delay, {-> deoplete#handler#_completion_begin(a:event)})
  else
    call deoplete#handler#_completion_begin(a:event)
  endif
endfunction
function! s:completion_timer_stop() abort
  if !exists('s:completion_timer')
    return
  endif

  call timer_stop(s:completion_timer)
  unlet s:completion_timer
endfunction

function! s:check_prev_completion(event) abort
  let prev = g:deoplete#_prev_completion
  if a:event ==# 'Async' || mode() !=# 'i'
        \ || empty(get(prev, 'candidates', []))
    return
  endif

  let input = deoplete#util#get_input(a:event)
  let complete_str = matchstr(input, '\w\+$')
  let min_pattern_length = deoplete#custom#_get_option('min_pattern_length')
  if prev.linenr != line('.') || len(complete_str) < min_pattern_length
    return
  endif

  call deoplete#mapping#_set_completeopt()

  let mode = deoplete#custom#_get_option('prev_completion_mode')
  let candidates = copy(prev.candidates)

  if mode ==# 'filter' || mode ==# 'length'
    let input = input[prev.complete_position :]
    let escaped_input = escape(input, '~\.^$[]*')
    let pattern = substitute(escaped_input, '\w', '\\w*\0', 'g')
    call filter(candidates, 'v:val.word =~? pattern')
    if mode ==# 'length'
      call filter(candidates, 'len(v:val.word) > len(input)')
    endif
  elseif mode ==# 'mirror'
    " pass
  else
    return
  endif

  let g:deoplete#_filtered_prev = {
        \ 'complete_position': prev.complete_position,
        \ 'candidates': candidates,
        \ }
  call feedkeys("\<Plug>+", 'i')
endfunction

function! deoplete#handler#_async_timer_start() abort
  let delay = deoplete#custom#_get_option('auto_refresh_delay')
  if delay <= 0
    return
  endif

  call timer_start(max([20, delay]),
        \ {-> deoplete#handler#_completion_begin('Async')})
endfunction

function! deoplete#handler#_completion_begin(event) abort
  call deoplete#custom#_update_cache()

  if s:is_skip(a:event)
    let g:deoplete#_context.candidates = []
    return
  endif

  call s:check_prev_completion(a:event)

  if a:event !=# 'Async'
    call deoplete#init#_prev_completion()
  endif

  call deoplete#util#rpcnotify(
        \ 'deoplete_auto_completion_begin', {'event': a:event})
endfunction
function! s:is_skip(event) abort
  if a:event ==# 'TextChangedP' && !empty(v:completed_item)
    return 1
  endif

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
function! s:check_eskk_phase_henkan(input) abort
  let preedit = eskk#get_preedit()
  let phase = preedit.get_henkan_phase()
  return phase is g:eskk#preedit#PHASE_HENKAN && a:input !~# '\w$'
endfunction
function! s:is_skip_text(event) abort
  let input = deoplete#util#get_input(a:event)

  let lastchar = matchstr(input, '.$')
  let skip_multibyte = deoplete#custom#_get_option('skip_multibyte')
  if skip_multibyte && len(lastchar) != strwidth(lastchar)
        \ && empty(get(b:, 'eskk', []))
    return 1
  endif

  " Note: Use g:deoplete#_context is needed instead of
  " g:deoplete#_prev_completion
  let prev_input = get(g:deoplete#_context, 'input', '')
  if input ==# prev_input
        \ && a:event !=# 'Manual'
        \ && a:event !=# 'Async'
        \ && a:event !=# 'TextChangedP'
    return 1
  endif
  if a:event ==# 'Async' && prev_input !=# '' && input !=# prev_input
    return 1
  endif

  if (exists('b:eskk') && !empty(b:eskk)
        \     && !s:check_eskk_phase_henkan(input))
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

  return (a:event !=# 'Manual' && input !=# ''
        \     && index(skip_chars, input[-1:]) >= 0)
endfunction

function! s:define_on_event(event) abort
  if !exists('##' . a:event)
    return
  endif

  execute 'autocmd deoplete' a:event
        \ '* if !&l:previewwindow | call deoplete#send_event('
        \ .string(a:event).') | endif'
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
  call deoplete#init#_prev_completion()
endfunction

function! s:on_complete_done() abort
  if get(v:completed_item, 'word', '') ==# ''
    return
  endif
  call deoplete#handler#_skip_next_completion()
endfunction

function! deoplete#handler#_skip_next_completion() abort
  if !exists('g:deoplete#_context')
    return
  endif

  let input = deoplete#util#get_input('CompleteDone')
  if input !~# '[/.]$'
    let g:deoplete#_context.input = input
  endif
  call deoplete#mapping#_restore_completeopt()
  call deoplete#init#_prev_completion()
endfunction

function! s:is_exiting() abort
  return exists('v:exiting') && v:exiting != v:null
endfunction

function! s:kill_yarp() abort
  if !exists('g:deoplete#_yarp')
    return
  endif

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
