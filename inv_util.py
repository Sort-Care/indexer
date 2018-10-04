def rshift(val, n):
    return (val % 0x100000000) >> n

def jsonKeys2int(x):
    if isinstance(x, dict):
            return {int(k):v for k,v in x.items()}
    return x
