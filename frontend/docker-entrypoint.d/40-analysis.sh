#!/bin/sh
# Overlay the freshest analysis published by the pipeline container, if present.
# Runs via nginx's /docker-entrypoint.d hook, before the server starts.
set -e
if [ -f /shared/analysis_results.json ]; then
    cp /shared/analysis_results.json /usr/share/nginx/html/analysis_results.json
    echo "40-analysis.sh: using pipeline-generated analysis from /shared"
else
    echo "40-analysis.sh: no /shared/analysis_results.json — serving baked-in sample"
fi
