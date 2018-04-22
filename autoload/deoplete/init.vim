"=============================================================================
" FILE: init.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

if !exists('s:is_enabled')
  let s:is_enabled = 0
endif

let s:is_windows = ((has('win32') || has('win64')) ? v:true : v:false)

function! deoplete#init#_is_enabled() abort
  return s:is_enabled
endfunction

function! deoplete#init#_initialize() abort
  if has('vim_starting')
    augroup deoplete
      autocmd!
      autocmd VimEnter * call deoplete#enable()
    augroup END
    return 1
  endif

  if !deoplete#init#_check_channel()
    return 1
  endif

  augroup deoplete
    autocmd!
  augroup END

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
function! deoplete#init#_check_channel() abort
  return !exists('g:deoplete#_initialized')
endfunction
function! deoplete#init#_enable() abort
  call deoplete#handler#_init()
  let s:is_enabled = 1
endfunction
function! deoplete#init#_disable() abort
  augroup deoplete
    autocmd!
  augroup END
  let s:is_enabled = 0
endfunction

function! s:init_internal_variables() abort
  let g:deoplete#_prev_completion = {
        \ 'complete_position': [],
        \ 'candidates': [],
        \ 'event': '',
        \ }
  let g:deoplete#_context = {}
  let g:deoplete#_rank = {}
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

function! deoplete#init#_context(event, sources) abort
  let input = deoplete#util#get_input(a:event)

  let [filetype, filetypes, same_filetypes] =
        \ deoplete#util#get_context_filetype(input, a:event)

  let sources = deoplete#util#convert2list(a:sources)
  if a:event !=# 'Manual' && empty(sources)
    " Use default sources
    let sources = deoplete#custom#_get_filetype_option(
          \ 'sources', filetype, [])
  endif

  let event = (deoplete#util#get_prev_event() ==# 'Refresh') ?
        \ 'Manual' : a:event

  let width = winwidth(0) - col('.') + len(matchstr(input, '\w*$'))
  let max_width = (width * 2 / 3)

  if a:event ==# 'BufNew'
    let bufnr = expand('<abuf>')
  else
    let bufnr = bufnr('%')
  endif
  let bufname = bufname(bufnr)
  let bufpath = fnamemodify(bufname, ':p')
  if !filereadable(bufpath) || getbufvar(bufnr, '&buftype') =~# 'nofile'
    let bufpath = ''
  endif

  return {
        \ 'changedtick': b:changedtick,
        \ 'event': event,
        \ 'input': input,
        \ 'is_windows': s:is_windows,
        \ 'next_input': deoplete#util#get_next_input(a:event),
        \ 'complete_str': '',
        \ 'encoding': &encoding,
        \ 'position': getpos('.'),
        \ 'filetype': filetype,
        \ 'filetypes': filetypes,
        \ 'same_filetypes': same_filetypes,
        \ 'ignorecase': deoplete#custom#_get_option('ignore_case'),
        \ 'smartcase': deoplete#custom#_get_option('smart_case'),
        \ 'camelcase': deoplete#custom#_get_option('camel_case'),
        \ 'delay': deoplete#custom#_get_option('auto_complete_delay'),
        \ 'sources': sources,
        \ 'max_abbr_width': max_width,
        \ 'max_kind_width': max_width,
        \ 'max_menu_width': max_width,
        \ 'runtimepath': &runtimepath,
        \ 'bufnr': bufnr,
        \ 'bufname': bufname,
        \ 'bufpath': bufpath,
        \ 'cwd': getcwd(),
        \ 'vars': filter(copy(g:),
        \       "stridx(v:key, 'deoplete#') == 0
        \        && v:key !=# 'deoplete#_yarp'"),
        \ 'bufvars': filter(copy(b:), "stridx(v:key, 'deoplete_') == 0"),
        \ 'custom': deoplete#custom#_get(),
        \ 'omni__omnifunc': &l:omnifunc,
        \ 'dict__dictionary': &l:dictionary,
        \ }
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
        \ 'auto_complete_delay': 50,
        \ 'auto_refresh_delay': 50,
        \ 'camel_case': v:false,
        \ 'complete_method': 'complete',
        \ 'delimiters': ['/'],
        \ 'ignore_case': &ignorecase,
        \ 'ignore_sources': {},
        \ 'max_list': 500,
        \ 'num_processes': s:is_windows ? 1 : 4,
        \ 'keyword_patterns': {'_': '[a-zA-Z_]\k*'},
        \ 'omni_patterns': {
        \  'html': ['<', '</', '<[^>]*\s[[:alnum:]-]*'],
        \  'xhtml': ['<', '</', '<[^>]*\s[[:alnum:]-]*'],
        \  'xml': ['<', '</', '<[^>]*\s[[:alnum:]-]*'],
        \ },
        \ 'on_insert_enter': v:true,
        \ 'profile': v:false,
        \ 'min_pattern_length': 2,
        \ 'refresh_always': v:false,
        \ 'skip_chars': ['(', ')'],
        \ 'smart_case': &smartcase,
        \ 'sources': {},
        \ 'yarp': v:false,
        \ }
endfunction
