# Graphiti MCP Usage Skill

## 概述

这个Skill让CodeBuddy等AI助手能够智能地使用Graphiti知识图谱MCP服务器，自动存储和检索对话中的重要信息，提供个性化的连续对话体验。

## 包含内容

```
graphiti-mcp-usage/
├── SKILL.md                      # 主技能文件（必需）
├── references/
│   └── system-prompt-zh.md       # 中文详细说明文档
└── README.md                     # 本文件
```

## 功能特性

- 🤖 **自动存储**：识别有价值的信息并自动保存到知识图谱
- 🔍 **智能检索**：在需要时自动检索历史信息
- 💬 **多模式支持**：完全自动、触发词、确认三种交互模式
- 📝 **智能标签**：自动分类信息（偏好、学习笔记、项目等）
- 🎯 **个性化体验**：基于用户历史提供定制化建议

## 安装方法

### 方法1：加载Skill（推荐）

在CodeBuddy中使用：

```bash
# 加载Skill
Load skill: c:\Users\TU\Documents\WorkingSpace\Graphiti\mcp_server\graphiti-mcp-usage
```

### 方法2：手动配置System Prompt

如果不想加载Skill，也可以手动配置：

1. 复制 `references/system-prompt-zh.md` 的内容
2. 在CodeBuddy设置中添加为System Prompt
3. 启用graphiti MCP工具

## 使用示例

### 示例1：自动存储学习笔记

**用户**："今天学习了Python的装饰器，感觉很有用"

**AI自动执行**：
```json
{
  "name": "Python装饰器学习笔记",
  "episode_body": "今天学习了Python的装饰器，很有用",
  "source": "Procedure",
  "group_id": "main"
}
```

**AI回复**："✓ 已将Python装饰器学习笔记保存到知识图谱"

### 示例2：智能检索历史信息

**用户**："我之前说的那个Python知识点是什么？"

**AI自动执行**：
1. 提取关键词："Python"
2. 调用search_episodes(query="Python", group_id="main")
3. 找到之前的学习记录

**AI回复**："根据你的知识图谱记录，你之前学习了Python装饰器..."

### 示例3：基于历史提供建议

**用户**："我想学一个新的Python框架，有什么推荐？"

**AI自动执行**：
1. 检索用户已有的Python相关记录
2. 分析学习偏好
3. 基于历史提供个性化建议

**AI回复**："根据你之前的学习记录，你已经掌握了...我推荐..."

## 交互模式

### 模式1：完全自动（默认）
AI自动判断何时存储和检索，无需用户干预。

### 模式2：触发词模式
用户使用关键词触发：
- 存储："记住：..."、"保存..."
- 检索："关于...我之前说过什么？"

### 模式3：确认模式
AI主动询问："这条信息很重要，需要我保存到知识图谱吗？"

## 自动存储的场景

✅ **会存储的内容**：
- 学习笔记和技能总结
- 个人偏好和选择
- 项目和工作信息
- 重要的个人信息（非敏感）
- 有价值的对话总结

❌ **不会存储的内容**：
- 密码、API密钥等敏感信息
- 个人身份证号、银行账号等隐私信息
- 临时性、无长期价值的信息

## 智能标签系统

存储时自动分类：
- `Preference` - 用户偏好、选择、观点
- `Procedure` - 学习笔记、操作步骤、方法论
- `Requirement` - 具体需求、功能要求
- `Experience` - 个人经历、工作经验
- `Project` - 项目信息、工作内容
- `Knowledge` - 知识点、技术概念
- `Decision` - 决策过程、选择理由
- `Goal` - 目标、计划

## 与直接配置System Prompt的区别

| 特性 | 加载Skill | 配置System Prompt |
|------|-----------|-------------------|
| 安装 | 简单（一行命令） | 需要复制粘贴大量文本 |
| 更新 | 自动更新（重新加载） | 需要手动更新 |
| 维护 | 集中维护 | 分散在各个配置中 |
| 可分享性 | 易于分享 | 难以分享 |
| 加载时机 | 按需加载 | 始终加载 |

## 最佳实践

1. **定期回顾**：定期查看知识图谱中的信息，确保质量
2. **使用标签**：利用标签快速分类和检索
3. **合理分组**：使用group_id管理不同场景的信息
4. **隐私保护**：避免存储敏感信息
5. **信息整合**：将相关的episodes合并或建立联系

## 故障排查

### 问题：AI没有自动存储信息
- **检查**：是否正确加载了Skill
- **检查**：graphiti MCP是否已连接
- **检查**：用户说的是否属于应该存储的内容

### 问题：检索不到历史信息
- **检查**：group_id是否正确
- **尝试**：使用不同的关键词
- **确认**：信息确实已存储

### 问题：存储失败
- **检查**：API密钥是否有效
- **检查**：数据库连接是否正常
- **查看**：错误日志

## 版本历史

- v1.0 (2025-01-30): 初始版本
  - 支持自动存储和检索
  - 包含中文System Prompt
  - 提供三种交互模式

## 相关文件

- [SKILL.md](./SKILL.md) - 技能主文件
- [references/system-prompt-zh.md](./references/system-prompt-zh.md) - 详细中文说明
- [README.md](./README.md) - 本文件

## 许可证

This skill is part of the Graphiti MCP Server project, licensed under Apache-2.0.
