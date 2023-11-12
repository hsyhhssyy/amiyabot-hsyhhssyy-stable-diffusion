# Stable Diffusion + ChatGPT

提供一个调用本地StableDiffusion WebUI的兔兔功能，再结合ChatGPT，实现一个近似MidJourney的效果（大概吧）。

**提示**：使用本功能前，请确保你已经在本地部署了StableDiffuion。不清楚如何部署？推荐参考B站大佬秋叶akki的教程: https://www.bilibili.com/video/BV1iM4y1y7oA。

**有一些必要WebUI的插件需要安装，他们都列在最下面的必要插件章节中**

**<span style="color:green;">要想使用本功能，你必须要：</span>**

1. **<span style="color:green;">对如何使用StableDiffuion有了解, 能够使用SD进行绘图和修图等操作. </span>**
2. **<span style="color:green;">拥有一个ChatGPT的API Key. </span>**
3. **<span style="color:green;">网络环境可以访问ChatGPT, Civitai网站. </span>**
4. **<span style="color:green;">安装我的另一个ChatGPT插件（可不设置为启用）并配置API Key</span>**


**<span style="color:red;">在开始之前，请一定要先从头到尾读完本说明。</span>**

**<span style="color:red;">如果你还不会使用StableDiffusion WebUI进行AI绘图，以及无法正常运行兔兔会涉及到的那些WebUI插件和功能，我不会负责教学和讲解。</span>**

**<span style="color:red;">当你提出一个Issue时，只有当你可以在StableDiffusionWebUI实现该效果，但是兔兔却报错时，我才会受理这个Issue。</span>**

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

可以使用 -ca 或者 -ia 命令来让兔兔以这张图为构图姿势还是人物画风
如果你指定了-ia来要求参考人物画风，最好不要再提供干员的名字。

该功能可以通过配置文件来开启，但是开启时，要求你拥有IP-Adapter和Canny两个ControlNet的ControlType，否则会报错。
你需要先试着用一下IP-Adapter和Canny两个模式，保证他们可以正常工作后，再开启该配置。

## 绘图队列

目前版本下，当兔兔有绘图任务时，会将其他新任务排队，队列总长度为5，每个群不可超过2。

队列这么短是因为不想耽误太长时间，一个任务的运行需要三五分钟，5个任务就已经是半小时以后了。

## 安装要求

1. **<span style="color:red;"> 兔兔版本大于6.3.9</span>**

2. **<span style="color:red;"> 已经部署且可运行的StableDiffusionWebUI</span>**

3. **<span style="color:red;"> 可以连接Civitai和OpenAI的网络连接</span>**

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

此时已经连上了WebUI Api，可以开始后续步骤了。

### 选择ChatGPT模型

不管你是否使用ChatGPT，你都必须要安装ChatGPT插件。
配置项中有是否开启ChatGPT的说明，注意开启后Api调用时收费的。
3和3/4Mixed的区别在于会用4去识别用户提到的干员名字，来解决“大哥大嫂过年好，除夕快乐，阿要给大家表演一曲苏格兰风笛。”难题。实际上生成的Prompt区别不大。用3会便宜很多，代价只不过是会画出一些额外的干员。

### 模型选择

* 刷新兔兔Console，在本插件设置中，进入‘模型选择’配置项。
* 根据需要配置模型和相应的prompt。
* 模型选择主要的作用是针对预定义的风格，选择底模和配置一些默认的参数

**工作原理**：

1. **图像生成**： 
   - 当用户发言时，兔兔会生成四张图像。
   - 这实际上是ChatGPT的Prompt会尝试理解用户的输出，然后给出四段danboru tag。

2. **Tag 类型**：
   - 生成的这四段tag会被标记为以下几种类型之一

   - SDXL标准Style类型：
     - "Anime" - 动画
     - "Manga" - 漫画
     - "Photographic" - 照片
     - "Isometric" - 微距
     - "Low_Poly" - 低分辨率
     - "Line_Art" - 素描
     - "3D_Model" - 3D模型
     - "Pixel_Art" - 像素风
     - "Watercolor" - 水彩

   - 还包括我自定义的类型：
     - "Chibi" - Q版

3. **模型配置**：
   - 如果您为某个类型配置了一个或多个模型，那么该tag的底模就从对应的配置项中随机一个。
   - 系统会自动将对应的prompt拼接到这段tag的最后，并使用配置的参数。
   - 如果您没有为某个类型定义模型，而ChatGPT生成了一个对应的tag，则将使用`默认模型`配置项中的模型。
   - 如果您为每种类型都提供了至少一个模型，那么`默认模型`实际上不会被调用。

### 添加Lora

好了，现在，兔兔已经可以开始接受用户的输入来画图了，但是作为明日方舟bot，总要有点特色。

管理员私聊兔兔并发送`兔兔下载Lora`。

兔兔就会在‘Lora下载到’配置的那个目录创建两个文件夹：lora和embeddings。如果配置项为空，默认位置是resources\stable-diffusion。然后，兔兔会去civitai上，按照Arknights作为关键词搜索模型,然后自动挑选并下载干员的lora,并放在这两个文件夹下。

等他下载完，你需要将lora和embeddings分别拷贝到SD的对应目录或子目录。
兔兔在做这件事时，会同时保存lora的文件名和提示词，因此你**不可以**对lora或者embeddings改名。
你可以在models\Lora\下建立一个子文件夹来放置这些lora,embeddings同理。新版WebUI是支持子文件夹的。

