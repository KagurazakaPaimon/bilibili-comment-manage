>[!NOTE]
>该项目**部分**由AI完成,欢迎PR提出修改,或者提交Issue告诉我们如何改进,谢谢大家!

<div align="center">

# Bilibili-Comment-Manage

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![Developed with](https://img.shields.io/badge/developed%20with-python%203.12.4-blue)](https://www.python.org)

[![LICENSE](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Release](https://img.shields.io/github/v/release/PaimonAnimation/bilibili-comment-manage)](https://github.com/PaimonAnimation/bilibili-comment-manage/releases)
[![Issues](https://img.shields.io/badge/issues-welcome-red)](https://github.com/PaimonAnimation/bilibili-comment-manage/issues)
[![Blog](https://img.shields.io/badge/blog-派蒙的博客-blue)](https://paimonmeow.cn)

</div>

## 简介
这是一个用于自动管理和清理B站视频评论区的工具.

现在项目已升级为基于[bilibili-api](https://github.com/Nemo2011/bilibili-api)的现代化版本.

本工具能够自动检测含有违禁词的评论,删除这些评论,并在用户多次违规后将其拉黑.

## 功能特性
1. **定时轮询评论区**
   - 使用异步任务实现非阻塞性查询
   - 默认每隔5分钟检查一次评论区(可配置)

2. **违禁词检测**
   - 支持正则表达式匹配
   - 可自定义违禁词列表

3. **自动删除违规评论**
   - 检测到含有违禁词的评论后自动删除

4. **用户违规统计**
   - 记录每个用户的违规次数
   - 保存违规用户的详细信息

5. **自动拉黑机制**
   - 当用户违规次数达到3次时自动拉黑该用户

6. **完善的日志系统**
   - 日志按天分割,便于查阅
   - 详细的错误追踪信息
   - 控制台输出info信息(可调为debug),log文件记录debug信息

7. **配置文件支持**
   - 通过`config.json`配置各项参数

## 使用方法
1. 安装Python3.9+
   > 推荐从使用3.12/3.13
   
2. 克隆或下载本项目

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 配置`config.json`文件:
   - `sessdata`, `bili_jct`, `ac_time_value`: B站账号凭证
   - `bvid`: 目标视频的BV号
   - `violation_words`: 违禁词列表
   - `whitelist`:`list[int]` 拉黑白名单列表
   - `interval`: 轮询间隔(秒)
   - `max_pages`: 最大获取评论页数(默认不用动)

5. 运行程序
   ```bash
   python app.py
   ```

## 获取B站凭证
1.  需要在浏览器先登录账号后再f12中获取,具体查看[bilibili_api的开发文档](https://nemo2011.github.io/bilibili-api/#/get-credential)

2.  将这些值填入`config.json`对应字段

## 未来计划
- [ ] 支持代理(可防止412风控)

## 更新记录

### 3.0 (Nov 02 2025)
- 重构
- 使用api获取主要数据
- 使用配置文件更改主要配置
- 全异步架构
- 可以作为模块在其他程序中调用
- 完整的日志支持

### 2.2 (Feb 21 2025)
- 更新了Edge浏览器支持

### 2.1 (---)
- **被派蒙吃了**

### 2.0 (Feb 20 2025)
- 新建仓库