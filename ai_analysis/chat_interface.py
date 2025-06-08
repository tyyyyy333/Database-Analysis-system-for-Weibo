from typing import Dict, List, Any
import streamlit as st
from .ai_analyzer import AIAnalyzer
import json
from pathlib import Path

class ChatInterface:
    """AI聊天界面"""
    
    def __init__(self, config: Dict):
        self.analyzer = AIAnalyzer(config)
        self._load_chat_history()
    
    def _load_chat_history(self):
        """加载聊天历史"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
    
    def _save_chat_history(self):
        """保存聊天历史"""
        history_file = Path(__file__).parent / 'data' / 'chat_history.json'
        history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=2)
    
    def _parse_user_input(self, user_input: str) -> Dict:
        """解析用户输入
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            解析结果
        """
        # TODO: 实现更复杂的自然语言理解
        if "趋势" in user_input:
            return {'type': 'trend', 'input': user_input}
        elif "情感" in user_input:
            return {'type': 'sentiment', 'input': user_input}
        elif "粉丝" in user_input:
            return {'type': 'fan', 'input': user_input}
        elif "比较" in user_input:
            return {'type': 'comparison', 'input': user_input}
        else:
            return {'type': 'unknown', 'input': user_input}
    
    def _generate_response(self, parsed_input: Dict) -> str:
        """生成响应
        
        Args:
            parsed_input: 解析后的用户输入
            
        Returns:
            响应文本
        """
        try:
            if parsed_input['type'] == 'trend':
                # 提取参数
                # TODO: 实现更智能的参数提取
                celebrity = "测试明星"  # 示例
                metric = "likes"  # 示例
                time_range = "7 DAY"  # 示例
                
                result = self.analyzer.analyze_trend(celebrity, metric, time_range)
                if result['status'] == 'success':
                    return f"分析结果：\n{result['data']}"
                else:
                    return f"分析失败：{result['message']}"
            
            elif parsed_input['type'] == 'sentiment':
                celebrity = "测试明星"  # 示例
                result = self.analyzer.analyze_sentiment(celebrity)
                if result['status'] == 'success':
                    return f"情感分析结果：\n{result['data']}"
                else:
                    return f"分析失败：{result['message']}"
            
            elif parsed_input['type'] == 'fan':
                celebrity = "测试明星"  # 示例
                result = self.analyzer.analyze_fans(celebrity)
                if result['status'] == 'success':
                    return f"粉丝分析结果：\n{result['data']}"
                else:
                    return f"分析失败：{result['message']}"
            
            elif parsed_input['type'] == 'comparison':
                celebrity1 = "明星1"  # 示例
                celebrity2 = "明星2"  # 示例
                metric = "likes"  # 示例
                result = self.analyzer.compare_celebrities(celebrity1, celebrity2, metric)
                if result['status'] == 'success':
                    return f"比较分析结果：\n{result['data']}"
                else:
                    return f"分析失败：{result['message']}"
            
            else:
                return "抱歉，我暂时无法理解您的问题。您可以询问关于趋势分析、情感分析、粉丝分析或明星比较的问题。"
        
        except Exception as e:
            return f"处理请求时发生错误：{str(e)}"
    
    def run(self):
        """运行聊天界面"""
        st.title("明星舆情分析助手")
        
        # 显示聊天历史
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # 用户输入
        if user_input := st.chat_input("请输入您的问题"):
            # 添加用户消息到历史
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # 显示用户消息
            with st.chat_message("user"):
                st.write(user_input)
            
            # 解析用户输入
            parsed_input = self._parse_user_input(user_input)
            
            # 生成响应
            response = self._generate_response(parsed_input)
            
            # 添加助手响应到历史
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # 显示助手响应
            with st.chat_message("assistant"):
                st.write(response)
            
            # 保存聊天历史
            self._save_chat_history()

if __name__ == "__main__":
    # 测试配置
    test_config = {
        'database_url': 'mysql://root:123456@localhost/celebrity_sentiment',
        'openai_api_key': 'your-api-key-here'
    }
    
    # 创建聊天界面实例
    chat = ChatInterface(test_config)
    
    # 测试输入解析
    test_inputs = [
        "分析张三最近一周的点赞趋势",
        "查看李四的评论情感分布",
        "分析王五的粉丝画像",
        "比较赵六和钱七的互动数据",
        "这是一个无法理解的问题"
    ]
    
    print("测试输入解析:")
    for user_input in test_inputs:
        parsed = chat._parse_user_input(user_input)
        print(f"\n输入: {user_input}")
        print(f"解析结果: {parsed}")
        
        # 测试响应生成
        response = chat._generate_response(parsed)
        print(f"生成的响应: {response}")
    
    print("\n要启动完整的聊天界面，请运行:")
    print("streamlit run ai_analysis/chat_interface.py") 