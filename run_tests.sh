#!/bin/bash

set -e

nosetests -v rplugin/python3
pyflakes rplugin/
