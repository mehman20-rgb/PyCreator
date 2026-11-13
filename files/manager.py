"""PyCreator layihə qovluğunda faylların idarə olunması."""
import os

class FileManager:
    def __init__(self, root):
        self.root=os.path.realpath(root)
        os.makedirs(self.root, exist_ok=True)

    def _path(self, name):
        path=os.path.realpath(os.path.join(self.root, name))
        if os.path.commonpath((self.root,path)) != self.root:
            raise ValueError("Fayl yolu layihə qovluğundan kənara çıxa bilməz.")
        return path

    def list_files(self, extension=None):
        result=[]
        for name in os.listdir(self.root):
            path=self._path(name)
            if os.path.isfile(path) and (not extension or name.lower().endswith(extension.lower())):
                result.append(name)
        return sorted(result,key=str.lower)

    def read_text(self,name):
        with open(self._path(name),"r",encoding="utf-8") as stream:
            return stream.read()

    def write_text(self,name,content):
        path=self._path(name)
        os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,"w",encoding="utf-8") as stream:
            stream.write(content)

    def delete(self,name):
        path=self._path(name)
        if not os.path.isfile(path):
            raise FileNotFoundError(name)
        os.remove(path)
