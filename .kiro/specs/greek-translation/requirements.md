# Requirements Document

## Introduction

Add Greek (el) as a fourth language to the Learn Claude Code workshop. The project currently supports English (en), Japanese (ja), and Chinese (zh) across three translation surfaces: markdown documentation files in `docs/`, root-level README files, and the Next.js web application (i18n messages, locale routing, and content extraction). This feature brings full Greek parity with the existing languages.

## Glossary

- **Workshop**: The Learn Claude Code repository, including agents, documentation, and the web platform
- **Web_App**: The Next.js interactive learning platform located in `web/`
- **Docs_Directory**: The `docs/` folder containing per-locale subdirectories with session markdown files (s01–s12)
- **I18n_Messages**: JSON translation files in `web/src/i18n/messages/` that provide UI string translations for the Web_App
- **Locale_Router**: The `[locale]` dynamic route segment in `web/src/app/[locale]/` that serves locale-specific pages
- **Content_Extractor**: The `web/scripts/extract-content.ts` script that reads docs from locale subdirectories and generates `docs.json`
- **Language_Switcher**: The UI component in the header that allows users to switch between available locales
- **README_File**: A root-level markdown file providing the project overview in a specific language

## Requirements

### Requirement 1: Greek Documentation Files

**User Story:** As a Greek-speaking learner, I want to read the workshop documentation in Greek, so that I can understand each session's concepts in my native language.

#### Acceptance Criteria

1. THE Docs_Directory SHALL contain a `docs/el/` subdirectory with 12 Greek-translated markdown files (s01 through s12), matching the filenames in `docs/en/`
2. WHEN a Greek documentation file is loaded, THE file SHALL preserve the same heading structure, code blocks, and ASCII diagrams as the corresponding English source file
3. THE Greek documentation files SHALL translate all prose content (headings, explanations, mottos) into Greek while keeping code snippets, variable names, and terminal commands in their original form


### Requirement 2: Greek README

**User Story:** As a Greek-speaking visitor, I want a Greek version of the project README, so that I can understand the project overview and get started without needing English.

#### Acceptance Criteria

1. THE Workshop SHALL include a `README-el.md` file at the repository root containing a Greek translation of the main README content
2. THE README-el.md file SHALL preserve all code blocks, architecture diagrams, and command examples from the English README in their original form
3. WHEN the Greek README is created, THE language selector line at the top of every README file (README.md, README-ja.md, README-zh.md, README-el.md) SHALL include a link to the Greek README with the label `Ελληνικά`

### Requirement 3: Greek I18n Messages for the Web App

**User Story:** As a Greek-speaking user of the web platform, I want all UI labels, navigation items, and descriptive text displayed in Greek, so that I can navigate and use the interactive learning platform in my language.

#### Acceptance Criteria

1. THE I18n_Messages SHALL include a `web/src/i18n/messages/el.json` file containing Greek translations for all keys present in `en.json`
2. THE el.json file SHALL maintain the same JSON structure and key names as en.json, with only the string values translated into Greek
3. WHEN a translation key is missing from el.json, THE Web_App SHALL fall back to the English value for that key

### Requirement 4: Locale Registration in the Web App

**User Story:** As a Greek-speaking user, I want the web application to recognize Greek as a valid locale, so that I can access the platform at the `/el` URL path.

#### Acceptance Criteria

1. THE Locale_Router SHALL include `"el"` in the `locales` array in `web/src/app/[locale]/layout.tsx` so that `generateStaticParams` generates the Greek locale route
2. THE Locale_Router SHALL import the Greek message file and include it in the `metaMessages` map in `web/src/app/[locale]/layout.tsx`
3. THE Web_App SHALL import the Greek message file and register it in the `messagesMap` in both `web/src/lib/i18n.tsx` and `web/src/lib/i18n-server.ts`

### Requirement 5: Language Switcher Update

**User Story:** As a user browsing the web platform, I want to see Greek as an option in the language switcher, so that I can switch to the Greek version of the site.

#### Acceptance Criteria

1. THE Language_Switcher SHALL include a Greek option with code `"el"` and label `"Ελληνικά"` in the `LOCALES` array in `web/src/components/layout/header.tsx`
2. WHEN a user clicks the Greek option in the Language_Switcher, THE Web_App SHALL navigate to the equivalent page under the `/el` locale path

### Requirement 6: Content Extraction Pipeline Update

**User Story:** As a developer building the web platform, I want the content extraction script to process Greek documentation, so that Greek docs appear in the generated data used by the web app.

#### Acceptance Criteria

1. THE Content_Extractor SHALL include `"el"` in the `localeDirs` array in `web/scripts/extract-content.ts`
2. THE Content_Extractor SHALL detect the `"el"` locale from doc file paths under `docs/el/`
3. WHEN the Content_Extractor runs, THE generated `docs.json` SHALL contain entries with `locale: "el"` for each Greek documentation file

### Requirement 7: TypeScript Type Update for Greek Locale

**User Story:** As a developer, I want the TypeScript types to include Greek as a valid locale, so that the codebase remains type-safe after adding the new language.

#### Acceptance Criteria

1. THE `DocContent` interface in `web/src/types/agent-data.ts` SHALL include `"el"` in the `locale` union type
2. THE `detectLocale` function in `web/scripts/extract-content.ts` SHALL return `"el"` for paths starting with `el/`
