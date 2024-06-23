#!/usr/bin/env bash
set -e

rye build --clean
docker build -t registry.bango29.com/melly/api:latest .
docker push registry.bango29.com/melly/api:latest
