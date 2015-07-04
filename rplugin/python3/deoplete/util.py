#=============================================================================
# FILE: util.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license  {{{
#     Permission is hereby granted, free of charge, to any person obtaining
#     a copy of this software and associated documentation files (the
#     "Software"), to deal in the Software without restriction, including
#     without limitation the rights to use, copy, modify, merge, publish,
#     distribute, sublicense, and/or sell copies of the Software, and to
#     permit persons to whom the Software is furnished to do so, subject to
#     the following conditions:
#
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#     CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#     TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#     SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# }}}
#=============================================================================

def get_buffer_config(vim, context, buffer_var, user_var, default_var):
    return vim.eval(('deoplete#util#get_buffer_config(' \
                    +'"{0}", "{1}", {2}, {3})') \
             .format(context['filetype'],
                     buffer_var, user_var, default_var))

def get_default_buffer_config(vim, context, buffer_var, user_var, default_var):
    return vim.eval(('deoplete#util#get_default_buffer_config(' \
                    +'"{0}", "{1}", {2}, {3})') \
             .format(context['filetype'],
                     buffer_var, user_var, default_var))

def get_simple_buffer_config(vim, buffer_var, user_var):
    return vim.eval('deoplete#util#get_simple_buffer_config("{0}", {1})' \
             .format(buffer_var, user_var))

def set_pattern(vim, variable, keys, pattern):
    return vim.eval("deoplete#util#set_pattern({0}, '{1}', '{2}')" \
             .format(variable, keys, pattern))

def set_default(vim, var, val):
    return vim.eval("deoplete#util#set_default('{0}', {1})" \
             .format(var, val))

def convert2list(expr):
    return (expr if isinstance(expr, list) else [expr])

def globruntime(vim, path):
    return vim.eval("globpath(&runtimepath, '" + path + "', 1, 1)")

def debug(vim, msg):
    vim.command('echomsg string("' + str(msg) + '")')

