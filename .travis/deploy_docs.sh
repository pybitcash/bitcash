#!/bin/bash

# Ideas from https://github.com/steveklabnik/automatically_update_github_pages_with_travis_example

set -o errexit -o nounset

if [ "$TRAVIS_PULL_REQUEST" != "false" ] || [ "$TRAVIS_BRANCH" != "master" ]
then
  echo "This commit was made against the $TRAVIS_BRANCH and not the master! No deploy!"
  exit 0
fi

echo "Building docs..."

rev=$(git rev-parse --short HEAD)

pip install sphinxcontrib-fulltoc
pip install .

cd docs
make clean
make html
cd build/html

git init
git config user.name "Teran McKinney"
git config user.email ""

git remote add upstream "https://$GH_TOKEN@github.com/pybitcash/bitcash.git"
git fetch upstream
git reset upstream/gh-pages

touch .

git add -A .
git commit -m "rebuild pages at ${rev}"
git push -q upstream HEAD:gh-pages

echo "Published to gh-pages branch."
