# SESSION

- GitHub Pages has not deployed since 18.04.2026: every legacy Pages build
  from ff737e2 on fails ("Page build failed"), so the live site still serves
  689c89c. Cause: the `dice` submodule points at 7cad88b, which is not on
  github.com/felixmueh/dice (the API returns "No commit found"). Pushing that
  dice commit (or dropping the submodule from the Pages tree) should fix it.
  One build from 16.09.2026 is stuck in "building".
- `.gitmodules` still uses the old account URL `git@github.com:Mo0dy/dice.git`
  (works via GitHub's rename redirect; not user-visible).
- The Python suite (`python3 -m unittest tests.test_webbridge`) needs the
  `dice` submodule checked out, so it cannot run in a fresh worktree without
  `git submodule update --init`.
- No favicon: every page load logs a 404 for `/favicon.ico`.
