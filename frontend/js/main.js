// 全局变量
const API_BASE_URL = 'http://localhost:5000/api';

// 工具函数
function formatDate(date) {
    return new Date(date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // 添加到页面
    document.body.appendChild(notification);

    // 3秒后移除
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 初始化各个模块
    initNavigation();
    initDashboard();
    initAnalysis();
    initAlerts();
    initSettings();
});

// 导航功能
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            showSection(targetId);
        });
    });
}

function showSection(sectionId) {
    // 隐藏所有section
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    // 显示目标section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
}

// 仪表盘功能
function initDashboard() {
    // 加载实时数据
    loadRealtimeData();
    
    // 设置定时刷新
    setInterval(loadRealtimeData, 60000); // 每分钟刷新一次
}

async function loadRealtimeData() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/realtime`);
        const data = await response.json();
        
        // 更新各个图表
        updateRealtimeChart(data.realtime);
        updateSentimentChart(data.sentiment);
        updateHotTopics(data.topics);
        updateAlertsList(data.alerts);
    } catch (error) {
        console.error('加载实时数据失败:', error);
        showNotification('加载实时数据失败', 'error');
    }
}

// 分析报告功能
function initAnalysis() {
    const generateButton = document.getElementById('generate-report');
    const timeRange = document.getElementById('time-range');
    
    generateButton.addEventListener('click', () => {
        generateReport(timeRange.value);
    });
}

async function generateReport(timeRange) {
    try {
        const response = await fetch(`${API_BASE_URL}/analysis/report?timeRange=${timeRange}`);
        const data = await response.json();
        
        // 显示报告内容
        const reportContent = document.getElementById('report-content');
        reportContent.innerHTML = formatReportContent(data);
    } catch (error) {
        console.error('生成报告失败:', error);
        showNotification('生成报告失败', 'error');
    }
}

function formatReportContent(data) {
    // 格式化报告内容
    return `
        <div class="report-section">
            <h3>总体概况</h3>
            <p>${data.summary}</p>
        </div>
        <div class="report-section">
            <h3>情感分析</h3>
            <p>${data.sentiment}</p>
        </div>
        <div class="report-section">
            <h3>热点话题</h3>
            <ul>
                ${data.topics.map(topic => `<li>${topic}</li>`).join('')}
            </ul>
        </div>
    `;
}

// 告警管理功能
function initAlerts() {
    const refreshButton = document.getElementById('refresh-alerts');
    const alertLevel = document.getElementById('alert-level');
    
    refreshButton.addEventListener('click', () => {
        loadAlerts(alertLevel.value);
    });
    
    // 初始加载
    loadAlerts('all');
}

async function loadAlerts(level) {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts?level=${level}`);
        const data = await response.json();
        
        // 更新告警表格
        const alertsTable = document.getElementById('alerts-table');
        alertsTable.innerHTML = formatAlertsTable(data);
    } catch (error) {
        console.error('加载告警失败:', error);
        showNotification('加载告警失败', 'error');
    }
}

function formatAlertsTable(alerts) {
    return `
        <table>
            <thead>
                <tr>
                    <th>时间</th>
                    <th>级别</th>
                    <th>内容</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
                ${alerts.map(alert => `
                    <tr>
                        <td>${formatDate(alert.timestamp)}</td>
                        <td>${alert.level}</td>
                        <td>${alert.content}</td>
                        <td>${alert.status}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// 系统设置功能
function initSettings() {
    const settingsForm = document.getElementById('settings-form');
    
    // 加载当前设置
    loadSettings();
    
    // 监听表单提交
    settingsForm.addEventListener('submit', (e) => {
        e.preventDefault();
        saveSettings();
    });
}

async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE_URL}/settings`);
        const data = await response.json();
        
        // 填充表单
        document.getElementById('email').value = data.email;
        document.getElementById('alert-threshold').value = data.alertThreshold;
        document.getElementById('update-interval').value = data.updateInterval;
    } catch (error) {
        console.error('加载设置失败:', error);
        showNotification('加载设置失败', 'error');
    }
}

async function saveSettings() {
    const formData = {
        email: document.getElementById('email').value,
        alertThreshold: document.getElementById('alert-threshold').value,
        updateInterval: document.getElementById('update-interval').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            showNotification('设置保存成功', 'success');
        } else {
            throw new Error('保存失败');
        }
    } catch (error) {
        console.error('保存设置失败:', error);
        showNotification('保存设置失败', 'error');
    }
} 