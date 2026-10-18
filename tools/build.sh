# Copies the files the browser loads into dist/ for `wrangler deploy`: the page, its modules, the skins and each battle's data.
# make.py, the research tools and the docs stay behind. Run from the repo root.
set -e
rm -rf dist; mkdir -p dist/battles
cp index.html app.js sim.js themes.js favicon.svg apple-touch-icon.png dist/
cp -R themes dist/
cp battles/index.json dist/battles/
for d in battles/*/; do id=$(basename "$d"); mkdir dist/battles/$id; cp $d/battle.json $d/terrain.json dist/battles/$id/; done
