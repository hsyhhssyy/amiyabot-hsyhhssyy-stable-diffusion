# StableDiffusion绘图

> 使用`兔兔绘图：A girl wearing a JK is walking along the seaside.`这样的关键词来进行绘画。

> 如果管理员开启了AI翻译，那么你可以使用中文。否则，你只能使用英文提示词，所有中文都会被忽略。

## 提示词小贴士：

### danboru tags

不管你的输入如何，StableDiffusion最终都要将其转换成逗号分隔的 `tag`
比如
```
jk, 1-girl, seaside, walking, masterpiece,best quality,ultra-detailed,best quality,high quality,newest,highres,very awa
```
因此你可以直接输入这种格式的提示词，来减少转换带来的差异。

**<span style="color:red;"> 中文逗号和英文逗号不等价，你必须使用英文逗号分隔tag </span>**

不是任何单词和句子都是合法的tag，你可以在这里：[https://danbooru.donmai.us/tags](https://danbooru.donmai.us/tags) 查找所有合法的tag的列表。

### 权重

用半角括号包含关键词，并加上冒号和数字，可以提供权重，甚至可以提供负数权重，比如：
`(seaside:1.5)` `(JK:0.5)`

### 角色和艺术家

你可以用`(艺术家的名字)`指定艺术家画风，用`(charater (ip):1)`指定角色。
你可以试试：`(amiya (arknights):1),(artist:momoko (momopoco))` 来看看momoko风格的阿米娅。

艺术家的名字，或者角色的名字，也是去上面 [https://danbooru.donmai.us/tags](https://danbooru.donmai.us/tags) 去找。

一些比较有趣的艺术家：`(momoko_(momopoco))` `(ebifurya)` `(sakimichan)` `(quan (kurisu tina))` `(moriyama shijimi)` `(kase daiki)` `(as109)`

一般来说，画风独特，并且作品量大的画师，AI会学习的更好。尤其推荐`(quan (kurisu tina))`,特别容易出图。

### 多输入一点提示词

提示词越少，画面就越空洞，产生的bug越多，越容易有ai味。
想要消除AI味，首先要挑一个好艺术家，此外最好多输入一点关键词。

### 提示词不应包含下划线

网上流传的用下划线替代空格的说法是错误的，下划线会破坏提示词，请不要使用任何下划线，请将其替换为空格。