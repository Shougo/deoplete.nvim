let s:suite = themis#suite('custom')
let s:assert = themis#helper('assert')

function! s:suite.custom_source() abort
  call deoplete#custom#_init()

  call deoplete#custom#source('_',
        \ 'matchers', ['matcher_head'])

  call deoplete#custom#source('_', 'converters',
        \ ['converter_auto_delimiter', 'remove_overlap'])

  call s:assert.equals(
        \ deoplete#custom#_get().source,
        \ {'_' : {
        \  'matchers': ['matcher_head'],
        \  'converters': ['converter_auto_delimiter', 'remove_overlap']}})

  call deoplete#custom#_init()

  call deoplete#custom#source('buffer',
        \ 'min_pattern_length', 9999)
  call deoplete#custom#source('buffer', 'rank', 9999)
endfunction

function! s:suite.custom_option() abort
  call deoplete#custom#_init()

  " Buffer options test
  call deoplete#custom#_init()
  call deoplete#custom#_init_buffer()
  call deoplete#custom#option('auto_complete', v:true)
  call s:assert.equals(
        \ deoplete#custom#_get_option('auto_complete'), v:true)

  call deoplete#custom#buffer_option('auto_complete', v:false)
  call s:assert.equals(
        \ deoplete#custom#_get_option('auto_complete'), v:false)

  " Compatibility test
  call deoplete#custom#_init()
  call deoplete#custom#_init_buffer()
  let g:deoplete#disable_auto_complete = 1
  call deoplete#init#_variables()
  call s:assert.equals(
        \ deoplete#custom#_get_option('auto_complete'), v:false)
endfunction
