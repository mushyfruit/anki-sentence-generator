class NoteConfig:
    FIELDS = "field_mappings"
    CONTEXT = "context"
    DIFFICULTY = "difficulty"


class ConfigKeys:
    DIFFICULTY_OPTIONS = "difficulty_options"
    DEFAULT_DIFFICULTY = "default_difficulty"
    CONTEXT_OPTIONS = "context_options"
    DEFAULT_CONTEXT = "default_context"

    allowed_keys = [
        DIFFICULTY_OPTIONS,
        CONTEXT_OPTIONS,
        DEFAULT_CONTEXT,
        DEFAULT_DIFFICULTY,
    ]


class ResponseFields:
    SENTENCE = "sentence"
    READING = "reading"
    TRANSLATION = "translation"
    NOTES = "notes"

    required_fields = [SENTENCE, READING, TRANSLATION, NOTES]
    multi_fields = {NOTES}
