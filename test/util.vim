let s:suite = themis#suite('parser')
let s:assert = themis#helper('assert')

function! s:suite.vimoption2python() abort
  call s:assert.equals(
        \ deoplete#util#vimoption2python('@,48-57,_'), '[a-zA-Z@0-9_]')
  call s:assert.equals(
        \ deoplete#util#vimoption2python('@,-,48-57,_'), '[a-zA-Z@0-9_-]')
  call s:assert.equals(
        \ deoplete#util#vimoption2python('@,,,48-57,_'), '[a-zA-Z@,0-9_]')
endfunction


" vim:foldmethod=marker:fen:
