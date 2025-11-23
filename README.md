# 通用图片生成插件 (Generic Image Generation)

一个功能强大的 AstrBot 插件，支持通用图片生成和自定义指令配置，让你轻松打造专属的 AI 绘图工具。

## 功能特性

* **通用生图指令**：使用 `生图 [提示词]` 快速生成图片，简单直接。
* **图生图支持**：自动识别消息中的图片、回复的图片、或 `@用户` 来获取头像作为参考图进行生成。
* **自动处理GIF**：插件会自动识别GIF动图并提取第一帧进行处理，无需用户手动转换。
* **高度可定制**：通过配置文件创建专属指令，自定义触发词、提示词、反向提示词、模型和提供商。
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

| 配置项 | 类型 | 描述 |
|--------|------|------|
| trigger | 字符串 | **（必需）** 指令的触发词，例如：手办化、二次元化 |
| prompt | 字符串 | **（必需）** 生成图片的提示词 |
| negative_prompt | 字符串 | （可选）不希望出现的内容，用于提高生成质量 |
| model | 字符串 | （可选）指定使用的模型名称 |
| provider | 字符串 | （可选）指定使用的提供商名称 |

### 配置示例

```json
{
  "commands": [
    {
      "trigger": "手办化",
      "prompt": "figure, toy, product photography, white background, high quality",
      "negative_prompt": "blurry, low quality, distorted"
    },
    {
      "trigger": "二次元",
      "prompt": "anime style, colorful, vibrant, high quality illustration",
      "negative_prompt": "realistic, photo, 3d",
      "model": "anime-diffusion"
    },
    {
      "trigger": "油画风格",
      "prompt": "oil painting style, artistic, classical art",
      "provider": "openai"
    }
  ]
}
```

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

