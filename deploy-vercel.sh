#!/bin/bash
set -e
echo "=== Step 1: Check available tools ==="
which npx 2>&1 || echo "npx not found"
which vercel 2>&1 || echo "vercel CLI not found"
which gh 2>&1 || echo "gh not found"
which git 2>&1 || echo "git not found"

echo ""
echo "=== Step 2: Check vercel.json ==="
cat /Users/camoufcengjingdemacbook/iiqe-study/vercel.json

echo ""
echo "=== Step 3: Check HTML file ==="
ls -la /Users/camoufcengjingdemacbook/iiqe-study/index.html

echo ""
echo "=== Step 4: Try Vercel deploy ==="
cd /Users/camoufcengjingdemacbook/iiqe-study

# Check if VERCEL_TOKEN is set
if [ -n "$VERCEL_TOKEN" ]; then
  echo "VERCEL_TOKEN is set, deploying..."
  npx vercel --prod --yes --token "$VERCEL_TOKEN" 2>&1 || true
else
  echo "VERCEL_TOKEN not set, trying without (may prompt)"
  # Try deploying without token - might use existing auth
  npx vercel --prod --yes 2>&1 || true
fi

echo ""
echo "=== Step 5: If Vercel fails, try surge.sh ==="
which surge 2>&1 && surge --domain iiqe-study.surge.sh ./ 2>&1 || echo "surge not available"

echo ""
echo "=== Step 6: Try npx surge ==="
npx surge --domain iiqe-study.surge.sh ./ 2>&1 || echo "surge deploy failed"

echo ""
echo "=== DONE ==="
