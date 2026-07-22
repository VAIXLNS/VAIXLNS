/**
 * Deterministic subproject lookup for VX URL handlers.
 *
 * Identifiers are compared exactly. Decoding and route parsing belong at the
 * HTTP boundary so this resolver cannot accidentally double-decode `%2F` or
 * make case-folding decisions that differ between endpoints.
 */

export class SubprojectNotFoundError extends Error {
  constructor(parentId, identifier) {
    super(`Subproject ${JSON.stringify(identifier)} was not found under parent ${JSON.stringify(parentId)}`);
    this.name = "SubprojectNotFoundError";
    this.code = "SUBPROJECT_NOT_FOUND";
  }
}

export class AmbiguousSubprojectIdentifierError extends Error {
  constructor(parentId, identifier, matchedBy) {
    super(`Multiple subprojects match ${matchedBy} ${JSON.stringify(identifier)} under parent ${JSON.stringify(parentId)}`);
    this.name = "AmbiguousSubprojectIdentifierError";
    this.code = "AMBIGUOUS_SUBPROJECT_IDENTIFIER";
    this.matchedBy = matchedBy;
  }
}

export class InvalidSubprojectLookupError extends TypeError {
  constructor(field) {
    super(`${field} must be a non-empty string`);
    this.name = "InvalidSubprojectLookupError";
    this.code = "INVALID_SUBPROJECT_LOOKUP";
    this.field = field;
  }
}

function requireIdentifier(value, field) {
  if (typeof value !== "string" || value.length === 0) {
    throw new InvalidSubprojectLookupError(field);
  }
}

function selectUnique(matches, parentId, identifier, matchedBy) {
  if (matches.length > 1) {
    throw new AmbiguousSubprojectIdentifierError(parentId, identifier, matchedBy);
  }
  return matches[0];
}

/**
 * @typedef {object} Subproject
 * @property {string} id
 * @property {string} parentId
 * @property {string} slug
 * @property {string | null | undefined} [alias]
 */

/**
 * @param {object} options
 * @param {string} options.parentId
 * @param {string} options.identifier
 * @param {readonly Subproject[]} options.subprojects
 * @param {boolean} [options.legacyAliasFallback=false]
 * @param {(event: {parentId: string, identifier: string, subprojectId: string, canonicalSlug: string}) => void} [options.onLegacyAliasMatch]
 * @returns {{subproject: Subproject, matchedBy: "slug" | "alias", canonicalSlug: string}}
 */
export function resolveSubproject({
  parentId,
  identifier,
  subprojects,
  legacyAliasFallback = false,
  onLegacyAliasMatch,
}) {
  requireIdentifier(parentId, "parentId");
  requireIdentifier(identifier, "identifier");
  if (!Array.isArray(subprojects)) {
    throw new TypeError("subprojects must be an array");
  }

  const siblings = subprojects.filter((subproject) => subproject.parentId === parentId);

  const slugMatch = selectUnique(
    siblings.filter((subproject) => subproject.slug === identifier),
    parentId,
    identifier,
    "slug",
  );

  if (slugMatch) {
    return { subproject: slugMatch, matchedBy: "slug", canonicalSlug: slugMatch.slug };
  }

  if (!legacyAliasFallback) {
    throw new SubprojectNotFoundError(parentId, identifier);
  }

  const aliasMatch = selectUnique(
    siblings.filter((subproject) => subproject.alias === identifier),
    parentId,
    identifier,
    "alias",
  );

  if (!aliasMatch) {
    throw new SubprojectNotFoundError(parentId, identifier);
  }

  onLegacyAliasMatch?.({
    parentId,
    identifier,
    subprojectId: aliasMatch.id,
    canonicalSlug: aliasMatch.slug,
  });

  return { subproject: aliasMatch, matchedBy: "alias", canonicalSlug: aliasMatch.slug };
}

/**
 * Builds a parent-scoped cache key using the canonical slug.
 */
export function subprojectCacheKey(parentId, canonicalSlug) {
  requireIdentifier(parentId, "parentId");
  requireIdentifier(canonicalSlug, "canonicalSlug");
  return JSON.stringify(["subproject", parentId, canonicalSlug]);
}
