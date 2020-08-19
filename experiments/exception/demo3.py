#!/usr/bin/python3
try:
    raise Exception
except Exception as e:
    s, r = getattr(e, 'message', str(e)), getattr(e, 'message', repr(e))
    print('s:', s, 'len(s):', len(s))
    print('r:', r, 'len(r):', len(r))
