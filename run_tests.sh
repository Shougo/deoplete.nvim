#!/usr/bin/env bash

set -e

nosetests -v rplugin/python3
flake8 rplugin/
