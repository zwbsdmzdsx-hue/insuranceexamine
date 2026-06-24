#!/bin/bash
set -e

cd /Users/camoufcengjingdemacbook/iiqe-study

# Init git if not already
if [ ! -d .git ]; then
  git init
fi

# Add and commit
git add index.html .gitignore 2>/dev/null
git commit -m "Deploy IIQE study page" 2>/dev/null || echo "Nothing new to commit"
git branch -M main

# Push to GitHub (assumes gh auth or ssh key is set up)
git remote add origin https://github.com/zwbsdmzdsx-hue/iiqe-study.git 2>/dev/null || true
git push -u origin main 2>&1

echo "---DONE---"
echo "GITHUB PAGES URL: https://zwbsdmzdsx-hue.github.io/iiqe-study/"
