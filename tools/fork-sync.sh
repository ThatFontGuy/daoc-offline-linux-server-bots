#!/usr/bin/env bash
# fork-sync.sh - bring this fork's branch up to date with its parent fork (for example
# catastrophic-impact/daoc-offline-linux-server-bots). This is NOT tools/upstream/sync.sh, which
# pulls shadowofze/OfflineDAoC's game code into src/; this script is for when GitHub shows this
# repo itself "N commits behind" the repo it was forked from.
#
#   tools/fork-sync.sh [--push] [--branch <name>] [--upstream-branch <name>]
#
# Why not `git merge`/`git rebase upstream/main`: if this fork's early history was pushed as fresh
# commits rather than a literal `git fork`, content that matches byte-for-byte can still be a
# different commit object, so rebase/merge may find no common ancestor and conflict across nearly
# every file even though nothing really conflicts. This script sidesteps that: it backs up the
# current branch, resets it straight to the parent's tip, and reports (but does NOT silently
# reapply) any commits that only existed on our side, so a real fix isn't lost quietly.
#
# Steps:
#   1. Requires a configured 'upstream' remote (the parent repo) and a clean working tree.
#   2. Reports how far ahead/behind the branch is; exits if already level.
#   3. Backs up the current branch to <branch>-pre-sync-<timestamp>.
#   4. Prints any commits that exist only on our branch (not on upstream) for manual review -
#      check each one against the parent's current code; re-port anything still needed as a new
#      commit after the reset (see docs/history for an example from the v0.36 sync).
#   5. Resets the branch to upstream/<upstream-branch>.
#   6. With --push, force-pushes the result to origin/<branch> (--force-with-lease). Without it,
#      the push is left as an explicit next step so you can review first.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

PUSH=0
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
UPSTREAM_BRANCH="main"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --upstream-branch) UPSTREAM_BRANCH="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

git remote get-url upstream >/dev/null 2>&1 || {
  echo "No 'upstream' remote configured. Add the parent repo first, for example:" >&2
  echo "  git remote add upstream https://github.com/catastrophic-impact/daoc-offline-linux-server-bots.git" >&2
  exit 1
}

[[ -z $(git status --porcelain) ]] || {
  echo "Working tree is not clean (tracked or untracked changes); commit or 'git stash -u' first." >&2
  exit 1
}

echo "== Fetching upstream..."
git fetch upstream --quiet
git fetch origin --quiet 2>/dev/null || true

AHEAD=$(git log --oneline "upstream/$UPSTREAM_BRANCH..$BRANCH" | wc -l | tr -d ' ')
BEHIND=$(git log --oneline "$BRANCH..upstream/$UPSTREAM_BRANCH" | wc -l | tr -d ' ')
echo "== $BRANCH is $AHEAD commit(s) ahead, $BEHIND behind upstream/$UPSTREAM_BRANCH"

if [[ $BEHIND -eq 0 ]]; then
  echo "Already level with upstream/$UPSTREAM_BRANCH. Nothing to do."
  exit 0
fi

BACKUP="${BRANCH}-pre-sync-$(date +%Y%m%d%H%M%S)"
git branch "$BACKUP" "$BRANCH"
echo "== Backed up current $BRANCH to branch $BACKUP (full history kept, nothing deleted)"

if [[ $AHEAD -gt 0 ]]; then
  echo
  echo "== $AHEAD commit(s) exist only on $BRANCH, not on upstream/$UPSTREAM_BRANCH."
  echo "   These are NOT reapplied automatically - review each one against upstream's current"
  echo "   code and re-port anything still needed as a fresh commit after the reset below."
  echo "   (Full copies remain on $BACKUP if you need to look at them.)"
  echo
  git log --oneline "upstream/$UPSTREAM_BRANCH..$BRANCH"
  echo
fi

git reset --hard "upstream/$UPSTREAM_BRANCH"
echo "== $BRANCH reset to upstream/$UPSTREAM_BRANCH ($(git rev-parse --short HEAD))"

if [[ $PUSH -eq 1 ]]; then
  echo "== Pushing to origin/$BRANCH (force-with-lease)..."
  git push origin "$BRANCH" --force-with-lease
else
  echo "== Not pushed. Review the commit list above, re-port anything still needed, then:"
  echo "     git push origin $BRANCH --force-with-lease"
fi

if [[ $AHEAD -gt 0 ]]; then
  echo "== Reminder: $AHEAD commit(s) from the old $BRANCH were not reapplied. Check the list above."
fi
