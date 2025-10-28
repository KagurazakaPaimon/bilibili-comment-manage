>[!NOTE]
>该代码**部分**由AI完成,欢迎PR提出修改，或者提交Issue告诉我该如何改进，谢谢大家！

## 直链（不会做徽章qwq）
[Releases](https://github.com/paimonanimation/releases)

[Issues](https://github.com/PaimonAnimation/bilibili-comment-manage/issues)

[Gitee镜像](https://gitee.com/paimonanimation/bilibili-comment-manage)

[派蒙的博客](https://paimonmeow.cn)

# 简介
脑抽的时候突发奇想写的，想到**B站没有违禁词检测删除**功能就用`Selenium`库写了一个。

# 功能
1. 定时轮询评论区：
使用 `while True` 实现无限循环，每隔随机时间（2-5分钟）轮询一次评论区。<br>
使用 ``` time.sleep() ``` 控制轮询间隔。
2. 违规词检测：
定义 ```violation_words``` 列表，存储需要检测的违规词。
在 ```clean_comments``` 函数中，遍历每个评论内容，检查是否包含违规词。
3. 删除违规评论：
使用 Selenium 获取评论内容和删除按钮，模拟用户点击删除按钮。
如果评论包含违规词，删除该评论。
4. 用户违规次数统计：
使用字典 ```user_violation_count``` 记录每个用户的违规次数。
每次发现违规评论时，更新对应用户的违规计数。
5. 拉黑用户：
当用户的违规次数超过 3 次时，调用 ```blacklist_user``` 函数拉黑该用户。
模拟用户点击拉黑按钮，并确认操作。
6. 错误处理：
使用异常处理机制，捕获可能的错误（如元素未找到、页面加载失败等）。*如果连续三次出现错误，程序会暂停 5 分钟后重试。*

# 使用方法
1. 请先从[这里](https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe)下载Python 3.13。
>[!TIP]
>你也可以在 Microsoft Store 里下载Python。
>![Microsoft Store截图](https://github.com/PaimonAnimation/bilibili-comment-manage/blob/main/pictures/1.png)
2. 在[releases](https://github.com/PaimonAnimation/bilibili-comment-manage/releases/)里下载zip包。（包含程序源码、Driver和 `requirements.txt` 。
>[!NOTE]
>Release里包含了**Edge**和**Chrome**两个版本的包，请根据**实际情况**选择使用相应的程序源码，并安装相应的Driver。
3. 拿到程序文件之后，先安装 `requirements.txt` 里面的依赖。<br>然后你可以在 IDLE、命令行或者VSC里直接运行了！~~其实是我懒得编译~~
>[!IMPORTANT]
>请**按照注释，按需修改**代码第125、130和131行的内容。
>![截图](https://github.com/PaimonAnimation/bilibili-comment-manage/blob/main/pictures/2.png)

# 待更新

- [ ] 继续添加 Firefox 浏览器的支持

# 更新记录

## 3.0 
把函数写成类 </br>
异步支持 </br>
MongoDB数据库支持 </br>
日志 </br>
配置文件支持 </br>
类型注解

## 2.2 (Feb 21 2025)
更新了Edge支持

## 2.1 (---)
**被派蒙吃了**

## 2.0 (Feb 20 2025)
新建了仓库（大嘘）