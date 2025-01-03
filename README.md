# StableDiffusion绘图

提供一个调用StableDiffusion WebUI的兔兔功能。

**提示**：使用本功能前，请确保你已经在本地部署了StableDiffuion。不清楚如何部署？推荐参考B站大佬秋叶akki的教程: https://www.bilibili.com/video/BV1iM4y1y7oA。

以前的兔兔绘图插件被拆分成两个独立插件，一个纯AI绘图插件，和一个整合插件。本插件就是这个纯AI绘图插件。

## 绘图命令

每个群内用户，可以使用`兔兔绘图：琴柳穿着jk在海边漫步`这样的关键词来进行绘画，兔兔会稍后在群内回复画好的图片，效果如下：

![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-1.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-3.png)
![Alt text](<https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/)@8LU4KD0FMQVPCXA(9T(ZI.png>)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/7KQBVL69%7BZLAGFSPUN055I9.png)

命令必须以`兔兔绘图：`开头，注意兔兔不可以换成任意其他唤醒词。此外，还可以在消息的结尾使用 -ar 16:9 -hr -lr 来指定分辨率和输出高分辨率，低分辨率图形。

## 图生图

可以通过在消息中包含一张或者两张图片的形式来进行图生图绘制。

![Alt text](<https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/S6JM_0$AA6B1HYDIU}(W2_7.png>)

## 绘图队列

目前版本下，当兔兔有绘图任务时，会将其他新任务排队，队列总长度为5，每个群不可超过2。

队列这么短是因为不想耽误太长时间，一个任务的运行需要三五分钟，5个任务就已经是半小时以后了。

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

2023-10-10 12:47:13,844 [AIPainting][     INFO] 因docs变化而重载WebUIApi...
2023-10-10 12:47:13,918 [AIPainting][     INFO] WebUIApi刷新完毕...

```

此时已经连上了WebUI Api，可以开始绘图了。

## 版权声明

SD WebUI 使用AGPL版权。AGPL是一个强限制的开源协议，访问任何使用AGPL协议的网络服务的代码也需要开源。因此，本项目同样遵循AGPL版权。任何使用该服务的人或修改该服务的人也必须提供源代码。

注意：AGPL相比于GPL，增加了对通过服务访问的限制，也就是说，你将本项目部署为服务，然后用其他软件去调用它，那么其他软件可能也需要开源。

## 法律风险

**StableDiffusion不带道德校验模块，兔兔可能会产生色情，暴力，反动，版权侵害等违法行为。**
**兔兔运营方应当关注兔兔的生成内容并及时处理，出现任何法律责任，本项目概不负责。**

## TODO

- 完善插件配置项，插件的各个配置项写的都非常简略，如果你愿意帮我修改配置项的说明，那我非常欢迎您提出PR。
- 完善文档，这篇文档写的非常简略，对于没有StableDiffusion经验的人来说可能会比较困难，同时还缺少一些步骤的截图。如果您有兴趣帮忙修改文档，您可以直接在Github提出PR。

## 备注

* 插件图标是使用StableDiffusion生成的。

## 相关链接

[项目地址:Github](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/)

[遇到问题可以在这里反馈(Github)](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/issues/new/)

|  版本   | 变更  |
|  ----  | ----  |
| 0.1.0  | 最初的版本 |