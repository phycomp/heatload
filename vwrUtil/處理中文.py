from re import compile as reCompile
pttrn = reCompile(r'[\u4e00-\u9fa5]+') #匹配字串中是否包含中文 \u3400 - \u4db5 CJK擴展A區
match = pttrn.search("Hello, 中文")
if match:
    print("找到中文")
