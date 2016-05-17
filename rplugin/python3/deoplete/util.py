# ============================================================================
# FILE: util.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import json
import re
import os
import sys
import unicodedata


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
    p = re.compile(pattern)
    return list(set(p.findall('\n'.join(f.read()))))


def parse_buffer_pattern(b, pattern, complete_str):
    p = re.compile(pattern)
    return [x for x in p.findall('\n'.join(b)) if x != complete_str]


def fuzzy_escape(string, camelcase):
    # Escape string for python regexp.
    p = re.sub(r'([a-zA-Z0-9_])', r'\1.*', re.escape(string))
    if camelcase and re.search(r'[A-Z]', string):
        p = re.sub(r'([a-z])', (lambda pat:
                                '['+pat.group(1)+pat.group(1).upper()+']'), p)
    p = re.sub(r'([a-zA-Z0-9_])\.\*', r'\1[^\1]*', p)
    return p


def load_external_module(file, module):
    current = os.path.dirname(os.path.abspath(file))
    module_dir = os.path.join(os.path.dirname(current), module)
    sys.path.insert(0, module_dir)


def truncate_skipping(string, max, footer, footer_len):
    if len(string) <= max/2:
        return string
    if strwidth(string) <= max:
        return string

    footer += string[
            -len(truncate(string[::-1], footer_len)):]
    return truncate(string, max - strwidth(footer)) + footer


def truncate(string, max):
    if len(string) <= max/2:
        return string
    if strwidth(string) <= max:
        return string

    width = 0
    ret = ''
    for c in string:
        wc = charwidth(c)
        if width + wc > max:
            break
        ret += c
        width += wc
    return ret


def strwidth(string):
    width = 0
    for c in string:
        width += charwidth(c)
    return width


def charwidth(c):
    wc = unicodedata.east_asian_width(c)
    return 2 if wc == 'F' or wc == 'W' else 1
