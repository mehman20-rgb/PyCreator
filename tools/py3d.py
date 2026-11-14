"""PyCreator 3D scene API rendered by the Android Kivy canvas."""
import threading
_lock=threading.RLock()
_objects=[]
_rotation=[20.0,30.0,0.0]
_background=(0.035,0.055,0.09,1.0)

def clear():
    with _lock: _objects.clear()

def add_cube(x=0,y=0,z=0,size=2,color=(0.1,0.65,1.0)):
    if isinstance(color,str):
        color={"blue":(0.1,0.55,1),"red":(1,0.2,0.2),"green":(0.2,0.85,0.35),"yellow":(1,0.8,0.1),"purple":(0.65,0.3,1)}.get(color.lower(),(0.1,0.65,1))
    color=tuple(float(v) for v in color[:3])
    if len(color)!=3: raise ValueError("color RGB formatında olmalıdır")
    with _lock:
        _objects.append({"position":(float(x),float(y),float(z)),"size":float(size),"color":color})
        return len(_objects)

def set_rotation(x=0,y=0,z=0):
    with _lock: _rotation[:]=[float(x),float(y),float(z)]

def rotate(x=0,y=0,z=0):
    with _lock:
        _rotation[0]+=float(x); _rotation[1]+=float(y); _rotation[2]+=float(z)

def set_background(color=(0.035,0.055,0.09,1)):
    global _background
    if isinstance(color,str):
        color={"black":(0,0,0,1),"white":(1,1,1,1),"navy":(0.035,0.055,0.09,1)}.get(color.lower(),_background)
    color=tuple(float(v) for v in color)
    if len(color)==3: color+=(1.0,)
    if len(color)!=4: raise ValueError("Fon RGB və ya RGBA olmalıdır")
    with _lock: _background=color

def snapshot():
    with _lock: return ([dict(o) for o in _objects],tuple(_rotation),tuple(_background))

def show():
    return True
