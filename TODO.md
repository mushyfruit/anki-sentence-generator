- [x] Implement context menu reibun generation.
  - Interface with Claude API.
  - Provide relevant contextual information based on existing fields.
  - Populate only the current field. Keep it simple for demo.
  - Should bold the reibun word.
  - Should allow for phrases.
  - Bold the associated english translation.

- [x] Simple pop-up to determine per deck controls for target field.
  - Auto-populates the current field as reibun field.
  - Then the rest are populated in order.
  - User dictates mapping.

- [ ] Allow for full customization of the prompt.
  - User can define the fields to return in the dialog.
  - Probably won't be necessary.
    - Start with Reibun, Translation, Additional Context
  - Pivot to a YAML based template system for prompting.

- [ ] Settings Menu?
  - Target JLPT level for auto-generation.
  - Refine the existing structure.