#!/bin/bash
cd /Users/camoufcengjingdemacbook/iiqe-study
git add -A
git commit --allow-empty -m "Deploy IIQE study page"
git push -f origin main 2>&1
echo "EXIT_CODE=$?"
