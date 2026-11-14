"""Simple 3D cube renderer using Kivy's Android OpenGL ES canvas."""
import math
from kivy.clock import Clock
from kivy.graphics import Color, Line, Triangle, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from tools import py3d
from ui.theme import ACCENT, MUTED, PANEL2, Btn, make_label

class ThreeDView(Widget):
    verts=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(1,5,6,2),(0,3,7,4)]
    edges=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    def __init__(self,**kw):
        super().__init__(**kw)
        self.bind(pos=self.redraw,size=self.redraw)
        self.event=Clock.schedule_interval(self.tick,1/30)
    def tick(self,dt):
        objs,rot,bg=py3d.snapshot()
        if objs and rot==(20.0,30.0,0.0): py3d.rotate(0,18*dt,0)
        self.redraw()
    def transform(self,v,rot,pos,size):
        x,y,z=[n*size*.5 for n in v]
        a,b,c=[math.radians(n) for n in rot]
        y,z=y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a)
        x,z=x*math.cos(b)+z*math.sin(b),-x*math.sin(b)+z*math.cos(b)
        x,y=x*math.cos(c)-y*math.sin(c),x*math.sin(c)+y*math.cos(c)
        return x+pos[0],y+pos[1],z+pos[2]
    def project(self,p):
        x,y,z=p
        depth=max(1.0,6.0-z)
        focal=min(self.width,self.height)*.9
        return self.center_x+x*focal/depth,self.center_y+y*focal/depth
    def redraw(self,*_):
        self.canvas.clear()
        objects,rotation,bg=py3d.snapshot()
        with self.canvas:
            Color(*bg); Rectangle(pos=self.pos,size=self.size)
            rendered=[]
            for obj in objects:
                p3=[self.transform(v,rotation,obj["position"],obj["size"]) for v in self.verts]
                for face in self.faces:
                    pts=[self.project(p3[i]) for i in face]
                    depth=sum(p3[i][2] for i in face)/4
                    rendered.append((depth,pts,obj["color"]))
            rendered.sort(key=lambda item:item[0], reverse=True)
            for depth,pts,rgb in rendered:
                shade=max(.35,min(1.0,.75+depth*.05))
                Color(*(min(1,c*shade) for c in rgb),1)
                Triangle(points=[pts[0][0],pts[0][1],pts[1][0],pts[1][1],pts[2][0],pts[2][1]])
                Triangle(points=[pts[0][0],pts[0][1],pts[2][0],pts[2][1],pts[3][0],pts[3][1]])
            # Kənarları üzlərin üstündən çək.
            for obj in objects:
                p3=[self.transform(v,rotation,obj["position"],obj["size"]) for v in self.verts]
                Color(.8,.9,1,.95)
                for a,b in self.edges:
                    p,q=self.project(p3[a]),self.project(p3[b])
                    Line(points=[p[0],p[1],q[0],q[1]],width=1.2)

class ThreeDScreen(BoxLayout):
    def __init__(self,**kw):
        super().__init__(orientation="vertical",spacing=dp(6),padding=(dp(8),dp(6)),**kw)
        self.add_widget(make_label("Android 3D Viewer · Kivy / OpenGL ES",size=15,color=MUTED,height=dp(30)))
        self.view=ThreeDView()
        self.add_widget(self.view)
        row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6))
        demo=Btn("Nümunə kub",base=ACCENT); clear=Btn("Təmizlə",base=PANEL2)
        demo.bind(on_release=lambda *_:self.load_demo())
        clear.bind(on_release=lambda *_:py3d.clear())
        row.add_widget(demo); row.add_widget(clear); self.add_widget(row)
        self.add_widget(make_label("Python: import py3d · py3d.add_cube() · py3d.set_rotation(25, 40, 0)",size=11,color=MUTED,height=dp(34)))
        self.load_demo()
    def load_demo(self):
        py3d.clear(); py3d.set_rotation(20,30,0); py3d.add_cube()
