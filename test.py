import re

reg = "^(?!.*artist:[^,]+,)(?!.*artist:[^,]+$).*"
text = "芙宁娜在远处向我招手(furina_(genshin impact:1))"
rep = "\\g<0>, artist:momoko_(momopoco)"
st = re.sub(reg,rep,text)
print(st)