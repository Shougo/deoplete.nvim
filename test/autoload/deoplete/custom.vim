let s:suite = themis#suite('custom')
let s:assert = themis#helper('assert')

function! s:suite.custom() abort
  call deoplete#custom#init()

  call deoplete#custom#source('_',
        \ 'matchers', ['matcher_head'])

  call deoplete#custom#source('_', 'converters',
        \ ['converter_auto_delimiter', 'remove_overlap'])

  call s:assert.equals(
        \ deoplete#custom#get().source,
        \ {'_' : {
        \  'matchers': ['matcher_head'],
        \  'converters': ['converter_auto_delimiter', 'remove_overlap']}})

  call deoplete#custom#init()

  call deoplete#custom#source('buffer',
        \ 'min_pattern_length', 9999)
  call deoplete#custom#source('buffer', 'rank', 9999)
endfunction
