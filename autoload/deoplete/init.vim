"=============================================================================
" FILE: init.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

if !exists('s:is_enabled')
  let s:is_enabled = 0
endif

function! deoplete#init#_is_enabled() abort
  return s:is_enabled
endfunction

function! deoplete#init#_initialize() abort
  if !deoplete#init#_check_channel()
    return 1
  endif

  augroup deoplete
    autocmd!
  augroup END

  call deoplete#init#_variables()

  if deoplete#init#_channel()
    return 1
  endif

  call deoplete#mapping#_init()
endfunction
function! deoplete#init#_channel() abort
  if !has('timers')
    call deoplete#util#print_error(
          \ 'deoplete requires timers support("+timers").')
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
      if !has('nvim') && !exists('*neovim_rpc#serveraddr')
        call deoplete#util#print_error(
              \ 'deoplete requires vim-hug-neovim-rpc plugin in Vim.')
      endif

      if !exists('*yarp#py3')
        call deoplete#util#print_error(
              \ 'deoplete requires nvim-yarp plugin.')
      endif
    else
      call deoplete#util#print_error(
          \ 'deoplete failed to load. '
          \ .'Try the :UpdateRemotePlugins command and restart Neovim. '
          \ .'See also :CheckHealth.')
    endif

    return 1
  endtry
endfunction
function! deoplete#init#_check_channel() abort
  return !has('vim_starting') && !exists('g:deoplete#_initialized')
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

function! deoplete#init#_variables() abort
  let g:deoplete#_context = {}
  let g:deoplete#_rank = {}
  if !exists('g:deoplete#_logging')
    let g:deoplete#_logging = {}
  endif
  unlet! g:deoplete#_initialized

  " User vairables
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_at_startup', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_yarp', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#auto_complete_start_length', 2)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_ignore_case', &ignorecase)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_smart_case', &smartcase)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_camel_case', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_refresh_always', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#disable_auto_complete', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#delimiters', ['/'])
  call deoplete#util#set_default(
        \ 'g:deoplete#max_list', 100)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_profile', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#auto_complete_delay', 50)
  call deoplete#util#set_default(
        \ 'g:deoplete#auto_refresh_delay', 500)
  call deoplete#util#set_default(
        \ 'g:deoplete#max_abbr_width', 80)
  call deoplete#util#set_default(
        \ 'g:deoplete#max_menu_width', 40)
  call deoplete#util#set_default(
        \ 'g:deoplete#skip_chars', [])
  call deoplete#util#set_default(
        \ 'g:deoplete#complete_method', 'complete')

  call deoplete#util#set_default(
        \ 'g:deoplete#keyword_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#_keyword_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#_omni_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#sources', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#ignore_sources', {})

  " Source variables
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#input_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#functions', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#member#prefix_patterns', {})

  " Initialize default keyword pattern.
  call deoplete#util#set_pattern(
        \ g:deoplete#_keyword_patterns,
        \ '_',
        \ '[a-zA-Z_]\k*')


  " Initialize omni completion pattern.
  " Note: HTML omni func use search().
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'html,xhtml,xml', ['<', '</', '<[^>]*\s[[:alnum:]-]*'])
endfunction

function! deoplete#init#_context(event, sources) abort
  let input = deoplete#util#get_input(a:event)

  let [filetype, filetypes, same_filetypes] =
        \ deoplete#util#get_context_filetype(input, a:event)

  let sources = deoplete#util#convert2list(a:sources)
  if a:event !=# 'Manual' && empty(sources)
    " Use default sources
    let sources = deoplete#util#get_buffer_config(
          \ filetype,
          \ 'b:deoplete_sources',
          \ 'g:deoplete#sources',
          \ '{}', [])
  endif

  let keyword_patterns = join(deoplete#util#convert2list(
        \   deoplete#util#get_buffer_config(
        \   filetype, 'b:deoplete_keyword_patterns',
        \   'g:deoplete#keyword_patterns',
        \   'g:deoplete#_keyword_patterns')), '|')

  " Convert keyword pattern.
  let pattern = deoplete#util#vimoption2python(
        \ &l:iskeyword . (&l:lisp ? ',-' : ''))
  let keyword_patterns = substitute(keyword_patterns,
        \ '\\k', '\=pattern', 'g')

  let event = (deoplete#util#get_prev_event() ==# 'Refresh') ?
        \ 'Manual' : a:event

  let width = winwidth(0) - col('.') + len(matchstr(input, '\w*$'))

  let bufname = bufname('%')
  let bufpath = fnamemodify(bufname, ':p')
  if &l:buftype =~# 'nofile' || !filereadable(bufpath)
    let bufpath = ''
  endif

  return {
        \ 'changedtick': b:changedtick,
        \ 'event': event,
        \ 'input': input,
        \ 'next_input': deoplete#util#get_next_input(a:event),
        \ 'complete_str': '',
        \ 'encoding': &encoding,
        \ 'position': getpos('.'),
        \ 'filetype': filetype,
        \ 'filetypes': filetypes,
        \ 'same_filetypes': same_filetypes,
        \ 'ignorecase': g:deoplete#enable_ignore_case,
        \ 'smartcase': g:deoplete#enable_smart_case,
        \ 'camelcase': g:deoplete#enable_camel_case,
        \ 'delay': g:deoplete#auto_complete_delay,
        \ 'sources': sources,
        \ 'keyword_patterns': keyword_patterns,
        \ 'max_abbr_width': (width * 2 / 3),
        \ 'max_kind_width': (width * 2 / 3),
        \ 'max_menu_width': (width * 2 / 3),
        \ 'runtimepath': &runtimepath,
        \ 'bufnr': bufnr('%'),
        \ 'bufname': bufname,
        \ 'bufpath': bufpath,
        \ 'bufsize': wordcount().bytes,
        \ 'cwd': getcwd(),
        \ 'vars': filter(copy(g:),
        \       "stridx(v:key, 'deoplete#') == 0
        \        && v:key !=# 'deoplete#_yarp'"),
        \ 'bufvars': filter(copy(b:), "stridx(v:key, 'deoplete_') == 0"),
        \ 'custom': deoplete#custom#get(),
        \ 'omni__omnifunc': &l:omnifunc,
        \ 'dict__dictionary': &l:dictionary,
        \ }
endfunction
