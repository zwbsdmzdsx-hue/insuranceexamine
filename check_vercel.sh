#!/bin/bash
echo "=== Checking vercel CLI ==="
which vercel 2>&1 || echo "vercel not in PATH"
echo ""
echo "=== npx vercel version ==="
npx vercel --version 2>&1
echo ""
echo "=== Checking auth ==="
cat ~/.vercel/auth.json 2>&1 || echo "No auth file found"
echo ""
echo "=== Checking ~/.vercel/config.json ==="
cat ~/.vercel/config.json 2>&1 || echo "No config file"
echo ""
echo "=== Checking project ==="
ls -la /Users/camoufcengjingdemacbook/iiqe-study/ 2>&1
