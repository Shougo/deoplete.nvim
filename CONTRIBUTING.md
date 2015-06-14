# Problems summary

## Expected

## Environment Information
 * OS:
 * Neovim version:

## Minimal nvimrc less than 50 lines

   " Your nvimrc
   set runtimepath+=~/path/to/deoplete.nvim/

  let g:deoplete#enable_at_startup = 1

## Reproducable ways from Neovim starting

 1. export NVIM_PYTHON_LOG_FILE=/tmp/log
 2. export NVIM_PYTHON_LOG_LEVEL=DEBUG
 3. nvim -u minimal.vimrc
 4. some works
 5. cat /tmp/log_{PID}

## Screen shot (if possible)

## Upload the log file
