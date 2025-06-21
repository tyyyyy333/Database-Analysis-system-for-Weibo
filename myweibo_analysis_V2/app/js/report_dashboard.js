// 全局变量
let reports = [];
let isManageMode = false;

// 创建浮动球动画
function createFloatingBalls() {
    const container = document.getElementById('floatingBalls');
    if (!container) return;
    
    const colors = ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.2)'];
    
    for (let i = 0; i < 10; i++) {
        const ball = document.createElement('div');
        ball.className = 'ball';
        ball.style.width = Math.random() * 100 + 50 + 'px';
        ball.style.height = ball.style.width;
        ball.style.left = Math.random() * 100 + '%';
        ball.style.top = Math.random() * 100 + '%';
        ball.style.animationDelay = Math.random() * 5 + 's';
        ball.style.background = colors[Math.floor(Math.random() * colors.length)];
        container.appendChild(ball);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 创建浮动球动画
    createFloatingBalls();
    
    // 加载报告列表
    loadReports();
    
    // 导航栏点击事件处理
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('onclick').match(/window\.location\.href='([^']+)'/)[1];
        if (currentPath === href) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
});

// 加载报告列表
async function loadReports() {
    try {
        const response = await fetch('/api/reports');
        if (response.ok) {
            const data = await response.json();
            reports = data.reports || [];
            renderReports();
        } else {
            console.error('获取报告列表失败');
            showNotification('获取报告列表失败', 'error');
        }
    } catch (error) {
        console.error('获取报告列表错误:', error);
        showNotification('获取报告列表失败', 'error');
    }
}

// 渲染报告列表
function renderReports() {
    const grid = document.getElementById('reportsGrid');
    
    // 清空现有报告卡片
    grid.innerHTML = '';
    
    // 渲染报告卡片
    reports.forEach(report => {
        const card = createReportCard(report);
        grid.appendChild(card);
    });
    
    // 如果没有报告，显示提示信息
    if (reports.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 50px; color: var(--inputColor); opacity: 0.7;">
                <i class="ri-user-star-line" style="font-size: 3rem; margin-bottom: 20px; display: block;"></i>
                <h3>暂无明星监控记录</h3>
                <p>请在首页搜索并添加明星进行监控</p>
            </div>
        `;
    }
}

// 创建报告卡片
function createReportCard(report) {
    const card = document.createElement('div');
    card.className = 'report-card';
    card.onclick = () => viewStar(report.star_id);
    
    // 获取明星昵称（这里需要从weibo_user表获取）
    const starName = report.star_nick_name || report.star_id;
    
    card.innerHTML = `
        <div class="checkbox" onclick="event.stopPropagation(); toggleReportSelection(this)"></div>
        <div class="report-card-header">
            <div class="report-card-icon">
                <i class="ri-user-star-line"></i>
            </div>
            <div class="report-card-title">${starName}</div>
        </div>
        <div class="report-card-info">
            <div class="report-card-info-item">
                <div class="report-card-info-value">${formatNumber(report.follower_count)}</div>
                <div class="report-card-info-label">粉丝数</div>
            </div>
            <div class="report-card-info-item">
                <div class="report-card-info-value">${formatNumber(report.following_count)}</div>
                <div class="report-card-info-label">关注数</div>
            </div>
        </div>
        <div class="report-card-description">
            ${report.hot_weibo || '暂无热门微博'}
        </div>
        <div class="report-card-actions">
            <button class="report-action-btn delete" onclick="event.stopPropagation(); deleteReport('${report.star_id}')">
                <i class="ri-delete-bin-line"></i>
                删除
            </button>
        </div>
    `;
    
    return card;
}

// 格式化数字
function formatNumber(num) {
    if (!num) return '0';
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    return num.toString();
}

// 管理模式切换
function toggleManageMode() {
    const checkboxes = document.querySelectorAll('.checkbox');
    const manageBtn = document.getElementById('manageBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const batchDeleteBtn = document.getElementById('batchDeleteBtn');
    
    checkboxes.forEach(checkbox => {
        checkbox.classList.add('visible');
    });
    
    manageBtn.style.display = 'none';
    cancelBtn.style.display = 'flex';
    batchDeleteBtn.style.display = 'flex';
}

function cancelManageMode() {
    const checkboxes = document.querySelectorAll('.checkbox');
    const manageBtn = document.getElementById('manageBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const batchDeleteBtn = document.getElementById('batchDeleteBtn');
    
    checkboxes.forEach(checkbox => {
        checkbox.classList.remove('visible', 'checked');
    });
    
    manageBtn.style.display = 'flex';
    cancelBtn.style.display = 'none';
    batchDeleteBtn.style.display = 'none';
}

// 报告选择切换
function toggleReportSelection(checkbox) {
    const card = checkbox.closest('.report-card');
    checkbox.classList.toggle('checked');
    card.classList.toggle('selected');
}

// 查看报告
function viewReport(reportId) {
    console.log('查看报告:', reportId);
    showNotification('查看报告功能开发中...', 'info');
}

// 查看明星
function viewStar(starId) {
    console.log('查看明星报告:', starId);
    window.location.href = `/report_detail?star_id=${starId}`;
}

// 下载报告
async function downloadReport(reportId) {
    try {
        const response = await fetch(`/api/reports/${reportId}/download`);
        const data = await response.json();
        
        if (response.ok) {
            showNotification('报告下载成功', 'success');
        } else {
            showNotification(data.message || '下载失败', 'error');
        }
    } catch (error) {
        console.error('下载报告错误:', error);
        showNotification('下载失败，请稍后重试', 'error');
    }
}

// 删除报告
async function deleteReport(reportId) {
    if (confirm('确定要删除这个明星监控吗？')) {
        try {
            const response = await fetch(`/api/reports/${reportId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (response.ok) {
                showNotification('明星监控删除成功', 'success');
                loadReports(); // 重新加载报告列表
            } else {
                showNotification(data.message || '删除失败', 'error');
            }
        } catch (error) {
            console.error('删除报告错误:', error);
            showNotification('删除失败，请稍后重试', 'error');
        }
    }
}

