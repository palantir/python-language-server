# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, uris, _utils

log = logging.getLogger(__name__)


@hookimpl
def pyls_definitions(config, document, position, kedro_context):
    settings = config.plugin_settings("jedi_definition")
    code_position = _utils.position_to_jedi_linecolumn(document, position)
    # TODO: make sure we are in a node definition and it's a catalog name
    try:
        dataset_name = document.word_at_position(position)
        config_loader = kedro_context.config_loader
        config_loader.get("catalog*", "catalog*/**", "**/catalog*")
        line_number, config_file = config_loader.line_numbers.get(dataset_name, [0, 0])
    except Exception as e:
        log.info(f"😭 {e}")
        line_number, config_file = None, None

    if not line_number or not config_file:
        definitions = document.jedi_script().goto(
            follow_imports=settings.get("follow_imports", True),
            follow_builtin_imports=settings.get("follow_builtin_imports", True),
            **code_position,
        )
        return [
            {
                "uri": uris.uri_with(document.uri, path=str(d.module_path)),
                "range": {
                    "start": {"line": d.line - 1, "character": d.column},
                    "end": {"line": d.line - 1, "character": d.column + len(d.name)},
                },
            }
            for d in definitions
            if d.is_definition() and _not_internal_definition(d)
        ]

    return [
        {
            "uri": uris.uri_with(document.uri, path=str(config_file)),
            "range": {
                "start": {"line": line_number, "character": 0},
                "end": {"line": line_number, "character": 1},
            },
        }
    ]


def _not_internal_definition(definition):
    return (
        definition.line is not None
        and definition.column is not None
        and definition.module_path is not None
        and not definition.in_builtin_module()
    )
