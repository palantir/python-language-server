from pyls import hookimpl
from .jedi_completion import pyls_jedi_completions
from .rope_completion import pyls_rope_completions


@hookimpl
def pyls_settings():
    return {'plugins': {'completion': {'provider': 'jedi'}}}


@hookimpl
def pyls_completions(config, document, position):
    provider = config.plugin_settings('completion').get('provider', 'jedi')
    if provider == 'jedi':
        return pyls_jedi_completions(document, position)
    elif provider == 'rope':
        return pyls_rope_completions(document, position)
    return []
