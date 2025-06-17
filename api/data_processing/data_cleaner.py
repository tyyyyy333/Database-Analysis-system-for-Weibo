import re
import jieba
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import torch
from transformers import BertTokenizer, BertModel
import numpy as np
from collections import defaultdict
import hashlib
import os
from pathlib import Path
import json

class DataCleaner:
    def __init__(self, batch_size: int = 32, cache_size: int = 10000, model_path: str = 'models/bert-base-chinese'):
        self.logger = logging.getLogger(__name__)
        self.batch_size = batch_size
        self.cache_size = cache_size
        
        # 初始化缓存
        self.semantic_cache = {}
        self.meaningful_cache = {}
        
        # 加载停用词和自定义词典
        self.stopwords = self._load_stopwords()
        self.custom_dict = self._load_custom_dict()
        
        # 初始化BERT模型
        self.model, self.tokenizer, self.device = self._init_bert_model(model_path)
        
        # 初始化正则表达式和预定义模式
        self._init_patterns()
        
    def _load_stopwords(self) -> set:
        """加载停用词"""
        try:
            with open('data/stopwords.txt', 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f)
        except FileNotFoundError:
            self.logger.warning("停用词文件未找到，将使用空集合")
            return set()
            
    def _load_custom_dict(self) -> set:
        """加载自定义词典"""
        try:
            with open('data/custom_dict.txt', 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f)
        except FileNotFoundError:
            self.logger.warning("自定义词典文件未找到，将使用空集合")
            return set()
            
    def _init_bert_model(self, model_path: str) -> tuple:
        """初始化BERT模型"""
        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            if os.path.exists(model_path):
                self.logger.info(f"从本地路径加载模型: {model_path}")
                tokenizer = BertTokenizer.from_pretrained(model_path)
                model = BertModel.from_pretrained(model_path)
            else:
                self.logger.warning(f"本地模型路径 {model_path} 不存在，将使用在线模型")
                tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
                model = BertModel.from_pretrained('bert-base-chinese')
                
                os.makedirs(model_path, exist_ok=True)
                tokenizer.save_pretrained(model_path)
                model.save_pretrained(model_path)
                self.logger.info(f"模型已保存到本地路径: {model_path}")
            
            model.to(device)
            model.eval()
            self.logger.info(f"BERT模型加载成功，使用设备: {device}")
            return model, tokenizer, device
            
        except Exception as e:
            self.logger.error(f"BERT模型加载失败: {str(e)}")
            return None, None, None
            
    def _init_patterns(self):
        """初始化正则表达式和预定义模式"""
        # 地区信息正则表达式
        self.location_pattern = re.compile(r'来自(.*?)(?:\s|$)')
        
        # 预定义的无意义评论模式
        self.meaningless_patterns = [
            r'^转发微博$',
            r'^//@.*$',
            r'^http[s]?://.*$'
        ]
        
        # 有意义的符号模式
        self.meaningful_symbols = {
            '，': '逗号',
            '。': '句号',
            '？': '问号',
            '！': '感叹号',
            '...': '省略号',
            '～': '波浪号',
            '~': '波浪号',
            '…': '省略号'
        }
        
        # 有意义的数字模式
        self.meaningful_numbers = {
            '6': '六',
            '9': '九',
            '233': '笑',
            '666': '厉害',
            '555': '哭',
            '520': '我爱你',
            '1314': '一生一世',
            '88': '拜拜',
            '99': '久久',
            '111': '一一一',
            '222': '二二二',
            '333': '三三三',
            '444': '四四四',
            '555': '五五五',
            '777': '七七七',
            '888': '八八八',
            '999': '久久久'
        }
        
        # 有意义的英文缩写
        self.meaningful_abbr = {
            'awsl': '啊我死了',
            'xswl': '笑死我了',
            'yyds': '永远的神',
            'nb': '牛逼',
            'gg': '哥哥',
            'mm': '妹妹',
            'dd': '弟弟',
            'jj': '姐姐',
            'tql': '太强了',
            'zqsg': '真情实感',
            'dbq': '对不起',
            'bhys': '不好意思',
            'xjj': '小姐姐',
            'xgg': '小哥哥',
            'plmm': '漂亮妹妹',
            'pljj': '漂亮姐姐',
            'plgg': '漂亮哥哥',
            'plxgg': '漂亮小哥哥',
            'plxjj': '漂亮小姐姐'
        }
        
    def clean_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理用户数据"""
        cleaned_data = {
            'weibo_id': user_data.get('_id'),
            'nickname': user_data.get('nick_name', ''),
            'verified': user_data.get('verified', False),
            'followers_count': user_data.get('followers_count', 0),
            'following_count': user_data.get('following_count', 0),
            'posts_count': user_data.get('statuses_count', 0),
            'updated_at': datetime.now()
        }
        return cleaned_data
        
    def clean_post_data(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """清理微博数据，如果内容无意义则返回None"""
        content = post_data.get('content', '')
        cleaned_content = self.clean_comment(content)
        
        # 判断内容是否有意义
        if not self.is_meaningful_comment_batch([cleaned_content])[0]:
            return None
            
        cleaned_data = {
            'weibo_id': post_data.get('_id'),
            'user_id': post_data.get('user_id'),
            'content': cleaned_content,
            'created_at': post_data.get('created_at'),
            'reposts_count': post_data.get('retweet_count', 0),
            'comments_count': post_data.get('comment_count', 0),
            'attitudes_count': post_data.get('like_count', 0),
            'read_count': post_data.get('read_count', 0),
            'source': post_data.get('source', ''),
            'pictures': json.dumps(post_data.get('pictures', []), ensure_ascii=False),
            'video_url': post_data.get('video_url', '')
        }
        return cleaned_data
        
    def clean_comment_data(self, comment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """清理评论数据，如果内容无意义则返回None"""
        content = comment_data.get('content', '')
        cleaned_content = self.clean_comment(content)
        
        # 判断内容是否有意义
        if not self.is_meaningful_comment_batch([cleaned_content])[0]:
            return None
            
        cleaned_data = {
            'weibo_id': comment_data.get('_id'),
            'post_id': comment_data.get('tweet_id'),
            'user_id': comment_data.get('user_id'),
            'content': cleaned_content,
            'created_at': comment_data.get('created_at'),
            'like_count': comment_data.get('like_count', 0)
        }
        return cleaned_data
        
    def clean_comment(self, comment: str) -> str:
        """清理评论内容"""
        if not comment:
            return ""
            
        # 移除URL
        comment = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', comment)
        
        # 移除@用户
        comment = re.sub(r'@[\w\u4e00-\u9fff]+', '', comment)
        
        # 移除表情符号
        comment = re.sub(r'\[.*?\]', '', comment)
        
        # 移除HTML标签
        comment = re.sub(r'<[^>]+>', '', comment)
        
        # 移除多余空白字符
        comment = re.sub(r'\s+', ' ', comment).strip()
        
        return comment
        
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode()).hexdigest()
        
    def _is_meaningful_symbols(self, text: str) -> bool:
        """判断是否包含有意义的符号组合"""
        # 检查连续重复的符号
        for symbol in self.meaningful_symbols.keys():
            pattern = f"{symbol}{{3,}}"
            if re.search(pattern, text):
                return True
                
        # 检查符号组合
        symbol_patterns = [
            r'[，。！？]{2,}',
            r'\.{3,}',
            r'!{2,}',
            r'\?{2,}',
            r'~{2,}',
        ]
        
        for pattern in symbol_patterns:
            if re.search(pattern, text):
                return True
                
        return False
        
    def _is_meaningful_number(self, text: str) -> bool:
        """判断是否包含有意义的数字"""
        if text in self.meaningful_numbers:
            return True
            
        for number in self.meaningful_numbers.keys():
            if number in text:
                return True
                
        number_patterns = [
            r'(\d)\1{2,}',
            r'(\d{2,})\1{1,}',
        ]
        
        for pattern in number_patterns:
            if re.search(pattern, text):
                return True
                
        return False
        
    def _is_meaningful_abbr(self, text: str) -> bool:
        """判断是否包含有意义的英文缩写"""
        text_lower = text.lower()
        
        if text_lower in self.meaningful_abbr:
            return True
            
        for abbr in self.meaningful_abbr.keys():
            if abbr in text_lower:
                return True
                
        return False
        
    def _is_meaningless_by_pattern(self, text: str) -> bool:
        """使用预定义模式判断无意义评论"""
        for pattern in self.meaningless_patterns:
            if re.match(pattern, text):
                return True
                
        if not text.strip():
            return True
            
        if self._is_meaningful_symbols(text):
            return False
            
        if self._is_meaningful_number(text):
            return False
            
        if self._is_meaningful_abbr(text):
            return False
            
        if len(text.strip()) == 1 and not any([
            text in self.meaningful_symbols,
            text in self.meaningful_numbers,
            text.lower() in self.meaningful_abbr
        ]):
            return True
            
        return False
        
    def has_semantic_meaning_batch(self, texts: List[str]) -> List[bool]:
        """批量判断文本是否包含语义信息"""
        if not texts or not self.model:
            return [False] * len(texts)
            
        results = []
        cache_hits = 0
        
        # 检查缓存
        for text in texts:
            cache_key = self._get_cache_key(text)
            if cache_key in self.semantic_cache:
                results.append(self.semantic_cache[cache_key])
                cache_hits += 1
            else:
                results.append(None)
                
        if cache_hits == len(texts):
            return results
            
        try:
            new_texts = [text for i, text in enumerate(texts) if results[i] is None]
            
            for i in range(0, len(new_texts), self.batch_size):
                batch_texts = new_texts[i:i + self.batch_size]
                
                inputs = self.tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    
                text_embeddings = outputs.last_hidden_state[:, 0].cpu().numpy()
                norms = np.linalg.norm(text_embeddings, axis=1)
                
                for j, norm in enumerate(norms):
                    idx = i + j
                    text = new_texts[idx]
                    cache_key = self._get_cache_key(text)
                    result = norm > 0.5
                    self.semantic_cache[cache_key] = result
                    results[texts.index(text)] = result
                    
                if len(self.semantic_cache) > self.cache_size:
                    self.semantic_cache.clear()
                    
        except Exception as e:
            self.logger.error(f"批量语义判断失败: {str(e)}")
            for i, text in enumerate(texts):
                if results[i] is None:
                    results[i] = self._is_meaningless_by_pattern(text)
                    
        return results
        
    def is_meaningful_comment_batch(self, cleaned_comments: List[str]) -> List[bool]:
        """批量判断评论是否有意义"""
        if not comments:
            return []
            
        results = []
        cache_hits = 0
        
        # 检查缓存
        for comment in comments:
            cache_key = self._get_cache_key(comment)
            if cache_key in self.meaningful_cache:
                results.append(self.meaningful_cache[cache_key])
                cache_hits += 1
            else:
                results.append(None)
                
        if cache_hits == len(comments):
            return results
            
        
        # 使用BERT模型批量判断语义
        semantic_results = self.has_semantic_meaning_batch(cleaned_comments)
        
        # 使用传统方法判断无意义模式
        pattern_results = [not self._is_meaningless_by_pattern(comment) for comment in cleaned_comments]
        
        # 综合两种方法的结果
        for i, (comment, semantic_result, pattern_result) in enumerate(zip(comments, semantic_results, pattern_results)):
            if results[i] is not None:
                continue
                
            # 如果BERT模型判断有意义，或者传统方法判断有意义，则认为评论有意义
            result = semantic_result or pattern_result
            
            # 更新结果和缓存
            cache_key = self._get_cache_key(comment)
            self.meaningful_cache[cache_key] = result
            results[i] = result
            
            # 清理缓存
            if len(self.meaningful_cache) > self.cache_size:
                self.meaningful_cache.clear()
                
        return results
         
    def clean_user_data_batch(self, users_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量清理用户数据"""
        return [self.clean_user_data(user_data) for user_data in users_data]
        
    def clean_post_data_batch(self, posts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量清理帖子数据，过滤掉无意义的内容"""
        # 先清理所有内容
        cleaned_contents = []
        for post_data in posts_data:
            content = post_data.get('content', '')
            cleaned_content = self.clean_comment(content)
            cleaned_contents.append(cleaned_content)
            
        # 批量判断内容是否有意义
        meaningful_results = self.is_meaningful_comment_batch(cleaned_contents)
        
        # 根据判断结果过滤和构建数据
        cleaned_posts = []
        for post_data, cleaned_content, is_meaningful in zip(posts_data, cleaned_contents, meaningful_results):
            if is_meaningful:
                cleaned_posts.append({
                    'weibo_id': post_data.get('_id'),
                    'user_id': post_data.get('user_id'),
                    'content': cleaned_content,
                    'created_at': post_data.get('created_at'),
                    'reposts_count': post_data.get('retweet_count', 0),
                    'comments_count': post_data.get('comment_count', 0),
                    'attitudes_count': post_data.get('like_count', 0),
                    'read_count': post_data.get('read_count', 0),
                    'source': post_data.get('source', ''),
                    'pictures': json.dumps(post_data.get('pictures', []), ensure_ascii=False),
                    'video_url': post_data.get('video_url', '')
                })
        return cleaned_posts
        
    def clean_comment_data_batch(self, comments_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量清理评论数据，过滤掉无意义的内容"""
        # 先清理所有内容
        cleaned_contents = []
        for comment_data in comments_data:
            content = comment_data.get('content', '')
            cleaned_content = self.clean_comment(content)
            cleaned_contents.append(cleaned_content)
            
        # 批量判断内容是否有意义
        meaningful_results = self.is_meaningful_comment_batch(cleaned_contents)
        
        # 根据判断结果过滤和构建数据
        cleaned_comments = []
        for comment_data, cleaned_content, is_meaningful in zip(comments_data, cleaned_contents, meaningful_results):
            if is_meaningful:
                cleaned_comments.append({
                    'weibo_id': comment_data.get('_id'),
                    'post_id': comment_data.get('tweet_id'),
                    'user_id': comment_data.get('user_id'),
                    'content': cleaned_content,
                    'created_at': comment_data.get('created_at'),
                    'like_count': comment_data.get('like_count', 0)
                })
        return cleaned_comments

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建数据清洗器实例
    cleaner = DataCleaner(batch_size=32, cache_size=10000)
    
    # 测试评论清洗
    test_comments = [
        "这个明星真棒！[微笑]",
        "666",
        "好",
        "这个演技太差了！",
        "转发微博",
        "//@用户A: 支持！",
        "https://example.com",
        "来自北京",
        "来自 上海",
        "来自广东 广州",
        "，，，",  # 连续逗号
        "。。。",  # 连续句号
        "？？？",  # 连续问号
        "！！！",  # 连续感叹号
        "...",    # 省略号
        "~~~",    # 波浪号
        "233",    # 网络用语
        "555",    # 网络用语
        "yyds",   # 英文缩写
        "awsl",   # 英文缩写
        "nb",     # 英文缩写
        "666666", # 重复数字
        "999999", # 重复数字
        "5201314" # 数字组合
    ] * 10  # 重复10次以测试批量处理
    
    print("=== 测试批量评论清洗 ===")
    start_time = datetime.now()
    
    # 批量清洗
    cleaned_comments = cleaner.clean_comments_batch(test_comments)
    meaningful_results = cleaner.is_meaningful_comment_batch(cleaned_comments)
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    print(f"处理 {len(test_comments)} 条评论用时: {processing_time:.2f} 秒")
    print(f"平均每条评论处理时间: {processing_time/len(test_comments)*1000:.2f} 毫秒")
    
    # 显示部分结果
    for i, (comment, cleaned, is_meaningful) in enumerate(zip(test_comments[:10], cleaned_comments[:10], meaningful_results[:10])):
        print(f"\n评论 {i+1}:")
        print(f"原文: {comment}")
        print(f"清洗后: {cleaned}")
        print(f"是否有意义: {is_meaningful}")
        
    # 测试缓存效果
    print("\n=== 测试缓存效果 ===")
    start_time = datetime.now()
    meaningful_results2 = cleaner.is_meaningful_comment_batch(cleaned_comments)
    end_time = datetime.now()
    cache_time = (end_time - start_time).total_seconds()
    
    print(f"使用缓存处理 {len(test_comments)} 条评论用时: {cache_time:.2f} 秒")
    print(f"缓存加速比: {processing_time/cache_time:.2f}倍")