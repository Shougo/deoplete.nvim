"=============================================================================
" FILE: init.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

if !exists('s:is_handler_enabled')
  let s:is_handler_enabled = 0
endif

function! deoplete#init#_is_handler_enabled() abort
  return s:is_handler_enabled
endfunction

function! deoplete#init#_initialize() abort
  if exists('g:deoplete#_initialized')
    return 1
  endif

  let g:deoplete#_initialized = v:false

  call s:init_internal_variables()
  call deoplete#init#_custom_variables()

  if deoplete#init#_channel()
    return 1
  endif

  call deoplete#mapping#_init()
endfunction
function! deoplete#init#_channel() abort
  if !exists('g:deoplete#_serveraddr')
    return 1
  endif

  let python3 = get(g:, 'python3_host_prog', 'python3')
  if !executable(python3)
    call deoplete#util#print_error(
          \ string(python3) . ' is not executable.')
    call deoplete#util#print_error(
          \ 'You need to set g:python3_host_prog.')
  endif
  if has('nvim') && !has('nvim-0.3.0')
    call deoplete#util#print_error('deoplete requires nvim 0.3.0+.')
    return 1
  endif

  try
    if deoplete#util#has_yarp()
      let g:deoplete#_yarp = yarp#py3('deoplete')
      call g:deoplete#_yarp.notify('deoplete_init')
    else
      " rplugin.vim may not be loaded on VimEnter
      if !exists('g:loaded_remote_plugins')
        runtime! plugin/rplugin.vim
      endif

      call _deoplete_init()
    endif
  catch
    call deoplete#util#print_error(v:exception)
    call deoplete#util#print_error(v:throwpoint)

    if !has('python3')
      call deoplete#util#print_error(
            \ 'deoplete requires Python3 support("+python3").')
    endif

    if deoplete#util#has_yarp()
      echomsg string(expand('<sfile>'))
      if !exists('*yarp#py3')
        call deoplete#util#print_error(
              \ 'deoplete requires nvim-yarp plugin.')
      endif
    else
      call deoplete#util#print_error(
          \ 'deoplete failed to load. '
          \ .'Try the :UpdateRemotePlugins command and restart Neovim. '
          \ .'See also :checkhealth.')
    endif

    return 1
  endtry
endfunction
function! deoplete#init#_channel_initialized() abort
  return get(g:, 'deoplete#_initialized', v:false)
endfunction
function! deoplete#init#_enable_handler() abort
  call deoplete#handler#_init()
  let s:is_handler_enabled = 1
endfunction
function! deoplete#init#_disable_handler() abort
  augroup deoplete
    autocmd!
  augroup END
  let s:is_handler_enabled = 0
endfunction

function! s:init_internal_variables() abort
  call deoplete#init#_prev_completion()

  let g:deoplete#_context = {}

  if !exists('g:deoplete#_logging')
    let g:deoplete#_logging = {}
  endif
  unlet! g:deoplete#_initialized
  try
    let g:deoplete#_serveraddr =
          \ deoplete#util#has_yarp() ?
          \ neovim_rpc#serveraddr() : v:servername
    if g:deoplete#_serveraddr ==# ''
      " Use NVIM_LISTEN_ADDRESS
      let g:deoplete#_serveraddr = $NVIM_LISTEN_ADDRESS
    endif
  catch
    if deoplete#util#has_yarp() && !exists('*neovim_rpc#serveraddr')
      call deoplete#util#print_error(
            \ 'deoplete requires vim-hug-neovim-rpc plugin in Vim.')
    endif
  endtry
