// REPLACED BY sense-rtmon. This is not the upstream file.
//
// Upstream ships a generated catalogue of roughly 160 KB of third-party brand
// logos (Simple Icons 16.28.0, plus an OpenAI mark). Those vector paths carry
// their own licences independent of Archify's MIT licence, and per upstream's
// THIRD_PARTY_NOTICES.md they include CC-BY-NC-SA-4.0 (Vue.js), CC-BY-SA-4.0
// (Rust), CC-BY-SA-3.0 (Jenkins) and CC-BY-4.0 (Angular) material, alongside
// trademarked marks used under brand guidelines.
//
// RTMon draws network topologies from a SENSE-O manifest and never sets a
// `brand` field on a component, so none of those marks can appear in a
// generated diagram. Vendoring the catalogue would have redistributed
// NonCommercial and ShareAlike licensed artwork through this repository and
// every RTMon container image in exchange for nothing.
//
// Emptied rather than deleted: brand-marks.mjs imports BRAND_MARKS from here,
// and Archify's MIT licence expressly permits modification. An empty catalogue
// makes findBrandMark() resolve nothing, which is the outcome RTMon already
// gets by never asking for a mark.
//
// If brand marks are ever wanted, re-vendor this file from upstream and clear
// the individual licences first - the NonCommercial one in particular. See
// autogole-api/vendor/README.md.
export const BRAND_MARKS = Object.freeze([]);
