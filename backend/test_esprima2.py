import esprima
code = "function test() { var a = { get x() {}, dataProperty: 1, get x() {} }; }"
try:
    tree = esprima.parseScript(code, tolerant=True)
    if getattr(tree, "errors", None):
        print("Tolerant returned errors:", len(tree.errors))
        for err in tree.errors:
            print(err)
except Exception as e:
    print("Exception:", e)
