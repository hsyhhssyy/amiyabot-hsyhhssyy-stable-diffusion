# StableDiffusion绘图

插件全新重做！

不再进行深度加工，而是单纯提供一个调用StableDiffusion WebUI的兔兔功能。

**提示**：使用本功能前，请确保你已经在本地部署了StableDiffuion。不清楚如何部署？推荐参考B站大佬秋叶akki的教程: https://www.bilibili.com/video/BV1iM4y1y7oA。

**进阶提示**：推荐使用NoobAI-XL（V-预测），[https://d0xb9r3fg5h.feishu.cn/docx/WWOHdr6RMoQZxQxCZRGc5KlEnUi](https://d0xb9r3fg5h.feishu.cn/docx/WWOHdr6RMoQZxQxCZRGc5KlEnUi) ，本插件附带的默认配置文件，是经过调整完美适配NoobAI-XL（V-预测）的配置文件。如果你使用其他模型，或者不使用V-预测，请不要使用默认值，而是修改配置文件。

## 绘图命令

每个群内用户，可以使用`兔兔绘图：A girl wearing a JK is walking along the seaside.`这样的关键词来进行绘画。

> 不开启AI翻译的话，默认StableDiffusion是仅支持英文的，因此插件会将所有中文裁切掉，以防干扰模型。

## 绘图队列

目前版本下，当兔兔有绘图任务时，会将其他新任务排队。
队列总长度可由配置项设置，所有群共用。
每个群最大队列长度为总长度的一半。

## 安装要求

1. **<span style="color:red;"> 兔兔版本大于6.3.9</span>**

2. **<span style="color:red;"> 已经部署且可运行的StableDiffusionWebUI</span>**

## 安装与配置

刚装好插件后，插件什么都做不了，你需要跟着下面这几步去执行初始化配置。

### 配置webui地址

* 打开您的webui。
* 滚动至页面最下方，点击API链接。

![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-2.png)

* 将新页面的地址复制，并粘贴至Docs Url配置项。

> 注：本插件暂不支持WebUI登录认证，你的WebUI地址必须可以匿名访问。WebUI自带的认证功能会在未来版本支持。如果你使用其他互联网服务商提供的网络部署服务，并且拥有独特的认证方式，请到GitHub提交Issue申请支持。

### 等待连接

稍等30秒，如果WebUI可以连接，你会在兔兔日志中看到诸如下面这样的提示信息。

```log

2023-10-10 12:47:13,844 [StableDiffusion][     INFO] 因docs变化而重载WebUIApi...
2023-10-10 12:47:13,918 [StableDiffusion][     INFO] WebUIApi刷新完毕...

```

此时已经连上了WebUI Api。

### 修改模型

接下来，请刷新兔兔Console，从而让插件配置项重载。

然后在插件配置项的 默认模型-> 模型 中选择一个模型。

> 注：如果你使用NoobAI-XL，请在这里选择NoobAI-XL对应的模型。

然后，选择一个采样器。

> 注：如果你使用NoobAI-XL，NoobAI-XL对采样器有严格要求，请根据你的NoobAI版本，在文档中找到合适的采样器，一般是Euler或者Euler A

再然后，选择一个vae

> 注：如果你使用NoobAI-XL，NoobAI要求不使用vae，请选择 `...`

现在，你可以开始绘图了

## 其他配置

你需要根据你的SD中的模型，调整下面的配置。
（或者如果你使用NoobAI-XL，那么你可以使用默认配置）

### 正则表达式

可以通过正则表达式对提示词进行一定的预处理。

比如可以配置表达式为`\(op:(\w+)\)`，替换为 `(\1_(arknights:1))`，这样就可以人工制造一个新指令：(干员:amiya) ，并使其产生特殊提示词。

或者使用负向断言表达`^(?!.*artist:[^,]+,)(?!.*artist:[^,]+$).*`，替换为`\g<0>, artist:momoko_(momopoco)`，这样就可以在提示词不包含artist的时候，添加一个artist tag。

### 自定义提示

可以添加一些你的随机小提示，比如：

`在提示词中添加“(amiya (arknights))”这样的词(只能用英文)，可以绘制泰拉上朋友们的图片哦。`

### 额外参数

可以通过这个字段提供一些额外的Json参数。控制SD使用HighRes等功能。
这个配置项接受一个json字符串。字符串的key是参数名，value是参数值。
具体可以去你的SD的docs中，查找 /sdapi/v1/txt2img 这个 api的介绍。

例如，你可以添加下面这段自定义参数，来使用HighRes:

```json
{
    "enable_hr":true,
    "hr_upscaler":"SwinIR_4x",
    "hr_second_pass_steps":10,
    "denoising_strength":0.3
}
```

或者调节SD的生成参数，如：
```json
{
    "steps": 35,
    "cfg_scale": 3.5
}
```

## AI翻译

因为源生SD只能使用英文，因此你可以选择使用AI翻译。如果你安装了大语言模型库，那么你可以选择一个模型，这样插件会先用这个AI模型，将用户的输入翻译为英文并拆解为danboru tag。
或者选择“不使用”以关闭。
注意，你选择的这个ai不能太笨，不然可能会破坏原有输入的tag，反而还不如手动翻译。

## 版权声明

SD WebUI 使用AGPL版权。AGPL是一个强限制的开源协议，访问任何使用AGPL协议的网络服务的代码也需要开源。因此，本项目同样遵循AGPL版权。任何使用该服务的人或修改该服务的人也必须提供源代码。

注意：AGPL相比于GPL，增加了对通过服务访问的限制，也就是说，你将本项目部署为服务，然后用其他软件去调用它，那么其他软件可能也需要开源。

## 法律风险

**StableDiffusion不带道德校验模块，兔兔可能会产生色情，暴力，反动，版权侵害等违法行为。**
**兔兔运营方应当关注兔兔的生成内容并及时处理，出现任何法律责任，本项目概不负责。**

## 帮助更小白的用户

- 完善文档，这篇文档写的非常简略，对于没有StableDiffusion经验的人来说可能会比较困难，同时还缺少一些步骤的截图。如果您有兴趣帮忙修改文档，您可以直接在Github提出PR。

## 备注

* 插件图标是使用StableDiffusion生成的。

## 相关链接

[项目地址:Github](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/)

[遇到问题可以在这里反馈(Github)](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/issues/new/)

|  版本   | 变更  |
|  ----  | ----  |
| 0.1.0  | 最初的版本 |