然后，当兔兔检测到用户绘图指令提到了方舟的干员，他会自动拼接Lora和Embeddings进prompt中，从而正确的绘制出方舟干员。

在resources\stable-diffusion\lora-download-log.txt文件中,你可以看到下载的详情日志.

## 必要插件

ADetailer，为了保证出图质量（主要是修脸和修手），指令默认用ADetailer进行了后处理，不安装ADetailer会报错。

`ADetailer的下载地址是（https://github.com/Bing-su/adetailer）`

## 可选插件

ControlNet, 各种一键包都会自带，如果你没有，那你需要去手动安装。

IP-Adapter，用于根据图片生成角色数据和画风的插件，目前网络上并没有比较好的傻瓜式教程，你可能需要自行百度如何安装该插件，下载对应的模型以及如何使用。

~~## GIF~~

~~兔兔可以利用AnimatedDiff插件输出GIF。~~

~~* 注意: AnimatedDiff插件Hack了很多其他插件，并在执行完毕后Hack回来，失败报错后会导致需要重启SD，因此可能会导致服务中断。~~

~~* 因为AnimatedDiff目前非常不稳定，为了大家的兔兔着想，本功能暂不开放。~~

## 开箱即用

* 你可能注意到了，本项目自带的默认配置文件并不是一个空白配置文件。
* 默认配置文件的内容，就是我正在使用的配置内容。
* 默认配置文件中含有我挑选的几个优质底模和画风Lora，他们在能够提供优质画面的同时，还能不过分影响角色Lora。
* 在positive和negitive prompt中，还含有几个优化lora。
* 这些lora都来自civitai，他们的列表如下：

* 底模（Checkpoints）
   - QteaMix
   - OrangeMix
   - RevAnimated
   - DreamShaper
   - GhostMix
* 风格Lora
   - [Anime Lineart / Manga-like (线稿/線画/マンガ風/漫画风) Style](https://civitai.com/models/16014/anime-lineart-manga-like-style)
   - [Lineart——照片线稿提取](https://civitai.com/models/94355/lineart)
   - [Miniature world style 微缩世界风格](https://civitai.com/models/28531/miniature-world-style)
   - [M_Pixel 像素人人](https://civitai.com/models/44960/mpixel)
   - [沁彩 Colorwater](https://civitai.com/models/16055/colorwater)
   - [【Art Style】ChiChi Style](https://civitai.com/models/22992/art-stylechichi-style)
   - [Akagi Shun Style LoRA](https://civitai.com/models/46813/akagi-shun-style-lora)
   - [Add More Details - Detail Enhancer / Tweaker (细节调整) LoRA](https://civitai.com/models/82098?modelVersionId=87153)

* 你可以选择将他们都下载下来，这样就可以直接使用我的配置文件。
* 如果你想自己调教，你也可以自己挑选模型和配置。**<span style="color:red;">但是请检查一遍配置，将使用了你没有的底模或Lora或插件的配置项删掉或关闭，不然兔兔会报错。</span>**
* 我自己部署的兔兔，使用了ControlNet，Canny和IPAdapter，但是，我的默认配置中没有给出他们的配置项，因为他们需要比较复杂的安装步骤。你需要自行安装，然后选择一个模型。

## 版权声明

SD WebUI 使用AGPL版权。AGPL是一个强限制的开源协议，访问任何使用AGPL协议的网络服务的代码也需要开源。因此，本项目同样遵循AGPL版权。任何使用该服务的人或修改该服务的人也必须提供源代码。

注意：AGPL相比于GPL，增加了对通过服务访问的限制，也就是说，你将本项目部署为服务，然后用其他软件去调用它，那么其他软件可能也需要开源。

## 法律风险

**尽管我尽了最大努力，包括StableDiffusion和ChatGPT两端均加入了负面提示，兔兔仍然可能会产生色情，暴力，反动，版权侵害等违法行为。**
**兔兔运营方应当关注兔兔的生成内容并及时处理，出现任何法律责任，本项目概不负责。**

## TODO

- 完善插件配置项，插件的各个配置项写的都非常简略，如果你愿意帮我修改配置项的说明，那我非常欢迎您提出PR。
- 完善文档，这篇文档写的非常简略，对于没有StableDiffusion经验的人来说可能会比较困难，同时还缺少一些步骤的截图和Civitai的链接地址。如果您有兴趣帮忙修改文档，您可以直接在Github想我提出PR。

## 备注

* 插件图标是使用StableDiffusion生成的。

## 相关链接

[项目地址:Github](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/)

[遇到问题可以在这里反馈(Github)](https://github.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/issues/new/)

|  版本   | 变更  |
|  ----  | ----  |
| 0.1.0  | 最初的版本 |
| 0.1.1  | 兔兔画廊增加一堆图片 |
| 0.2.0  | 修复了商店页面不显示文档的bug |

## 下面就是兔兔画廊时间了

** 下面的内容都是由兔兔绘图生成的 **
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-6.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-4.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-7.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-9.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-10.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-12.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-14.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/image-15.png)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/LZ%60BZPCGW$JH%7D%7D5GRPISFDG.png)
![Alt text](<https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/2H1CT((H2]PL0G(XBD%K7DC_tmb.png>)
![Alt text](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-hsyhhssyy-stable-diffusion/master/images/_D6%60UYEN5X%7B%5DINYA9FORQE9_tmb.png)


## TODO List

暂无


