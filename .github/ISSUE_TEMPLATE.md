**Warning:  I will close the issue without the minimal init.vim and the reproduce ways.**

# Problems summary


## Expected


## Environment Information

 * OS:

 * nvim-python-doctor result or `:CheckHealth` result(neovim ver.0.1.5-452+):
https://github.com/tweekmonster/nvim-python-doctor

```
## Neovim Python Diagnostic

- Neovim Version: NVIM v0.1.4-180-g2ba30a7

## Python versions visible to Neovim

### 'python' info from /usr/local/bin/nvim

WARN: 'g:python_host_prog' is not set
WARN: Fallback to '/usr/bin/python'
**Python Version**: `Python 3.5.1`
**Neovim Package Version**: `neovim (0.1.7)
neovim-gui (0.1.2)
neovim-remote (1.1.3)`

### 'python3' info from /usr/local/bin/nvim

WARN: 'g:python3_host_prog' is not set
WARN: Fallback to '/usr/bin/python3'
**Python Version**: `Python 3.5.1`
**Neovim Package Version**: `neovim (0.1.7)
neovim-gui (0.1.2)
neovim-remote (1.1.3)`

## Python versions visible in the current shell

- **python** version: `Python 3.5.1`
  - **neovim** version: `neovim (0.1.7)
neovim-gui (0.1.2)
neovim-remote (1.1.3)`
- **python3** version: `Python 3.5.1`
  - **neovim** version: `neovim (0.1.7)
neovim-gui (0.1.2)
neovim-remote (1.1.3)`
```

## Provide a minimal init.vim with less than 50 lines (Required!)

```vim
" Your minimal init.vim
set runtimepath+=~/path/to/deoplete.nvim/
let g:deoplete#enable_at_startup = 1
```


## The reproduce ways from neovim starting (Required!)

 1. foo
 2. bar
 3. baz


## Generate a logfile if appropriate

 1. export NVIM_PYTHON_LOG_FILE=/tmp/log
 2. export NVIM_PYTHON_LOG_LEVEL=DEBUG
 3. nvim -u minimal.vimrc
 4. some works
 5. cat /tmp/log_{PID}


## Screen shot (if possible)


## Upload the log file
