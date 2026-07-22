# VX subproject routing

This dependency-free module implements the URL identifier policy recorded in
VAIXLNS issue #4.

## Contract

- A subproject slug is its canonical URL identifier.
- Lookup is scoped to the requested parent project.
- Exact slug matching always happens first.
- Exact alias matching is available only when `legacyAliasFallback` is enabled.
- An alias can never shadow a slug.
- Ambiguous stored data fails closed instead of selecting an arbitrary project.
- Matching is exact: the HTTP boundary owns percent-decoding, Unicode policy,
  trailing-slash handling, and route parsing.

## Example

```js
import { resolveSubproject } from "./src/resolve-subproject.js";

const result = resolveSubproject({
  parentId: "parent-1",
  identifier: "legacy/name",
  subprojects,
  legacyAliasFallback: parent.features.legacySubprojectAliases,
  onLegacyAliasMatch: (event) => metrics.increment("subproject.alias_fallback", event),
});

// Redirect-capable handlers may use this to construct the canonical URL.
console.log(result.canonicalSlug);
```

## Integration requirements

API, download, and page-redirect handlers should call the same resolver. The
router must decode the path once, then pass the resulting identifier unchanged.
Authorization must run on the resolved subproject exactly as it does today.

Run the verification suite with:

```sh
npm test
```
