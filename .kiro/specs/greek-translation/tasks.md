# Implementation Plan: Greek Translation

## Overview

Add Greek (el) as a fourth locale to the Learn Claude Code workshop by following the existing ja/zh translation pattern. All changes are additive: new files for docs/README/i18n messages, and small insertions into existing arrays, maps, and union types in the web app.

## Tasks

- [ ] 1. Create Greek documentation files
  - [x] 1.1 Create `docs/el/` directory and add Greek translations of all 12 session markdown files (s01 through s12)
    - Copy each file from `docs/en/` and translate all prose content (headings, explanations, mottos) into Greek
    - Preserve heading structure, code blocks, ASCII diagrams, variable names, and terminal commands exactly as-is
    - Files: `docs/el/s01-the-agent-loop.md` through `docs/el/s12-worktree-task-isolation.md`
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Create Greek README and update language selector
  - [x] 2.1 Create `README-el.md` at the repository root with a Greek translation of `README.md`
    - Translate prose content into Greek while preserving all code blocks, architecture diagrams, and command examples
    - Include the updated language selector line at the top: `[English](./README.md) | [中文](./README-zh.md) | [日本語](./README-ja.md) | [Ελληνικά](./README-el.md)`
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Update the language selector line in `README.md`, `README-ja.md`, and `README-zh.md`
    - Add `[Ελληνικά](./README-el.md)` link to the existing language selector line in each file
    - _Requirements: 2.3_

- [ ] 3. Create Greek i18n messages file
  - [x] 3.1 Create `web/src/i18n/messages/el.json` with Greek translations of all UI strings
    - Copy the structure and keys from `en.json` and translate all string values into Greek
    - Maintain the same JSON structure and all top-level namespaces: `meta`, `nav`, `home`, `version`, `sim`, `timeline`, `layers`, `compare`, `diff`, `sessions`, `layer_labels`, `viz`
    - _Requirements: 3.1, 3.2_

- [ ] 4. Register Greek locale in the web app
  - [x] 4.1 Update `web/src/app/[locale]/layout.tsx` to register the Greek locale
    - Add `import el from "@/i18n/messages/el.json";`
    - Add `"el"` to the `locales` array
    - Add `el` to the `metaMessages` map
    - _Requirements: 4.1, 4.2_

  - [x] 4.2 Update `web/src/lib/i18n.tsx` to include Greek messages
    - Add `import el from "@/i18n/messages/el.json";`
    - Add `el` to the `messagesMap` object
    - _Requirements: 4.3_

  - [x] 4.3 Update `web/src/lib/i18n-server.ts` to include Greek messages
    - Add `import el from "@/i18n/messages/el.json";`
    - Add `el` to the `messagesMap` object
    - _Requirements: 4.3_

- [ ] 5. Update language switcher
  - [x] 5.1 Add Greek option to the `LOCALES` array in `web/src/components/layout/header.tsx`
    - Add `{ code: "el", label: "Ελληνικά" }` to the `LOCALES` array
    - The existing `switchLocale` function handles navigation automatically
    - _Requirements: 5.1, 5.2_

- [ ] 6. Update content extraction pipeline and TypeScript types
  - [x] 6.1 Update `web/src/types/agent-data.ts` to include Greek in the locale union type
    - Change `locale: "en" | "zh" | "ja"` to `locale: "en" | "zh" | "ja" | "el"` in the `DocContent` interface
    - _Requirements: 7.1_

  - [x] 6.2 Update `web/scripts/extract-content.ts` to process Greek docs
    - Add `"el"` to the `localeDirs` array
    - Add an `el` branch to the `detectLocale` function: `if (relPath.startsWith("el/") || relPath.startsWith("el\\")) return "el";`
    - Update the `detectLocale` return type to `"en" | "zh" | "ja" | "el"`
    - Update the locale type cast in the docs loop to include `"el"`
    - _Requirements: 6.1, 6.2, 6.3, 7.2_

- [ ] 7. Checkpoint - Verify build and integration
  - Ensure all tests pass, ask the user if questions arise.
  - Verify the web app builds successfully with `npm run build` in the `web/` directory
  - Confirm `docs/el/` contains all 12 files, `el.json` is valid JSON, and all locale registrations are in place

## Notes

- All changes follow the exact pattern established by the Japanese (ja) and Chinese (zh) translations
- No new infrastructure, config files, or build steps are needed
- English fallback for missing keys is already handled by the existing `messagesMap[locale] || en` pattern
- Each task references specific requirements for traceability
