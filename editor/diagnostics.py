"""Python mənbə kodu üçün sintaksis diaqnostikası."""
def check_syntax(source, filename="<pycreator>"):
    try:
        compile(source, filename, "exec")
    except SyntaxError as error:
        return {"ok":False,"message":error.msg,"line":error.lineno,
                "column":error.offset,"text":error.text}
    return {"ok":True,"message":"","line":None,"column":None,"text":None}
