# ============================================================================
# FILE: util.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import functools
import json
import operator
import os
import re
import sys


def get_buffer_config(vim, filetype, buffer_var, user_var, default_var):
    return vim.call('deoplete#util#get_buffer_config',
                    filetype, buffer_var, user_var, default_var)


def get_simple_buffer_config(vim, buffer_var, user_var):
    return vim.call('deoplete#util#get_simple_buffer_config',
                    buffer_var, user_var)


def set_pattern(vim, variable, keys, pattern):
    return vim.call('deoplete#util#set_pattern', variable, keys, pattern)


def set_list(vim, variable, keys, list):
    return vim.call('deoplete#util#set_pattern', variable, keys, list)


def set_default(vim, var, val):
    return vim.call('deoplete#util#set_default', var, val)


def convert2list(expr):
    return (expr if isinstance(expr, list) else [expr])


def globruntime(vim, path):
    return vim.funcs.globpath(vim.options['runtimepath'], path, 1, 1)


def debug(vim, expr):
    if vim.vars['deoplete#enable_debug']:
        try:
            json_data = json.dumps(str(expr).strip())
        except Exception:
            vim.command('echomsg string(\'' + str(expr).strip() + '\')')
        else:
            vim.command('echomsg string(\'' + escape(json_data) + '\')')

    else:
        error(vim, "not in debug mode, but debug called")


def error(vim, msg):
    vim.call('deoplete#util#print_error', msg)


def escape(expr):
    return expr.replace("'", "''")


def charpos2bytepos(vim, input, pos):
    return len(bytes(input[: pos], vim.options['encoding']))


def bytepos2charpos(vim, input, pos):
    return len(vim.funcs.substitute(
        vim.funcs.strpart(input, 0, pos), '.', 'x', 'g'))


def get_custom(vim, source_name):
    return vim.call('deoplete#custom#get', source_name)


def get_syn_name(vim):
    return vim.call('deoplete#util#get_syn_name')


def parse_file_pattern(f, pattern):
    lines = f.readlines()
    if not lines:
        return []
    p = re.compile(pattern)
    return list(set(functools.reduce(operator.add, [
        p.findall(x) for x in lines
    ])))


def fuzzy_escape(string, camelcase):
    # Escape string for python regexp.
    p = re.sub(r'([a-zA-Z0-9_])', r'\1.*', re.escape(string))
    if camelcase and re.search(r'[A-Z]', string):
        p = re.sub(r'([a-z])', (lambda pat:
                                '['+pat.group(1)+pat.group(1).upper()+']'), p)
    return p


def load_external_module(file, module):
    current = os.path.dirname(os.path.abspath(file))
    module_dir = os.path.join(os.path.dirname(current), module)
    sys.path.insert(0, module_dir)
