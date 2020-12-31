#!/bin/sh

tar -xvf $1 --wildcards --no-anchored '*/setup.py' --strip=1
