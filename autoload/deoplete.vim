"=============================================================================
" FILE: deoplete.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#initialize() abort "{{{
  return deoplete#init#enable()
endfunction"}}}

function! deoplete#enable_logging(level, logfile) abort "{{{
  if !deoplete#init#is_enabled()
    " Enable to allow logging before completions start.
    call deoplete#init#enable()
  endif

  call rpcrequest(g:deoplete#_channel_id,
        \ 'deoplete_enable_logging', a:level, a:logfile)
endfunction"}}}

" vim: foldmethod=marker
