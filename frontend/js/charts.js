// 图表配置
const chartConfig = {
    realtime: {
        type: 'line',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    },
    sentiment: {
        type: 'pie',
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    }
};

// 更新实时监控图表
function updateRealtimeChart(data) {
    const ctx = document.getElementById('realtime-chart');
    if (!ctx) return;
    
    // 准备数据
    const chartData = {
        labels: data.map(item => new Date(item.timestamp)),
        datasets: [{
            label: '情感得分',
            data: data.map(item => item.score),
            borderColor: '#3498db',
            tension: 0.4,
            fill: false
        }]
    };
    
    // 创建或更新图表
    if (window.realtimeChart) {
        window.realtimeChart.data = chartData;
        window.realtimeChart.update();
    } else {
        window.realtimeChart = new Chart(ctx, {
            type: chartConfig.realtime.type,
            data: chartData,
            options: chartConfig.realtime.options
        });
    }
}

// 更新情感分布图表
function updateSentimentChart(data) {
    const ctx = document.getElementById('sentiment-chart');
    if (!ctx) return;
    
    // 准备数据
    const chartData = {
        labels: ['正面', '中性', '负面'],
        datasets: [{
            data: [
                data.positive,
                data.neutral,
                data.negative
            ],
            backgroundColor: [
                '#2ecc71',
                '#95a5a6',
                '#e74c3c'
            ]
        }]
    };
    
    // 创建或更新图表
    if (window.sentimentChart) {
        window.sentimentChart.data = chartData;
        window.sentimentChart.update();
    } else {
        window.sentimentChart = new Chart(ctx, {
            type: chartConfig.sentiment.type,
            data: chartData,
            options: chartConfig.sentiment.options
        });
    }
}

// 更新热点话题列表
function updateHotTopics(topics) {
    const container = document.getElementById('hot-topics');
    if (!container) return;
    
    const html = topics.map(topic => `
        <div class="topic-item">
            <span class="topic-name">${topic.name}</span>
            <span class="topic-count">${topic.count}</span>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// 更新告警信息列表
function updateAlertsList(alerts) {
    const container = document.getElementById('alerts-list');
    if (!container) return;
    
    const html = alerts.map(alert => `
        <div class="alert-item ${alert.level}">
            <div class="alert-time">${formatDate(alert.timestamp)}</div>
            <div class="alert-content">${alert.content}</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// 添加图表样式
const style = document.createElement('style');
style.textContent = `
    .topic-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem;
        border-bottom: 1px solid #eee;
    }
    
    .topic-name {
        color: #2c3e50;
    }
    
    .topic-count {
        color: #7f8c8d;
    }
    
    .alert-item {
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
        background-color: #f8f9fa;
    }
    
    .alert-item.high {
        border-left: 4px solid #e74c3c;
    }
    
    .alert-item.medium {
        border-left: 4px solid #f1c40f;
    }
    
    .alert-item.low {
        border-left: 4px solid #3498db;
    }
    
    .alert-time {
        font-size: 0.8rem;
        color: #7f8c8d;
        margin-bottom: 0.25rem;
    }
    
    .alert-content {
        color: #2c3e50;
    }
`;

document.head.appendChild(style); 