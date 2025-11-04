import json
import asyncio
import os
import re
import traceback
from collections import deque
from logging import Logger
from typing import List, Dict, Any
from bilibili_api import comment, user
from bilibili_api.user import RelationType
from bilibili_api import Credential, video, sync
from logger import setup_logger



# 重要数据
#
# [cmt]:list[dict] 评论列表
# {cmt['rpid']} 回复id
# {cmt['member']['uname']} 用户名
# {cmt['mid']} uid
# {cmt['content']['message']} 内容
#
# [sub_comment]:list[dict] 子评论列表
# {sub_comment['rpid']} 子评论id
# {sub_comment['user']} 用户名
# {sub_comment['mid']} uid
# {sub_comment['content']} 内容

class BilibiliCommentManager:
    async def __init__(
                        self, 
                        sessdata:str, 
                        bili_jct:str, 
                        bvid:str, 
                        ac_time_value:str, 
                        violation_words:list[str],
                        logger:Logger) -> None:
        """
        初始化Bilibili评论管理器
        
        Args:
            sessdata (str): sessdata凭证
            bili_jct (str): bili_jct凭证
            ac_time_value (str): ac_time_value凭证
            bvid (str): 视频BV号
            violation_words (list): 违禁词列表
            logger (Logger): 日志记录器
        """
        self.logger = logger
        self.credential = Credential(sessdata=sessdata, bili_jct=bili_jct, ac_time_value=ac_time_value)
        await self._check_refresh()
        self.av_id = video.Video(bvid=bvid).get_aid()
        self.violation_words = violation_words or []
        self.violation_users_file = "violation_users.json"
        self.violation_users = await self._load_violation_users()
        self.comment_queue = deque()  # 评论处理队列
        self.blacklist_queue = deque()  # 拉黑处理队列
        self.violation_check_queue = asyncio.Queue() # 违禁词检查队列
    
    async def _check_refresh(self) -> None:
        """
        检查登录凭证是否需要刷新
        """
        self.logger.info("检查登录凭证是否需要刷新")
        try:
            if sync(self.credential.check_refresh()):
                self.logger.info("登录凭证已过期")
                sync(self.credential.refresh())
                self.logger.info("登录凭证已刷新")
            else:
                self.logger.info("登录凭证有效，无需刷新")
        except Exception as e:
            self.logger.error(f"刷新登录凭证时发生错误: {e}")
            self.logger.debug(traceback.format_exc())

    async def _load_violation_users(self) -> List[Dict[str, Any]]:
        """
        加载违规用户信息
        
        Returns:
            List[Dict[str, Any]]: 违规用户列表
        """
        if os.path.exists(self.violation_users_file):
            try:
                with open(self.violation_users_file, 'r', encoding='utf-8') as f:
                    self.logger.info("已加载违规用户信息")
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"加载违规用户信息失败: {e}")
                self.logger.debug(traceback.format_exc())
                return []
        else:
            # 初始化空的违规用户文件
            try:
                with open(self.violation_users_file, 'w', encoding='utf-8') as f:
                    self.logger.info("已创建违规用户文件")
                    json.dump([], f, ensure_ascii=False, indent=4)
                return []
            except Exception as e:
                self.logger.error(f"初始化违规用户文件失败: {e}")
                self.logger.debug(traceback.format_exc())
                return []

    async def _save_violation_users(self) -> None:
        """
        异步保存违规用户信息到文件
        """
        try:
            with open(self.violation_users_file, 'w', encoding='utf-8') as f:
                json.dump(self.violation_users, f, ensure_ascii=False, indent=4)
            self.logger.info("违规用户信息已保存")
        except Exception as e:
            self.logger.error(f"保存违规用户信息失败: {e}")
            self.logger.debug(traceback.format_exc())

    async def _check_violation(self, content: str) -> bool:
        """
        检查内容是否包含违禁词
        
        Args:
            content (str): 待检查的内容
            
        Returns:
            bool: 是否包含违禁词
        """
        try:
            for word in self.violation_words:
                if re.search(word, content):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"检查违禁词时发生错误: {e}")
            self.logger.debug(traceback.format_exc())
            return False

    async def _update_violation_user(self, username: str, uid: int, rpid: int, content: str) -> None:
        """
        更新违规用户信息
        
        Args:
            username (str): 用户名
            uid (int): 用户ID
            rpid (int): 评论ID
            content (str): 评论内容
        """
        try:
            # 查找用户是否已存在
            user_found = False
            user_index = -1
            for i, user_info in enumerate(self.violation_users):
                if user_info["uid"] == uid:
                    user_found = True
                    user_index = i
                    # 增加违规次数
                    user_info["violation_count"] += 1
                    # 添加评论ID和内容
                    user_info["comment_rpids"].append(rpid)
                    user_info["comment_contents"].append(content)
                    break

            # 如果用户不存在，添加新用户
            if not user_found:
                self.violation_users.append({
                    "username": username,
                    "uid": uid,
                    "violation_count": 1,
                    "comment_rpids": [rpid],
                    "comment_contents": [content]
                })

            # 如果违规次数恰好达到3次，加入黑名单队列
            check_index = len(self.violation_users) - 1 if not user_found else user_index
            if self.violation_users[check_index]["violation_count"] == 3:
                self.blacklist_queue.append(uid)
        except Exception as e:
            self.logger.error(f"更新违规用户信息时发生错误: {e}")
            self.logger.debug(traceback.format_exc())

    async def delete_comment(self, rpid) -> None:
        """
        删除评论
        
        Args:
            rpid (int): 评论ID
        """
        self.logger.info(f"准备删除评论 {rpid}")
        try:
            c = comment.Comment(
                self.av_id,
                comment.CommentResourceType.VIDEO,
                rpid=rpid,
                credential=self.credential
            )
            await c.delete()
            self.logger.info(f"评论 {rpid} 已删除")
        except Exception as e:
            self.logger.error(f"删除评论 {rpid} 时发生错误: {e}")
            self.logger.debug(traceback.format_exc())

    async def blacklist_user(self, uid) -> None:
        """
        拉黑用户
        
        Args:
            uid (int): 用户ID
        """
        self.logger.info(f"准备拉黑用户 {uid}")
        try:
            if uid not in [621240130]:
                u = user.User(uid=uid, credential=self.credential)
                await u.modify_relation(RelationType.BLOCK)
                self.logger.info(f"用户 {uid} 已被拉黑")

                # 将该用户的违规次数改为999作为标记
                for user_info in self.violation_users:
                    if user_info["uid"] == uid:
                        user_info["violation_count"] = 999
                        break
        except Exception as e:
            self.logger.error(f"拉黑用户 {uid} 时发生错误: {e}")
            self.logger.debug(traceback.format_exc())

    async def _get_single_sub_comment(self, rpid: int) -> List[Dict[str, Any]]:
        """
        获取单个评论的所有子评论
        
        Args:
            rpid (int): 评论ID
            
        Returns:
            List[Dict[str, Any]]: 子评论列表
        """
        try:
            all_sub_comments = []
            page = 1
            
            while True:
                sub = comment.Comment(
                    self.av_id,
                    comment.CommentResourceType.VIDEO,
                    rpid=rpid,
                    credential=self.credential
                )
                if page > 1 :
                    await asyncio.sleep(1)
                data = await sub.get_sub_comments(page_index=page, page_size=20)
                
                replies = data.get('replies', [])
                if not replies or len(replies) == 0:
                    break
                    
                for reply in replies:
                    all_sub_comments.append({
                        'rpid': reply.get('rpid'),
                        'mid': reply.get('mid'),
                        'user': reply.get('member', {}).get('uname'),
                        'content': reply.get('content', {}).get('message'),
                        'parent_rpid': rpid  # 父评论ID
                    })
                
                # 将获取到的子评论放入违禁词检查队列
                for reply in replies:
                    await self.violation_check_queue.put({
                        'type': 'sub_comment',
                        'data': {
                            'rpid': reply.get('rpid'),
                            'mid': reply.get('mid'),
                            'user': reply.get('member', {}).get('uname'),
                            'content': reply.get('content', {}).get('message'),
                            'parent_rpid': rpid
                        }
                    })
                
                if len(replies) == 20 :
                    page += 1
                else:
                    break
            
            self.logger.info(f"已获取评论 {rpid} 的全部子评论，共 {len(all_sub_comments)} 条")
            return all_sub_comments
        except Exception as e:
            self.logger.error(f"获取评论 {rpid} 的子评论时发生错误: {e}")
            self.logger.debug(traceback.format_exc())
            raise e

    async def get_comments(self, max_pages=5) -> list[dict]:
        """
        获取视频评论
        
        Args:
            max_pages (int): 最大获取页数
            
        Returns:
            list[dict]: 评论列表
        """
        comments = []
        page = 1
        try:
            while True:
            
                self.logger.info(f"正在获取第 {page} 页评论")
                c = await comment.get_comments(
                    self.av_id, 
                    comment.CommentResourceType.VIDEO, 
                    page_index=page,
                    order=comment.OrderType.LIKE, 
                    credential=self.credential
                )

                replies = c['replies']
                if not replies:
                    self.logger.info(f"第 {page} 页没有评论，已结束")
                    self.logger.info(f"共获取{page-1}页评论")
                    break
                comments.extend(replies)
                
                # 将获取到的评论放入违禁词检查队列
                for reply in replies:
                    await self.violation_check_queue.put({
                        'type': 'comment',
                        'data': reply
                    })
                
                page += 1
                if page > max_pages:
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            self.logger.error(f"获取评论时发生错误: {e}")
            self.logger.debug(traceback.format_exc())
            raise e

        return comments

    async def _process_violations(self) -> None:
        """
        处理违禁词检查队列中的评论和子评论
        """
        try:
            while True:
                try:
                    # 从队列中获取待检查的评论或子评论，设置超时以便能正常退出
                    item = await asyncio.wait_for(self.violation_check_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # 超时继续，允许循环检查是否应该退出
                    continue
                
                item_type = item['type']
                data = item['data']
                
                if item_type == 'comment':
                    content = data['content']['message']
                    username = data['member']['uname']
                    uid = data['mid']
                    rpid = data['rpid']
                elif item_type == 'sub_comment':
                    content = data['content']
                    username = data['user']
                    uid = data['mid']
                    rpid = data['rpid']
                else:
                    # 未知类型，标记任务完成并继续
                    self.violation_check_queue.task_done()
                    continue
                
                # 检查是否包含违禁词
                if await self._check_violation(content):
                    self.logger.info(f"发现违规{item_type}: {username}({uid}): {content}")
                    # 更新违规用户信息
                    await self._update_violation_user(username, uid, rpid, content)
                    # 添加到删除队列
                    self.comment_queue.append(rpid)
                
                # 标记该队列任务已完成
                self.violation_check_queue.task_done()
        except Exception as e:
            self.logger.error(f"处理违禁词检查队列时发生错误: {e}")
            self.logger.debug(traceback.format_exc())

    async def process_all_comments(self, max_pages=99999) -> None:
        """
        处理所有评论和子评论的主流程方法
        
        Args:
            max_pages (int): 最大获取页数
        """
        try:
            # 启动违禁词检查任务
            violation_task = asyncio.create_task(self._process_violations())
            
            # 获取评论
            comments_task = asyncio.create_task(self.get_comments(max_pages=max_pages))
            comments = await comments_task
            self.logger.info(f"共获取到 {len(comments)} 条评论")
            
            # 提取子评论
            sub_comments_tasks = []
            for cmt in comments:
                # 检查是否有内嵌的子评论
                if 'replies' in cmt and cmt['replies']:
                    # 如果有内嵌子评论，则调用API获取完整的子评论列表
                    task = asyncio.create_task(self._get_single_sub_comment(cmt['rpid']))
                    sub_comments_tasks.append((task, cmt['rpid']))
                    # 每次API调用后等待0.5秒
                    await asyncio.sleep(0.8)

            # 等待所有子评论获取任务完成
            sub_comments = []
            for task, parent_rpid in sub_comments_tasks:
                try:
                    sub_list = await task
                    sub_comments.extend(sub_list)
                except Exception as e:
                    self.logger.error(f"获取评论 {parent_rpid} 的子评论时发生错误: {e}")
                    self.logger.debug(traceback.format_exc())

            self.logger.info(f"共获取到 {len(sub_comments)} 条子评论")

            # 等待违禁词检查队列处理完成
            await self.violation_check_queue.join()
            
            # 取消违禁词检查任务
            violation_task.cancel()
            try:
                await violation_task
            except asyncio.CancelledError:
                pass

            # 保存违规用户信息
            await self._save_violation_users()

            # 处理删除队列中的评论（间隔0.1秒）
            while self.comment_queue:
                rpid = self.comment_queue.popleft()
                await self.delete_comment(rpid)
                await asyncio.sleep(0.5)

            # 处理拉黑队列中的用户（间隔0.1秒）
            while self.blacklist_queue:
                uid = self.blacklist_queue.popleft()
                await self.blacklist_user(uid)
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"处理评论时发生错误: {e}")
            self.logger.debug(traceback.format_exc())


async def load_config(config_file='config.json'):
    """
    从JSON文件加载配置
    
    Args:
        config_file (str): 配置文件路径
        
    Returns:
        dict: 配置信息字典
    """
    try:
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")
        with open(config_file, 'r', encoding='utf-8') as f:
            config: dict = json.load(f)
        return config
    except Exception as e:
        raise Exception

if __name__ == "__main__":
    async def main():
        try:
            logger = setup_logger(filename='bot', cmd_level="INFO")
            # 从配置文件加载配置
            config = await load_config()
            # 定时任务循环
            interval = config.get("interval", 300)  # 默认5分钟(300秒)

            # 初始化评论管理器
            manager = BilibiliCommentManager(
                sessdata=config.get("sessdata",""),
                bili_jct=config.get("bili_jct",""),
                bvid=config.get("bvid",""),
                ac_time_value=config.get("ac_time_value", ""),
                violation_words=config.get("violation_words", [""]),
                logger=logger
            )

            # 循环执行
            while True:
                await manager.process_all_comments(
                    max_pages=config.get("max_pages", 9999)
                )
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"程序运行时发生错误: {e}")
            logger.debug(traceback.format_exc())
    asyncio.run(main())