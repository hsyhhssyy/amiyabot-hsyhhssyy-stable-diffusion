# Stable Diffusion

提供一个StableDiffusion WebUI的兔兔接口。
要想使用这个功能，首先你需要有一个本地的StableDiffuion部署。
如果你还不知道怎么自己部署一个自己的绘图AI，你可以去看看B站大佬秋叶akki的教程。

**<span style="color:green;">要想使用本功能，你必须要对如何使用StableDiffuion有一定基础的了解，否则本插件很多配置项的功能你都不知道是干什么用的。虽然本插件开箱即用的能力还凑合。</span>**

## 绘图命令

每个群内用户，可以使用`兔兔绘图：琴柳穿着jk在海边漫步`这样的关键词来进行绘画，兔兔会稍后在群内回复画好的图片，效果如下：

![Alt text](document_image/image.png)

## 安装要求

该插件需要兔兔版本大于

## 安装与配置

刚装好插件后，插件什么都做不了，你需要跟着下面这几步去执行初始化配置。

### 配置webui地址

首先打开你的webui，然后拉到页面最下方，点击API链接。

![Alt text](image.png)

然后复制打开的页面的地址到设置中的`Doc Url`配置项中。

注：本插件暂不支持WebUI登录认证，你的WebUI地址必须可以匿名访问。
WebUI自带的认证功能会在未来版本支持。如果你使用其他互联网服务商提供的网络部署服务，并且拥有独特的认证方式，请到Git提交Issue申请支持。

### 等待连接

稍等30秒，如果WebUI可以连接，你会在兔兔日志中看到诸如下面这样的提示信息。

```log

2023-10-10 12:47:13,844 [StableDiffusion][     INFO] 因docs变化而重载WebUIApi...
2023-10-10 12:47:13,918 [StableDiffusion][     INFO] WebUIApi刷新完毕...

```

此时已经连上了WebUI Api，可以开始后续步骤了。

### 模型选择

打开兔兔Console，在本插件的设置里，全局设置中，找到‘模型选择’配置项。

在里面添加复数个模型和对应的prompt。

这个模块的工作原理是这样的：
每次用户说话，兔兔会生成四张图像，其实是ChatGPT的Prompt会尝试理解用户的输出，然后给出四段danboru tag。
这四段tag会被同时标记为下面几种类型：

"Anime", 动画
"Manga", 漫画
"Photographic", 照片
"Isometric", 微距
"Low_Poly", 
"Line_Art", 素描
"3D_Model", 3D模型
"Pixel_Art", 像素风
"Watercolor" 水彩

以及我自己定义的类型

"Chibi", Q版

如果你在某个类型下配置了1个或者多个模型，那么这段tag的底模就会是你选的这一个，同时系统也会自动将对应的prompt拼接到这段tag的最后。

如果你某个类型没有定义模型，而ChatGPT生成了一段对应的tag，就会使用默认模型配置项里的模型。（所以如果你每个类型都提供至少一个项目的话，默认模型实际上不会被调用到）

### 添加Lora

好了，现在，兔兔已经可以开始接受用户的输入来画图了，但是作为明日方舟bot，总要有点特色。
管理员私聊兔兔并发送 兔兔下载Lora。
兔兔就会在‘Lora下载到’配置的那个目录创建两个文件夹：lora和embeddings。如果配置项为空，默认位置是resources\stable-diffusion
然后，兔兔会去civitai上，按照Arknights作为关键词搜索模型,然后自动挑选并下载干员的lora,并放在这两个文件夹下。
等他下载完，你需要将lora和embeddings分别拷贝到SD的对应目录或子目录。
兔兔在做这件事时，会同时保存lora的文件名和提示词，因此你不可以对lora或者embeddings改名。

然后，当兔兔检测到用户绘图指令提到了方舟的干员，他会自动拼接Lora和Embeddings进prompt中。

- 群内单人锁

- 下载lora脚本修改:
1. 对于同一个干员的多个版本，只下载最好的那个(get_model_score)
2. 如果文件不是safesensor,则不下载.
3. 加入对lyco的支持---暂时跳过疑似Lyco的模型

- 看一下Lora的混合,是什么问题导致的
- 输出对干员的检测

- 德克萨斯和缄默德克萨斯会一起触发

## 备注

插件图标是我自己用StableDiffusion跑的。

[项目地址:Github](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/)

[遇到问题可以在这里反馈(Github)](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/issues/new/)

[如果上面的连接无法打开可以在这里反馈(Gitee)](https://gitee.com/hsyhhssyy/amiyabot-plugin-bug-report/issues/new)


|  版本   | 变更  |
|  ----  | ----  |
| 1.0  | 最初的版本 |