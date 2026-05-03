#!/bin/bash
set -e
rm -rf build docs
find . -type d -name __pycache__ -exec rm -rf {} +
