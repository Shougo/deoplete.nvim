"=============================================================================
" FILE: custom.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

function! deoplete#custom#init() abort
  let s:custom = {}
  let s:custom.source = {}
  let s:custom.source._ = {}
endfunction

function! deoplete#custom#get() abort
  if !exists('s:custom')
    call deoplete#custom#init()
  endif

  return s:custom
endfunction

function! deoplete#custom#get_source_var(source_name) abort
  let custom = deoplete#custom#get().source

  if !has_key(custom, a:source_name)
    let custom[a:source_name] = {}
  endif

  return custom[a:source_name]
endfunction

function! deoplete#custom#set(source_name, option_name, value) abort
  call deoplete#util#print_error(
        \ 'deoplete#custom#set() is deprecated.')
  call deoplete#util#print_error(
        \ 'Please use deoplete#custom#source() instead.')
  return deoplete#custom#source(a:source_name, a:option_name, a:value)
endfunction
function! deoplete#custom#source(source_name, option_name, value) abort
  let value = index([
        \ 'filetypes', 'disabled_syntaxes',
        \ 'matchers', 'sorters', 'converters'
        \ ], a:option_name) < 0 ? a:value :
        \ deoplete#util#convert2list(a:value)
  for key in split(a:source_name, '\s*,\s*')
    let custom_source = deoplete#custom#get_source_var(key)
    let custom_source[a:option_name] = value
  endfor
endfunction
function! deoplete#custom#var(source_name, var_name, value) abort
  for key in split(a:source_name, '\s*,\s*')
    let custom_source = deoplete#custom#get_source_var(key)
    let vars = get(custom_source, 'vars', {})
    let vars[a:var_name] = a:value
    call deoplete#custom#source(key, 'vars', vars)
  endfor
endfunction
