from typing import Dict, List, Any, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from sqlalchemy import create_engine, text
import logging
from pathlib import Path
import json

class ReportSender:
    def __init__(self, db_url: str, smtp_config: Dict[str, Any]):
        """
        初始化报告发送器
        
        Args:
            db_url: 数据库连接URL
            smtp_config: SMTP服务器配置
        """
        self.engine = create_engine(db_url)
        self.smtp_config = smtp_config
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
    def send_report(self, report_id: int) -> bool:
        """
        发送报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            是否发送成功
        """
        try:
            # 获取报告信息
            report = self._get_report(report_id)
            if not report:
                raise ValueError(f"报告不存在: {report_id}")
                
            # 获取接收人列表
            recipients = self._get_recipients(report['template_id'])
            if not recipients:
                raise ValueError(f"报告没有配置接收人: {report_id}")
                
            # 发送报告
            success_count = 0
            for recipient in recipients:
                if self._send_to_recipient(report, recipient):
                    success_count += 1
                    
            # 更新报告状态
            self._update_report_status(report_id, success_count > 0)
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"发送报告失败: {str(e)}")
            self._update_report_status(report_id, False, str(e))
            return False
            
    def _get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """获取报告信息"""
        query = """
            SELECT r.*, t.template_name
            FROM report_records r
            JOIN report_templates t ON r.template_id = t.id
            WHERE r.id = :report_id
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'report_id': report_id}).fetchone()
            
        return dict(result) if result else None
        
    def _get_recipients(self, template_id: int) -> List[Dict[str, Any]]:
        """获取报告接收人列表"""
        query = """
            SELECT * FROM report_recipients
            WHERE template_id = :template_id AND is_active = TRUE
        """
        
        with self.engine.connect() as conn:
            results = conn.execute(text(query), {'template_id': template_id}).fetchall()
            
        return [dict(row) for row in results]
        
    def _send_to_recipient(self, report: Dict[str, Any],
                          recipient: Dict[str, Any]) -> bool:
        """发送报告给单个接收人"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['Subject'] = f"{report['template_name']} - {report['report_time'].strftime('%Y-%m-%d')}"
            msg['From'] = self.smtp_config['username']
            msg['To'] = recipient['email']
            
            # 添加正文
            msg.attach(MIMEText(report['report_content'], 'html'))
            
            # 添加附件
            if 'attachments' in report:
                for attachment in report['attachments']:
                    with open(attachment['path'], 'rb') as f:
                        part = MIMEApplication(f.read())
                        part.add_header('Content-Disposition', 'attachment',
                                      filename=attachment['name'])
                        msg.attach(part)
                        
            # 发送邮件
            with smtplib.SMTP_SSL(self.smtp_config['host'],
                                self.smtp_config['port']) as server:
                server.login(self.smtp_config['username'],
                           self.smtp_config['password'])
                server.send_message(msg)
                
            # 记录发送日志
            self._log_send_record(report['id'], recipient['id'], True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"发送报告给接收人失败: {str(e)}")
            self._log_send_record(report['id'], recipient['id'], False, str(e))
            return False
            
    def _update_report_status(self, report_id: int, success: bool,
                             error_message: str = None):
        """更新报告状态"""
        query = """
            UPDATE report_records
            SET status = :status,
                updated_at = :updated_at
            WHERE id = :report_id
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(query), {
                'report_id': report_id,
                'status': 'sent' if success else 'failed',
                'updated_at': datetime.now()
            })
            
    def _log_send_record(self, report_id: int, recipient_id: int,
                        success: bool, error_message: str = None):
        """记录发送日志"""
        query = """
            INSERT INTO report_send_logs
            (report_id, recipient_id, send_time, send_status,
             error_message, created_at)
            VALUES
            (:report_id, :recipient_id, :send_time, :send_status,
             :error_message, :created_at)
        """
        
        now = datetime.now()
        
        with self.engine.connect() as conn:
            conn.execute(text(query), {
                'report_id': report_id,
                'recipient_id': recipient_id,
                'send_time': now,
                'send_status': 'success' if success else 'failed',
                'error_message': error_message,
                'created_at': now
            }) 