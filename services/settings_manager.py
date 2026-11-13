"""Tətbiq parametrlərinin JSON faylında saxlanması."""
import json
import os

DEFAULTS={"theme":"dark","font_size":14,"autosave":True}


class SettingsManager:
    def __init__(self,path):
        self.path=path

    def load(self):
        try:
            with open(self.path,"r",encoding="utf-8") as stream:
                saved=json.load(stream)
            result=dict(DEFAULTS)
            if isinstance(saved,dict):
                result.update(saved)
            return result
        except (OSError,ValueError,TypeError):
            return dict(DEFAULTS)

    def update(self,values):
        current=self.load()
        current.update(values)
        os.makedirs(os.path.dirname(os.path.abspath(self.path)),exist_ok=True)
        temporary=self.path+".tmp"
        with open(temporary,"w",encoding="utf-8") as stream:
            json.dump(current,stream,ensure_ascii=False,indent=2)
        os.replace(temporary,self.path)
        return current
