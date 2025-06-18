import os
import logging
import torch
from pathlib import Path
from transformers import BertTokenizer, BertModel
from huggingface_hub import snapshot_download
import shutil


class ModelManager:
    """模型管理器，用于处理模型的本地化下载和管理"""
    
    def __init__(self, model_dir: str = "models/weights"):
        self.logger = logging.getLogger(__name__)
        self.model_dir = Path(model_dir)
        self.bert_model_name = "bert-base-chinese"
        self.bert_dir = self.model_dir / self.bert_model_name.replace('\\', '/')
        
        # 确保模型目录存在
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def _check_model_exists(self) -> bool:
        """检查模型是否已下载"""
        required_files = [
            "config.json",
            "pytorch_model.bin",
            "vocab.txt"
        ]
        
        return all((self.bert_dir / file).exists() for file in required_files)
        
    def _download_model(self) -> bool:
        """下载模型到本地"""
        try:
            self.logger.info(f"开始下载模型 {self.bert_model_name}...")
            
            # 使用huggingface_hub下载模型
            snapshot_download(
                repo_id=self.bert_model_name,
                local_dir=str(self.bert_dir),
                local_dir_use_symlinks=False
            )
            
            self.logger.info("模型下载完成")
            return True
            
        except Exception as e:
            self.logger.error(f"模型下载失败: {str(e)}")
            return False
            
    def _cleanup_download(self):
        """清理下载过程中的临时文件"""
        try:
            temp_dir = self.model_dir / "tmp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {str(e)}")
            
    def get_bert_model(self) -> tuple[BertTokenizer, BertModel]:
        """获取BERT模型和分词器
        
        Returns:
            tuple: (tokenizer, model)
        """
        # 检查模型是否存在
        if not self._check_model_exists():
            # 下载模型
            if not self._download_model():
                print("模型下载失败")  # raise RuntimeError("模型下载失败")
            self._cleanup_download()
            
        try:
            # 加载模型和分词器
            self.logger.info("加载BERT模型和分词器...")
            
            # 设置设备
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # 加载分词器
            tokenizer = BertTokenizer.from_pretrained(
                str(self.bert_dir),
                local_files_only=True
            )
            
            # 加载模型
            model = BertModel.from_pretrained(
                str(self.bert_dir),
                local_files_only=True
            )
            model.to(device)
            model.eval()
            
            self.logger.info(f"BERT模型加载成功，使用设备: {device}")
            return tokenizer, model
            
        except Exception as e:
            self.logger.error(f"模型加载失败: {str(e)}")
            raise
            
    def get_model_info(self) -> dict:
        """获取模型信息"""
        info = {
            "model_name": self.bert_model_name,
            "model_dir": str(self.bert_dir),
            "is_downloaded": self._check_model_exists(),
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }
        
        if self._check_model_exists():
            # 获取模型文件大小
            total_size = 0
            for file in self.bert_dir.glob("**/*"):
                if file.is_file():
                    total_size += file.stat().st_size
            info["model_size"] = f"{total_size / 1024 / 1024:.2f}MB"
            
        return info

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建模型管理器实例
    model_manager = ModelManager()
    
    # 获取模型信息
    info = model_manager.get_model_info()
    print("\n=== 模型信息 ===")
    for key, value in info.items():
        print(f"{key}: {value}")
        
    # 测试模型加载
    print("\n=== 测试模型加载 ===")
    try:
        tokenizer, model = model_manager.get_bert_model()
        print("模型加载成功")
        
        # 测试模型推理
        test_text = "这是一个测试文本"
        inputs = tokenizer(test_text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
        print("模型推理成功")
        
    except Exception as e:
        print(f"模型加载失败: {str(e)}") 
 
 