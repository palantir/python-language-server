# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, _utils

log = logging.getLogger(__name__)


@hookimpl
def pyls_signature_help(document, position):
    signatures = document.jedi_script(position).call_signatures()

    if len(signatures) == 0:
        return {'signatures': []}

    s = signatures[0]
    sig = {
        'label': s.docstring().splitlines()[0],
        'documentation': _utils.format_docstring(s.docstring(raw=True))
    }

    # If there are params, add those
    if len(s.params) > 0:
        sig['parameters'] = [{
            'label': p.name,
            # TODO: we could do smarter things here like parsing the function docstring
            'documentation': ""
        } for p in s.params]

    # We only return a single signature because Python doesn't allow overloading
    sig_info = {'signatures': [sig], 'activeSignature': 0}

    if s.index is not None and s.params:
        # Then we know which parameter we're looking at
        sig_info['activeParameter'] = s.index

    return sig_info