endfunction
function! deoplete#init#_custom_variables() abort
  if get(g:, 'deoplete#disable_auto_complete', v:false)
    call deoplete#custom#option('auto_complete', v:false)
  endif
  call s:check_custom_option(
        \ 'g:deoplete#auto_complete_delay',
        \ 'auto_complete_delay')
  call s:check_custom_option(
        \ 'g:deoplete#auto_refresh_delay',
        \ 'auto_refresh_delay')
  call s:check_custom_option(
        \ 'g:deoplete#camel_case',
        \ 'camel_case')
  call s:check_custom_option(
        \ 'g:deoplete#delimiters',
        \ 'delimiters')
  call s:check_custom_option(
        \ 'g:deoplete#ignore_case',
        \ 'ignore_case')
  call s:check_custom_option(
        \ 'g:deoplete#ignore_sources',
        \ 'ignore_sources')
  call s:check_custom_option(
        \ 'g:deoplete#keyword_patterns',
        \ 'keyword_patterns')
  call s:check_custom_option(
        \ 'g:deoplete#max_list',
        \ 'max_list')
  call s:check_custom_option(
        \ 'g:deoplete#num_processes',
        \ 'num_processes')
  call s:check_custom_option(
        \ 'g:deoplete#auto_complete_start_length',
        \ 'min_pattern_length')
  call s:check_custom_option(
        \ 'g:deoplete#enable_on_insert_enter',
        \ 'on_insert_enter')
  call s:check_custom_option(
        \ 'g:deoplete#enable_profile',
        \ 'profile')
  call s:check_custom_option(
        \ 'g:deoplete#enable_refresh_always',
        \ 'refresh_always')
  call s:check_custom_option(
        \ 'g:deoplete#skip_chars',
        \ 'skip_chars')
  call s:check_custom_option(
        \ 'g:deoplete#sources',
        \ 'sources')
  call s:check_custom_option(
        \ 'g:deoplete#enable_smart_case',
        \ 'smart_case')
  call s:check_custom_option(
        \ 'g:deoplete#enable_yarp',
        \ 'yarp')

  " Source variables
  call s:check_custom_var('file',
        \ 'g:deoplete#file#enable_buffer_path',
        \ 'enable_buffer_path')
  call s:check_custom_var('omni',
        \ 'g:deoplete#omni#input_patterns',
        \ 'input_patterns')
  call s:check_custom_var('omni',
        \ 'g:deoplete#omni#functions',
        \ 'functions')
endfunction

function! s:check_custom_var(source_name, old_var, new_var) abort
  if exists(a:old_var)
    call deoplete#custom#var(a:source_name, a:new_var, eval(a:old_var))
  endif
endfunction
function! s:check_custom_option(old_var, new_var) abort
  if exists(a:old_var)
    call deoplete#custom#option(a:new_var, eval(a:old_var))
  endif
endfunction

function! deoplete#init#_option() abort
  " Note: HTML omni func use search().
  return {
        \ 'auto_complete': v:true,
        \ 'auto_complete_delay': 0,
        \ 'auto_refresh_delay': 20,
        \ 'camel_case': v:false,
        \ 'delimiters': ['/'],
        \ 'ignore_case': &ignorecase,
        \ 'ignore_sources': {},
        \ 'candidate_marks': [],
        \ 'max_list': 500,
        \ 'num_processes': 4,
        \ 'keyword_patterns': {'_': '[a-zA-Z_]\k*'},
        \ 'omni_patterns': {},
        \ 'on_insert_enter': v:true,
        \ 'on_text_changed_i': v:true,
        \ 'profile': v:false,
        \ 'prev_completion_mode': 'filter',
        \ 'min_pattern_length': 2,
        \ 'refresh_always': v:true,
        \ 'skip_chars': ['(', ')'],
        \ 'skip_multibyte': v:false,
        \ 'smart_case': &smartcase,
        \ 'sources': {},
        \ 'trigger_key': v:char,
        \ 'yarp': v:false,
        \ }
endfunction
function! deoplete#init#_prev_completion() abort
  let g:deoplete#_prev_completion = {
        \ 'event': '',
        \ 'input': '',
        \ 'linenr': -1,
        \ 'candidates': [],
        \ 'complete_position': -1,
        \ }
endfunction

function! deoplete#init#_python_version_check() abort
  python3 << EOF
import vim
import sys
vim.vars['deoplete#_python_version_check'] = (
    sys.version_info.major,
    sys.version_info.minor,
    sys.version_info.micro) < (3, 5, 0)
EOF
  return g:deoplete#_python_version_check
endfunction