// 获取选中的报告ID列表
function getSelectedReportIds() {
    const selectedCheckboxes = document.querySelectorAll('.checkbox.checked');
    const selectedIds = [];
    
    selectedCheckboxes.forEach(checkbox => {
        const card = checkbox.closest('.report-card');
        // 从卡片的删除按钮中获取star_id
        const deleteBtn = card.querySelector('.report-action-btn.delete');
        if (deleteBtn) {
            const onclick = deleteBtn.getAttribute('onclick');
            const match = onclick.match(/deleteReport\('([^']+)'\)/);
            if (match) {
                selectedIds.push(match[1]);
            }
        }
    });
    
    return selectedIds;
}

// 批量删除报告
async function batchDeleteReports() {
    const selectedIds = getSelectedReportIds();
    
    if (selectedIds.length === 0) {
        showNotification('请先选择要删除的报告', 'error');
        return;
    }
    
    const confirmMessage = `确定要删除选中的 ${selectedIds.length} 个明星监控吗？此操作不可恢复。`;
    
    if (confirm(confirmMessage)) {
        try {
            // 逐个删除选中的报告
            let successCount = 0;
            let failCount = 0;
            
            for (const reportId of selectedIds) {
                try {
                    const response = await fetch(`/api/reports/${reportId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        successCount++;
                    } else {
                        failCount++;
                    }
                } catch (error) {
                    console.error(`删除报告 ${reportId} 失败:`, error);
                    failCount++;
                }
            }
            
            // 显示删除结果
            if (successCount > 0) {
                showNotification(`成功删除 ${successCount} 个明星监控`, 'success');
                if (failCount > 0) {
                    showNotification(`${failCount} 个删除失败`, 'error');
                }
                // 重新加载报告列表
                loadReports();
                // 退出管理模式
                cancelManageMode();
            } else {
                showNotification('删除失败，请稍后重试', 'error');
            }
            
        } catch (error) {
            console.error('批量删除错误:', error);
            showNotification('批量删除失败，请稍后重试', 'error');
        }
    }
}

// 显示通知消息
function showNotification(message, type) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        max-width: 300px;
        word-wrap: break-word;
        animation: slideIn 0.3s ease;
    `;

    // 根据类型设置样式
    if (type === 'success') {
        notification.style.backgroundColor = '#27ae60';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#e74c3c';
    } else if (type === 'info') {
        notification.style.backgroundColor = '#3498db';
    } else {
        notification.style.backgroundColor = '#3498db';
    }

    notification.textContent = message;
    document.body.appendChild(notification);

    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style); 