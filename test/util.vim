let s:suite = themis#suite('parser')
let s:assert = themis#helper('assert')

function! s:suite.vimoption2python() abort
  call s:assert.equals(
        \ deoplete#util#vimoption2python('@,48-57,_,\'), '[a-zA-Z@0-9_\\]')
  call s:assert.equals(
        \ deoplete#util#vimoption2python('@,-,48-57,_'), '[a-zA-Z@0-9_-]')
  call s:assert.equals(
        \ deoplete#util#vimoption2python('@,,,48-57,_'), '[a-zA-Z@,0-9_]')
  call s:assert.equals(
        \ deoplete#util#versioncmp('0.1.10', '0.1.8'), 2)
  call s:assert.equals(
        \ deoplete#util#versioncmp('0.1.10', '0.1.10'), 0)
  call s:assert.equals(
        \ deoplete#util#versioncmp('0.1.10', '0.1.0010'), 0)
  call s:assert.equals(
        \ deoplete#util#versioncmp('0.1.1', '0.1.8'), -7)
  call s:assert.equals(
        \ deoplete#util#versioncmp('0.1.1000', '0.1.10'), 990)
  call s:assert.equals(
        \ deoplete#util#versioncmp('0.1.0001', '0.1.10'), -9)
  call s:assert.equals(
        \ deoplete#util#versioncmp('2.0.1', '1.3.5'), 9696)
  call s:assert.equals(
        \ deoplete#util#versioncmp('3.2.1', '0.0.0'), 30201)
endfunction
