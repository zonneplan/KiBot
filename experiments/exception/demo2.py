###########
# Python 2:
###########
try:
    raise Exception
except Exception as e:
    s, r = getattr(e, 'message') or str(e), getattr(e, 'message') or repr(e)
    print 's:', s, 'len(s):', len(s)   # noqa: E999
    print 'r:', r, 'len(r):', len(r)   # noqa: E999
