"=============================================================================
" FILE: init.vim
" AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
" License: MIT license
"=============================================================================

if !exists('s:is_enabled')
  let s:is_enabled = 0
endif

function! deoplete#init#_is_enabled() abort "{{{
  return s:is_enabled
endfunction"}}}
function! s:is_initialized() abort "{{{
  return exists('g:deoplete#_channel_id')
endfunction"}}}

function! deoplete#init#_initialize() abort "{{{
  if s:is_initialized()
    return
  endif

  augroup deoplete
    autocmd!
  augroup END

  if !has('nvim') || !has('python3')
    call deoplete#util#print_error(
          \ 'deoplete.nvim does not work with this version.')
    call deoplete#util#print_error(
          \ 'It requires Neovim with Python3 support("+python3").')
    return 1
  endif

  if &completeopt !~# 'noinsert\|noselect'
    let save_completeopt = &completeopt
    try
      set completeopt+=noselect
    catch
      call deoplete#util#print_error(
            \ 'deoplete.nvim does not work with this version.')
      call deoplete#util#print_error(
            \ 'Please update neovim to latest version.')
      return 1
    finally
      let &completeopt = save_completeopt
    endtry
  endif

  try
    if !exists('g:loaded_remote_plugins')
      runtime! plugin/rplugin.vim
    endif
    call _deoplete()
  catch
    call deoplete#util#print_error(
          \ 'deoplete.nvim is not registered as Neovim remote plugins.')
    call deoplete#util#print_error(
          \ 'Please execute :UpdateRemotePlugins command and restart Neovim.')
    return 1
  endtry

  call deoplete#mappings#_init()
  call deoplete#init#_variables()

  let s:is_enabled = g:deoplete#enable_at_startup
  if s:is_enabled
    call deoplete#init#_enable()
  else
    call deoplete#init#_disable()
  endif
endfunction"}}}
function! deoplete#init#_enable() abort "{{{
  call deoplete#handlers#_init()
  let s:is_enabled = 1
endfunction"}}}
function! deoplete#init#_disable() abort "{{{
  augroup deoplete
    autocmd!
  augroup END
  let s:is_enabled = 0
endfunction"}}}

function! deoplete#init#_variables() abort "{{{
  let g:deoplete#_context = {}
  let g:deoplete#_rank = {}

  " User vairables
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_at_startup', 0)
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
        \ 'g:deoplete#delimiters', ['/', '.', '::', ':', '#'])
  call deoplete#util#set_default(
        \ 'g:deoplete#max_list', 100)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_debug', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#enable_profile', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#auto_complete_delay', 0)
  call deoplete#util#set_default(
        \ 'g:deoplete#max_abbr_width', 80)
  call deoplete#util#set_default(
        \ 'g:deoplete#max_menu_width', 40)

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
        \ 'g:deoplete#omni#_input_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#functions', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#omni#_functions', { '_': '' })
  call deoplete#util#set_default(
        \ 'g:deoplete#member#prefix_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#member#_prefix_patterns', {})
  call deoplete#util#set_default(
        \ 'g:deoplete#tag#cache_limit_size', 500000)

  " Initialize default keyword pattern. "{{{
  call deoplete#util#set_pattern(
        \ g:deoplete#_keyword_patterns,
        \ '_',
        \ '[a-zA-Z_]\k*')
  "}}}

  " Initialize omni completion pattern. "{{{
  " Note: HTML omni func use search().
  call deoplete#util#set_pattern(
        \ g:deoplete#_omni_patterns,
        \ 'html,xhtml,xml,markdown,mkd', ['<', '<[^>]*\s[[:alnum:]-]*'])

  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'css,less,scss,sass', ['\w+', '\w+[):;]?\s+\w*', '[@!]'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'ruby', ['[^. \t0-9]\.\w*', '[a-zA-Z_]\w*::\w*'])
  call deoplete#util#set_pattern(
        \ g:deoplete#omni#_input_patterns,
        \ 'lua', ['\w+[.:]', 'require\s*\(?["'']\w*'])
  "}}}

  " Initialize member prefix pattern. "{{{
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ '_', '\.')
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'c,objc', ['\.', '->'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'cpp,objcpp', ['\.', '->', '::'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'perl,php', ['->'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'ruby', ['\.', '::'])
  call deoplete#util#set_pattern(
        \ g:deoplete#member#_prefix_patterns,
        \ 'lua', ['\.', ':'])
  "}}}
endfunction"}}}

function! deoplete#init#_context(event, sources) abort "{{{
  let filetype = (exists('*context_filetype#get_filetype') ?
        \   context_filetype#get_filetype() :
        \   (&filetype == '' ? 'nothing' : &filetype))
  let filetypes = exists('*context_filetype#get_filetypes') ?
        \   context_filetype#get_filetypes() :
        \   &filetype == '' ? ['nothing'] :
        \                     deoplete#util#uniq([&filetype]
        \                          + split(&filetype, '\.'))

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

  let event = (deoplete#util#get_prev_event() ==# 'refresh') ?
        \ 'Manual' : a:event

  let input = deoplete#util#get_input(a:event)

  let width = winwidth(0) - col('.') + len(matchstr(input, '\w*$'))

  return {
        \ 'changedtick': b:changedtick,
        \ 'event': event,
        \ 'input': input,
        \ 'next_input': deoplete#util#get_next_input(a:event),
        \ 'complete_str': '',
        \ 'position': getpos('.'),
        \ 'filetype': filetype,
        \ 'filetypes': filetypes,
        \ 'ignorecase': g:deoplete#enable_ignore_case,
        \ 'smartcase': g:deoplete#enable_smart_case,
        \ 'camelcase': g:deoplete#enable_camel_case,
        \ 'delay': g:deoplete#auto_complete_delay,
        \ 'sources': sources,
        \ 'keyword_patterns': keyword_patterns,
        \ 'max_abbr_width': (width * 2 / 3),
        \ 'max_menu_width': (width * 2 / 3),
        \ }
endfunction"}}}

" vim: foldmethod=marker
