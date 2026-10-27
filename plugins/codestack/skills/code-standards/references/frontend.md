# Frontend shared conventions

Apply to affected user-visible copy in a frontend product that already supports
multiple languages or is explicitly required to do so. These conventions apply
across JavaScript/TypeScript and frameworks such as React and Vue; they are not
general language or framework style rules. Single-language products and changes
unrelated to copy do not acquire an internationalization requirement.

## Centralize multilingual copy

- Keep fixed user-visible copy in a dedicated, centrally maintained language-resource
  area for the current product/application. Pages, components, hooks, composables
  and actions reference resource keys through the project's existing localization
  mechanism. Do not hardcode translatable copy in these implementations, scatter
  per-component or per-action language dictionaries, or choose translated literals
  with inline locale branches. Wrapping a scattered dictionary in a lookup helper
  does not give it a central resource owner.
- Resources may be split by language, business domain or namespace and loaded
  lazily within the unified resource area. Follow existing resource ownership;
  do not require a particular directory name, file format, library or giant file,
  or merge independent applications' resources merely because they share a repository.
- Include page text, buttons, form labels, placeholders, accessible labels and
  descriptions, dialogs, validation errors, and success/failure feedback such as
  toasts. A message produced by an action or validation path is still user-visible
  copy even when it is not written in a component template.
- Keep complete interpolated messages in the resource area. Pass names, email
  addresses and other dynamic values through the existing interpolation mechanism;
  do not assemble translated sentence fragments in business logic. Preserve the
  product's locale-switching, fallback and interpolation behavior.
- User-authored or externally supplied business content remains data. Identifiers,
  protocol values, state tags and logs are not translation targets. Fixed local
  labels, fallbacks and message templates surrounding that data remain resources.
- Apply this convention within the authorized change or review scope. Reuse the
  existing resource area when adding copy; creating a separate dictionary beside
  each new feature is not centralization. Do not install a new library or migrate
  unrelated historical text just to match an example.

This is CodeStack's explicit resource-organization convention, not a claim that
every frontend framework requires this arrangement. Functional language switching
does not by itself prove that messages have a central owner; inspect the actual
definitions and the keys used by affected rendering and feedback paths.
