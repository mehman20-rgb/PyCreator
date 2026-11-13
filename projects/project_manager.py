"""PyCreator layihə qovluqlarının idarə olunması."""
import os
import re


class ProjectManager:
    def __init__(self, root):
        self.root=os.path.realpath(root)
        os.makedirs(self.root,exist_ok=True)

    def _path(self,name):
        safe=re.sub(r"[^A-Za-z0-9_.-]+","_",name.strip()).strip("._")
        if not safe:
            raise ValueError("Layihə adı boş ola bilməz.")
        path=os.path.realpath(os.path.join(self.root,safe))
        if os.path.commonpath((self.root,path))!=self.root:
            raise ValueError("Etibarsız layihə yolu.")
        return path

    def list_projects(self):
        return sorted(name for name in os.listdir(self.root)
                      if os.path.isdir(os.path.join(self.root,name)))

    def create(self,name):
        path=self._path(name)
        os.makedirs(path,exist_ok=False)
        with open(os.path.join(path,"main.py"),"w",encoding="utf-8") as stream:
            stream.write('print("Salam, dünya!")\n')
        return path
