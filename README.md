# 通用图片生成插件 (Generic Image Generation)

一个功能强大的 AstrBot 插件，支持通用图片生成和自定义指令配置，让你轻松打造专属的 AI 绘图工具。

## 功能特性

* **通用生图指令**：使用 `生图 [提示词]` 快速生成图片，简单直接。
* **图生图支持**：自动识别消息中的图片、回复的图片、或 `@用户` 来获取头像作为参考图进行生成。
* **自动处理GIF**：插件会自动识别GIF动图并提取第一帧进行处理，无需用户手动转换。
* **高度可定制**：通过配置文件创建专属指令，自定义触发词、提示词、反向提示词和模型。
* **灵活配置**：每个自定义指令都可以独立配置参数，满足不同场景需求。

## 安装与配置

### 安装

1. 下载本插件的压缩包并解压。
2. 将解压后的 `astrbot_plugin_generic_image_gen` 文件夹放入 `astrbot/plugins` 目录下。
3. 重启 AstrBot。

或使用 Git 克隆：

```bash
cd plugins
git clone https://github.com/mkroen/astrbot_plugin_generic_image_gen.git
```

### 配置

在 AstrBot 管理面板的 `插件管理` -> `通用图片生成插件` 中进行配置。

#### 全局配置

| 配置项 | 类型 | 描述 |
|--------|------|------|
| api_base_url | 字符串 | （可选）图片生成 API 的基础地址 |
| api_keys | 列表 | （可选）图片生成 API 的密钥列表，支持多个密钥自动轮换 |
| default_model | 字符串 | （可选）默认使用的图片生成模型 |

#### 基础生图配置

`basic_generation` 对象配置项：

| 字段 | 类型 | 描述 |
|------|------|------|
| enabled | 布尔值 | 是否启用基础生图功能，默认为 true |
| trigger | 字符串 | 触发词，默认为"生图" |
| model | 字符串 | （可选）指定使用的模型 |
| negative_prompt | 字符串 | （可选）默认的反向提示词 |

#### 自定义指令配置

在 `commands` 配置项中使用 JSON 格式配置多个自定义指令。每个指令包含以下字段：

| 字段 | 类型 | 描述 |
|------|------|------|
| trigger | 字符串 | **（必需）** 指令的触发词，例如：手办化、二次元化 |
| prompt | 字符串 | **（必需）** 生成图片的提示词 |
| negative_prompt | 字符串 | （可选）不希望出现的内容，用于提高生成质量 |
| model | 字符串 | （可选）指定使用的模型名称，留空则使用默认模型 |

### 配置示例

在管理面板的 `commands` 配置项中，使用 JSON 编辑器输入以下内容：

```json
[
  {
    "trigger": "手办化",
    "prompt": "Create a 1/7 scale commercialized figure of the character in the illustration, in a realistic style and environment. Place the figure on a computer desk, using a circular transparent acrylic base without any text. On the computer screen, display the ZBrush modeling process of the figure. Next to the computer screen, place a BANDAI-style toy packaging box printed with the original artwork.",
    "negative_prompt": "low quality, blurry, distorted",
    "model": ""
  }
]
```

### 配置模板

复制以下模板添加新指令：

```json
{
  "trigger": "你的触发词",
  "prompt": "你的提示词描述",
  "negative_prompt": "不想要的内容",
  "model": ""
}
```

### 推荐提示词

以下是一些有趣的提示词配置，可以直接复制使用：

<details>
<summary>🧸 玩偶化 - 将人物变成毛绒玩具</summary>

```json
{
  "trigger": "玩偶化",
  "prompt": "Turn the person in the uploaded picture into a soft, high-quality plush toy, with an oversized head, small body, and stubby limbs. Made of fuzzy fabric with visible stitching and embroidered facial features. The plush is shown sitting or standing against a neutral background. The expression is cute or expressive, and it wears simple clothes or iconic accessories if relevant. Lighting is soft and even, with a realistic, collectible plush look. Centered, full-body view.",
  "negative_prompt": "low quality, blurry",
  "model": ""
}
```
</details>

<details>
<summary>👩 拟人化 - 将角色变成真人Coser</summary>

```json
{
  "trigger": "拟人化",
  "prompt": "生成图片主体的真人东亚美女COSER，18岁，年轻，可爱，萌，身材好，真实的cosplay出片感，并保持当前主体的衣着及姿势，皮肤及衣物为真实的质感，侧后放置画架展示图片本身。位置在东京无人街头，保持相同姿势。像从插画里走出来的活人一样，完美精细的脸，直发，大眼睛，活泼。以人物为主体，画面中人物占比高。",
  "negative_prompt": "low quality, blurry",
  "model": "gemini-3-pro-image-preview"
}
```
</details>

<details>
<summary>📝 帮我做题 - 生成手写解题过程</summary>

```json
{
  "trigger": "帮我做题",
  "prompt": "Create a fully hand-drawn sketch-style illustration. Use the image I provide as the problem statement. Your output must be an illustration, not text. Illustrate a sheet of slightly wrinkled draft paper placed on a desk. On this draft paper, draw the entire solution process to the math problem from the input image. The solution must appear as natural student handwriting. Show all steps visually: formulas, calculations, arrows, marginal notes, circled key results. Pencil-style strokes with light smudging, small eraser marks, uneven pressure, realistic imperfections. If relevant, include hand-drawn diagrams such as number lines, geometric shapes, coordinate axes. Do not print or typeset any text. Everything must be drawn by hand. Do not rewrite the problem text. The paper only contains the solution. The final result must look like a realistic sketch photograph of a physical piece of draft paper on a desk.",
  "negative_prompt": "low quality, blurry",
  "model": "gemini-3-pro-image-preview"
}
```
</details>

## 使用方法

* **基础用法**
  * 发送 `生图 一只可爱的猫咪` 直接生成图片。
  * 发送 `生图` 然后发送一张图片进行图生图。
  
* **自定义指令**
  * 发送 `手办化`，然后发送一张图片。
  * 回复一张图片，并发送 `手办化`。
  * 发送 `手办化 @某人` 来将对方的头像进行转换。

## 致谢

本插件的部分实现思路参考了 **zgojin** 的优秀插件 [astrbot_plugin_figurine_workshop](https://github.com/zgojin/astrbot_plugin_figurine_workshop)，特别是图片处理和消息解析部分。在此表示诚挚的感谢！

## 关于

当前版本：v0.1.0  
作者：mkroen  
许可：MIT License

