"=============================================================================
" FILE: custom.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#custom#get() abort
  if !exists('s:custom')
    let s:custom = {}
    let s:custom._ = {}
  endif

  return s:custom
endfunction

function! deoplete#custom#get_source_var(source_name) abort
  let custom = deoplete#custom#get()

  if !has_key(custom, a:source_name)
    let custom[a:source_name] = {}
  endif

  return custom[a:source_name]
endfunction

function! deoplete#custom#set(source_name, option_name, value) abort
  return deoplete#custom#source(a:source_name, a:option_name, a:value)
endfunction
function! deoplete#custom#source(source_name, option_name, value) abort
  for key in split(a:source_name, '\s*,\s*')
    let custom_source = deoplete#custom#get_source_var(key)
    let custom_source[a:option_name] = a:value
  endfor
endfunction
