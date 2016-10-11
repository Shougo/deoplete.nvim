"=============================================================================
" FILE: deoplete.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
"         TJ DeVries <devries.timothyj at gmail.com>
" License: MIT license
"=============================================================================

function! s:check_neovim() abort
  if has('nvim')
    call health#report_ok('has("nvim") was successful')
  else
    call health#report_error('has("nvim") was not successful',
          \ 'Deoplete only works for neovim!')
  endif
endfunction

function! s:check_required_python_for_deoplete() abort
  if has('python3')
    call health#report_ok('has("python3") was successful')
  else
    call health#report_error('has("python3") was not successful', [
          \ 'Please install the python3 package for neovim.',
          \ 'A good guide can be found here: ' .
          \ 'https://github.com/tweekmonster/nvim-python-doctor/'
          \ . 'wiki/Advanced:-Using-pyenv'
          \ ]
          \ )
  endif
endfunction

function! s:still_have_issues() abort
  let indentation = '        '
  call health#report_info("If you're still having problems, " .
        \ "try the following commands:\n" .
        \ indentation . "$ export NVIM_PYTHON_LOG_FILE=/tmp/log\n" .
        \ indentation . "$ export NVIM_PYTHON_LOG_LEVEL=DEBUG\n" .
        \ indentation . "$ nvim\n" .
        \ indentation . "$ cat /tmp/log_{PID}\n" .
        \ indentation . ' and then create an issue on github'
        \ )
endfunction

function! health#deoplete#check() abort
  call health#report_start('deoplete.nvim')
  call s:check_neovim()
  call s:check_required_python_for_deoplete()
  call s:still_have_issues()
endfunction
