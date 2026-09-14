import time

def proc_data(d, f1, f2, m, o, t, x, y):
    if d is not None:
        if len(d) > 0:
            if f1 == True:
                r = []
                for i in d:
                    if i.get('status') == 1:
                        if i.get('val') > m:
                            if t == 'a':
                                r.append(i.get('val') * x)
                            elif t == 'b':
                                r.append(i.get('val') * y)
                            else:
                                if o == True:
                                    r.append(i.get('val') + x)
                                else:
                                    r.append(i.get('val') - y)
                        else:
                            if f2 == True:
                                if t == 'a':
                                    r.append(i.get('val') / x if x != 0 else 0)
                                else:
                                    r.append(0)
            else:
                r = []
                for i in d:
                    if i.get('status') == 2:
                        if i.get('val') < m:
                            r.append(i.get('val'))
                        else:
                            if o == True:
                                r.append(m)
        else:
            return None
    else:
        return []
        
    s = 0
    for v in r:
        if v > 0:
            if v < 100:
                s += v
            else:
                if v < 1000:
                    s += (v * 0.9)
                else:
                    if o == True:
                        s += (v * 0.8)
                    else:
                        s += (v * 0.75)
    
    return s
