#!/bin/bash
# Install AZPowers-Skills for Agent Zero
set -e

REPO=/a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo

echo '=== AZPowers-Skills Installation ==='

# Step 1: Install npm dependencies and build
echo '[1/3] Building CPS dist...'
cd "$REPO"
npm install
npm run build
echo '  -> dist/index.js built'

# Step 2: Create ~/.clawpowers runtime dirs
echo '[2/3] Creating ~/.clawpowers runtime directories...'
mkdir -p ~/.clawpowers/{memory,metrics,logs,wallet,state/checkpoints,data,skills}
echo '  -> ~/.clawpowers/ ready'

# Step 3: Install ITP service dependencies
echo '[3/3] Installing ITP service Python dependencies...'
cd /a0/usr/projects/adapt_clawpowers-skills_to_a0/itp-service
pip install -q -r requirements.txt
echo '  -> ITP service deps installed'

echo ''
echo 'AZPowers-Skills installed successfully!'
echo ''
echo 'Next steps:'
echo '  1. Start ITP service: bash /a0/usr/projects/adapt_clawpowers-skills_to_a0/itp-service/start.sh'
echo '  2. Run smoke test:    node /a0/usr/projects/adapt_clawpowers-skills_to_a0/scripts/smoke-test.mjs'
echo '  3. Run verify:        bash /a0/usr/projects/adapt_clawpowers-skills_to_a0/scripts/verify.sh'
