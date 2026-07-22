import assert from "node:assert/strict";
import test from "node:test";

import {
  AmbiguousSubprojectIdentifierError,
  InvalidSubprojectLookupError,
  SubprojectNotFoundError,
  resolveSubproject,
  subprojectCacheKey,
} from "../src/resolve-subproject.js";

const projects = [
  { id: "one", parentId: "parent-a", slug: "docs", alias: "guide" },
  { id: "two", parentId: "parent-a", slug: "guide", alias: "old-guide" },
  { id: "three", parentId: "parent-b", slug: "docs", alias: "guide" },
];

test("resolves an exact slug without legacy fallback", () => {
  const result = resolveSubproject({ parentId: "parent-a", identifier: "docs", subprojects: projects });
  assert.equal(result.subproject.id, "one");
  assert.equal(result.matchedBy, "slug");
  assert.equal(result.canonicalSlug, "docs");
});

test("slug wins when it collides with another subproject alias", () => {
  const result = resolveSubproject({
    parentId: "parent-a",
    identifier: "guide",
    subprojects: projects,
    legacyAliasFallback: true,
  });
  assert.equal(result.subproject.id, "two");
  assert.equal(result.matchedBy, "slug");
});

test("legacy alias is rejected when fallback is disabled", () => {
  assert.throws(
    () => resolveSubproject({ parentId: "parent-a", identifier: "old-guide", subprojects: projects }),
    SubprojectNotFoundError,
  );
});

test("legacy alias resolves and emits telemetry when fallback is enabled", () => {
  const events = [];
  const result = resolveSubproject({
    parentId: "parent-a",
    identifier: "old-guide",
    subprojects: projects,
    legacyAliasFallback: true,
    onLegacyAliasMatch: (event) => events.push(event),
  });

  assert.equal(result.subproject.id, "two");
  assert.equal(result.matchedBy, "alias");
  assert.equal(result.canonicalSlug, "guide");
  assert.deepEqual(events, [{
    parentId: "parent-a",
    identifier: "old-guide",
    subprojectId: "two",
    canonicalSlug: "guide",
  }]);
});

test("never crosses a parent boundary", () => {
  assert.throws(
    () => resolveSubproject({
      parentId: "parent-c",
      identifier: "guide",
      subprojects: projects,
      legacyAliasFallback: true,
    }),
    SubprojectNotFoundError,
  );
});

test("matches slash aliases exactly without normalizing or partially matching", () => {
  const nested = [{ id: "nested", parentId: "parent-a", slug: "nested-docs", alias: "team/docs" }];
  const result = resolveSubproject({
    parentId: "parent-a",
    identifier: "team/docs",
    subprojects: nested,
    legacyAliasFallback: true,
  });
  assert.equal(result.subproject.id, "nested");
  assert.throws(
    () => resolveSubproject({
      parentId: "parent-a",
      identifier: "docs",
      subprojects: nested,
      legacyAliasFallback: true,
    }),
    SubprojectNotFoundError,
  );
});

test("does not double-decode encoded slashes", () => {
  const encoded = [{ id: "encoded", parentId: "parent-a", slug: "encoded", alias: "team%2Fdocs" }];
  assert.equal(resolveSubproject({
    parentId: "parent-a",
    identifier: "team%2Fdocs",
    subprojects: encoded,
    legacyAliasFallback: true,
  }).subproject.id, "encoded");
  assert.throws(
    () => resolveSubproject({
      parentId: "parent-a",
      identifier: "team/docs",
      subprojects: encoded,
      legacyAliasFallback: true,
    }),
    SubprojectNotFoundError,
  );
});

test("uses exact case-sensitive Unicode matching", () => {
  const unicode = [{ id: "arabic", parentId: "parent-a", slug: "دليل", alias: "الدليل" }];
  assert.equal(resolveSubproject({
    parentId: "parent-a",
    identifier: "دليل",
    subprojects: unicode,
  }).subproject.id, "arabic");
  assert.throws(
    () => resolveSubproject({ parentId: "parent-a", identifier: "دَلِيل", subprojects: unicode }),
    SubprojectNotFoundError,
  );
});

test("fails closed for duplicate slugs and duplicate aliases", () => {
  const duplicateSlug = [
    { id: "a", parentId: "parent-a", slug: "same", alias: "a" },
    { id: "b", parentId: "parent-a", slug: "same", alias: "b" },
  ];
  assert.throws(
    () => resolveSubproject({ parentId: "parent-a", identifier: "same", subprojects: duplicateSlug }),
    AmbiguousSubprojectIdentifierError,
  );

  const duplicateAlias = [
    { id: "a", parentId: "parent-a", slug: "a", alias: "same" },
    { id: "b", parentId: "parent-a", slug: "b", alias: "same" },
  ];
  assert.throws(
    () => resolveSubproject({
      parentId: "parent-a",
      identifier: "same",
      subprojects: duplicateAlias,
      legacyAliasFallback: true,
    }),
    AmbiguousSubprojectIdentifierError,
  );
});

test("rejects empty lookup fields", () => {
  assert.throws(
    () => resolveSubproject({ parentId: "", identifier: "docs", subprojects: projects }),
    InvalidSubprojectLookupError,
  );
  assert.throws(
    () => resolveSubproject({ parentId: "parent-a", identifier: "", subprojects: projects }),
    InvalidSubprojectLookupError,
  );
});

test("cache keys are canonical and parent-scoped", () => {
  assert.notEqual(subprojectCacheKey("parent-a", "docs"), subprojectCacheKey("parent-b", "docs"));
  assert.equal(subprojectCacheKey("parent-a", "docs"), '["subproject","parent-a","docs"]');
});
