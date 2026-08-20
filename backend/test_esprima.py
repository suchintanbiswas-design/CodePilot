import esprima
code = "var x = ;\nconst y = 2"
try:
    tree = esprima.parseScript(code, tolerant=True)
    if getattr(tree, "errors", None):
        for err in tree.errors:
            print("Error:", err.lineNumber, err.description)
    else:
        print("Success, no errors.")
except Exception as e:
    print("Caught exception:", e)
