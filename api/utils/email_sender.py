import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional
import logging
from pathlib import Path

class EmailSender:
    """邮件发送器，用于发送分析报告和告警信息"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """
        初始化邮件发送器
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            username: 邮箱用户名
            password: 邮箱密码
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
        
    def send_email(
        self,
        to_addrs: List[str],
        subject: str,
        content: str,
        attachments: Optional[List[str]] = None,
        cc_addrs: Optional[List[str]] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_addrs: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            attachments: 附件路径列表
            cc_addrs: 抄送人列表
            
        Returns:
            发送是否成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_addrs)
            if cc_addrs:
                msg['Cc'] = ', '.join(cc_addrs)
            msg['Subject'] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(content, 'html'))
            
            # 添加附件
            if attachments:
                for attachment in attachments:
                    file_path = Path(attachment)
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            part = MIMEApplication(f.read())
                            part.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=file_path.name
                            )
                            msg.attach(part)
                    else:
                        self.logger.warning(f"附件不存在: {attachment}")
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                
                # 获取所有收件人
                all_recipients = to_addrs + (cc_addrs or [])
                server.sendmail(self.username, all_recipients, msg.as_string())
                
            self.logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False
            
    def send_alert_email(
        self,
        to_addrs: List[str],
        alert_type: str,
        alert_content: str,
        alert_level: str = 'normal'
    ) -> bool:
        """
        发送告警邮件
        
        Args:
            to_addrs: 收件人列表
            alert_type: 告警类型
            alert_content: 告警内容
            alert_level: 告警级别
            
        Returns:
            发送是否成功
        """
        subject = f"[{alert_level.upper()}] {alert_type} 告警"
        
        # 根据告警级别设置不同的样式
        if alert_level == 'high':
            style = 'color: red; font-weight: bold;'
        elif alert_level == 'medium':
            style = 'color: orange; font-weight: bold;'
        else:
            style = 'color: blue;'
            
        content = f"""
        <html>
            <body>
                <h2 style="{style}">{subject}</h2>
                <div style="margin: 20px 0;">
                    {alert_content}
                </div>
                <p style="color: gray; font-size: 12px;">
                    此邮件由系统自动发送，请勿直接回复。
                </p>
            </body>
        </html>
        """
        
        return self.send_email(to_addrs, subject, content)
        
    def send_report_email(
        self,
        to_addrs: List[str],
        report_title: str,
        report_content: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        发送报告邮件
        
        Args:
            to_addrs: 收件人列表
            report_title: 报告标题
            report_content: 报告内容
            attachments: 附件路径列表
            
        Returns:
            发送是否成功
        """
        subject = f"分析报告: {report_title}"
        
        content = f"""
        <html>
            <body>
                <h2 style="color: #2c3e50;">{report_title}</h2>
                <div style="margin: 20px 0;">
                    {report_content}
                </div>
                <p style="color: gray; font-size: 12px;">
                    此邮件由系统自动发送，请勿直接回复。
                </p>
            </body>
        </html>
        """
        
        return self.send_email(to_addrs, subject, content, attachments) 