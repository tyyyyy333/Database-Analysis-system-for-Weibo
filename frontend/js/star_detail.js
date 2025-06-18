// 获取URL中的明星ID
const urlParams = new URLSearchParams(window.location.search);
const starId = urlParams.get('star_id');

if (!starId) {
    showErrorMessage('未找到明星ID');
} else {
    // 获取明星数据
    fetchStarData();
}

// 获取明星数据
async function fetchStarData() {
    try {
        // 获取基本信息
        const basicResponse = await fetch(`/api/stars/${starId}/basic`);
        if (!basicResponse.ok) throw new Error('获取基本信息失败');
        const basicData = await basicResponse.json();
        updateStarInfo(basicData);

        // 获取情感分析数据
        const sentimentResponse = await fetch(`/api/stars/${starId}/sentiment`);
        if (!sentimentResponse.ok) throw new Error('获取情感分析数据失败');
        const sentimentData = await sentimentResponse.json();
        updateSentimentCharts(sentimentData);

        // 获取黑粉分析数据
        const haterResponse = await fetch(`/api/stars/${starId}/hater`);
        if (!haterResponse.ok) throw new Error('获取黑粉分析数据失败');
        const haterData = await haterResponse.json();
        updateHaterData(haterData);

        // 获取热度分析数据
        const heatResponse = await fetch(`/api/stars/${starId}/heat`);
        if (!heatResponse.ok) throw new Error('获取热度分析数据失败');
        const heatData = await heatResponse.json();
        updateHeatCharts(heatData);

    } catch (error) {
        showErrorMessage('获取数据失败：' + error.message);
    }
}

// 更新明星基本信息
function updateStarInfo(data) {
    document.getElementById('starName').textContent = data.name;
    document.getElementById('starAvatar').textContent = data.name.charAt(0);
    document.getElementById('starUrl').href = data.weibo_url;
    document.getElementById('starUrlText').textContent = data.weibo_url;
    document.getElementById('starStatus').textContent = data.status;
    document.getElementById('starIntro').textContent = data.introduction;

    // 更新指标卡片
    document.getElementById('fansCount').textContent = data.fans_count.toLocaleString();
    document.getElementById('postCount').textContent = data.post_count.toLocaleString();
    document.getElementById('blackFanCount').textContent = data.black_fan_count.toLocaleString();
    document.getElementById('sentimentScore').textContent = data.sentiment_score.toFixed(2);
}

// 更新情感分析图表
function updateSentimentCharts(data) {
    // 情感分布饼图
    const sentimentChart = echarts.init(document.getElementById('sentimentChart'));
    sentimentChart.setOption({
        title: {
            text: '情感分布',
            left: 'center',
            textStyle: {
                color: '#FFB7C5'
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {
                color: '#FFB7C5'
            }
        },
        series: [{
            name: '情感分布',
            type: 'pie',
            radius: '50%',
            data: [
                { value: data.positive_count, name: '正面', itemStyle: { color: '#91cc75' } },
                { value: data.neutral_count, name: '中性', itemStyle: { color: '#fac858' } },
                { value: data.negative_count, name: '负面', itemStyle: { color: '#ee6666' } }
            ],
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    });

    // 情感趋势折线图
    const trendChart = echarts.init(document.getElementById('heatTrendChart'));
    trendChart.setOption({
        title: {
            text: '情感趋势',
            left: 'center',
            textStyle: {
                color: '#FFB7C5'
            }
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: data.trend_dates,
            axisLabel: {
                color: '#FFB7C5'
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                color: '#FFB7C5'
            }
        },
        series: [{
            data: data.trend_scores,
            type: 'line',
            smooth: true,
            lineStyle: {
                color: '#FFB7C5'
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(255, 183, 197, 0.3)'
                }, {
                    offset: 1,
                    color: 'rgba(255, 183, 197, 0.1)'
                }])
            }
        }]
    });
}

// 更新黑粉分析数据
function updateHaterData(data) {
    // 更新黑粉统计数据
    document.getElementById('total-hater-count').textContent = data.total_count.toLocaleString();
    document.getElementById('active-hater-count').textContent = data.active_count.toLocaleString();
    document.getElementById('hater-growth-rate').textContent = data.growth_rate.toFixed(2) + '%';
    document.getElementById('hater-influence-score').textContent = data.influence_score.toFixed(2);

    // 更新分数分布图
    const scoreChart = echarts.init(document.getElementById('score-distribution-chart'));
    scoreChart.setOption({
        title: {
            text: '黑粉分数分布',
            left: 'center',
            textStyle: { color: '#FFB7C5' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        },
        grid: {
            top: '15%',
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['低分(0-0.5)', '中分(0.5-0.8)', '高分(0.8-1.0)'],
            axisLabel: { color: '#FFB7C5' },
            axisLine: { lineStyle: { color: '#FFB7C5' } }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#FFB7C5' },
            axisLine: { lineStyle: { color: '#FFB7C5' } },
            splitLine: { lineStyle: { color: 'rgba(255, 183, 197, 0.1)' } }
        },
        series: [{
            data: [
                data.score_distribution.distribution.low,
                data.score_distribution.distribution.medium,
                data.score_distribution.distribution.high
            ],
            type: 'bar',
            itemStyle: { 
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#FFB7C5' },
                    { offset: 1, color: 'rgba(255, 183, 197, 0.3)' }
                ])
            }
        }]
    });

    // 更新性别分布图
    const genderChart = echarts.init(document.getElementById('gender-distribution-chart'));
    genderChart.setOption({
        title: {
            text: '性别分布',
            left: 'center',
            textStyle: { color: '#FFB7C5' }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: { color: '#FFB7C5' }
        },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 10,
                borderColor: '#000',
                borderWidth: 2
            },
            label: {
                show: false,
                position: 'center'
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: '20',
                    fontWeight: 'bold',
                    color: '#FFB7C5'
                }
            },
            labelLine: {
                show: false
            },
            data: Object.entries(data.gender_distribution).map(([gender, count]) => ({
                name: gender === 'm' ? '男' : gender === 'f' ? '女' : '未知',
                value: count,
                itemStyle: {
                    color: gender === 'm' ? '#FFB7C5' : 
                           gender === 'f' ? '#FF69B4' : 
                           'rgba(255, 183, 197, 0.3)'
                }
            }))
        }]
    });

    // 更新时间分布图
    const timeChart = echarts.init(document.getElementById('time-distribution-chart'));
    timeChart.setOption({
        title: {
            text: '活跃时间分布',
            left: 'center',
            textStyle: { color: '#FFB7C5' }
        },
        tooltip: {
            trigger: 'axis'
        },
        grid: {
            top: '15%',
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: Object.keys(data.time_distribution),
            axisLabel: { color: '#FFB7C5' },
            axisLine: { lineStyle: { color: '#FFB7C5' } }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#FFB7C5' },
            axisLine: { lineStyle: { color: '#FFB7C5' } },
            splitLine: { lineStyle: { color: 'rgba(255, 183, 197, 0.1)' } }
        },
        series: [{
            data: Object.values(data.time_distribution),
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: { 
                color: '#FFB7C5',
                width: 3
            },
            itemStyle: {
                color: '#FFB7C5',
                borderWidth: 2,
                borderColor: '#000'
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(255, 183, 197, 0.3)'
                }, {
                    offset: 1,
                    color: 'rgba(255, 183, 197, 0.1)'
                }])
            }
        }]
    });

    // 更新风险等级图
    const riskChart = echarts.init(document.getElementById('risk-level-chart'));
    riskChart.setOption({
        title: {
            text: '风险等级分布',
            left: 'center',
            textStyle: { color: '#FFB7C5' }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: { color: '#FFB7C5' }
        },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 10,
                borderColor: '#000',
                borderWidth: 2
            },
            label: {
                show: false,
                position: 'center'
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: '20',
                    fontWeight: 'bold',
                    color: '#FFB7C5'
                }
            },
            labelLine: {
                show: false
            },
            data: [
                { 
                    value: data.risk_level.risk_levels.high, 
                    name: '高风险',
                    itemStyle: { 
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#ee6666' },
                            { offset: 1, color: 'rgba(238, 102, 102, 0.3)' }
                        ])
                    }
                },
                { 
                    value: data.risk_level.risk_levels.medium, 
                    name: '中风险',
                    itemStyle: { 
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#fac858' },
                            { offset: 1, color: 'rgba(250, 200, 88, 0.3)' }
                        ])
                    }
                },
                { 
                    value: data.risk_level.risk_levels.low, 
                    name: '低风险',
                    itemStyle: { 
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#91cc75' },
                            { offset: 1, color: 'rgba(145, 204, 117, 0.3)' }
                        ])
                    }
                }
            ]
        }]
    });

    // 更新黑粉排名列表
    const rankingList = document.getElementById('hater-ranking-list');
    if (data.top_black_fans && data.top_black_fans.length > 0) {
        rankingList.innerHTML = data.top_black_fans.map((fan, index) => `
            <div class="ranking-item">
                <div class="ranking-rank">${index + 1}</div>
                <div class="ranking-info">
                    <div class="ranking-name">${fan.nickname || '未知用户'}</div>
                    <div class="ranking-metrics">
                        <span>评论数: ${fan.comment_count}</span>
                        <span>最后活跃: ${new Date(fan.last_active).toLocaleDateString()}</span>
                        <span>地区: ${fan.location || '未知'}</span>
                    </div>
                </div>
                <div class="ranking-score">${(fan.black_fan_score * 100).toFixed(1)}分</div>
            </div>
        `).join('');
    } else {
        rankingList.innerHTML = '<div class="no-data">暂无黑粉数据</div>';
    }

    // 更新黑粉活跃度趋势图
    const activityChart = echarts.init(document.getElementById('hater-activity-chart'));
    activityChart.setOption({
        title: {
            text: '黑粉活跃度趋势',
            left: 'center',
            textStyle: { color: '#FFB7C5' }
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: data.trend_analysis.map(item => item.date),
            axisLabel: { color: '#FFB7C5' }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#FFB7C5' }
        },
        series: [{
            data: data.trend_analysis.map(item => item.count),
            type: 'line',
            smooth: true,
            lineStyle: { color: '#FFB7C5' },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(255, 183, 197, 0.3)'
                }, {
                    offset: 1,
                    color: 'rgba(255, 183, 197, 0.1)'
                }])
            }
        }]
    });

    // 更新黑粉地域分布图
    const locationChart = echarts.init(document.getElementById('hater-location-chart'));
    const locationData = Object.entries(data.location_distribution)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    locationChart.setOption({
        title: {
            text: '黑粉地域分布 Top 10',
            left: 'center',
            textStyle: { color: '#FFB7C5' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        },
        xAxis: {
            type: 'value',
            axisLabel: { color: '#FFB7C5' }
        },
        yAxis: {
            type: 'category',
            data: locationData.map(item => item[0]),
            axisLabel: { color: '#FFB7C5' }
        },
        series: [{
            name: '黑粉数量',
            type: 'bar',
            data: locationData.map(item => item[1]),
            itemStyle: { color: '#FFB7C5' }
        }]
    });

    // 更新黑粉情感分析图
    const sentimentChart = echarts.init(document.getElementById('hater-sentiment-chart'));
    sentimentChart.setOption({
        title: {
            text: '黑粉情感分析',
            left: 'center',
            textStyle: { color: '#FFB7C5' }
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: data.sentiment_trend.map(item => item.date),
            axisLabel: { color: '#FFB7C5' }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#FFB7C5' }
        },
        series: [{
            name: '平均情感得分',
            type: 'line',
            data: data.sentiment_trend.map(item => item.avg_sentiment),
            smooth: true,
            lineStyle: { color: '#FFB7C5' },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(255, 183, 197, 0.3)'
                }, {
                    offset: 1,
                    color: 'rgba(255, 183, 197, 0.1)'
                }])
            }
        }]
    });

    // 更新预警列表
    const warningList = document.getElementById('warning-list');
    warningList.innerHTML = data.warnings.map(warning => `
        <li class="warning-item">
            <div class="level level-${warning.level.toLowerCase()}">${warning.level}</div>
            <div class="content">${warning.content}</div>
            <div class="time">${warning.time}</div>
        </li>
    `).join('');
}

// 更新热度分析图表
function updateHeatCharts(data) {
    // 热度趋势图
    const heatChart = echarts.init(document.getElementById('heatTrendChart'));
    heatChart.setOption({
        title: {
            text: '热度趋势',
            left: 'center',
            textStyle: {
                color: '#FFB7C5'
            }
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                color: '#FFB7C5'
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                color: '#FFB7C5'
            }
        },
        series: [{
            data: data.heat_scores,
            type: 'line',
            smooth: true,
            lineStyle: {
                color: '#FFB7C5'
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(255, 183, 197, 0.3)'
                }, {
                    offset: 1,
                    color: 'rgba(255, 183, 197, 0.1)'
                }])
            }
        }]
    });

    // 互动分析图
    const interactionChart = echarts.init(document.getElementById('interactionChart'));
    interactionChart.setOption({
        title: {
            text: '互动分析',
            left: 'center',
            textStyle: {
                color: '#FFB7C5'
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {
                color: '#FFB7C5'
            }
        },
        series: [{
            name: '互动分布',
            type: 'pie',
            radius: '50%',
            data: [
                { value: data.comment_count, name: '评论', itemStyle: { color: '#91cc75' } },
                { value: data.like_count, name: '点赞', itemStyle: { color: '#fac858' } },
                { value: data.repost_count, name: '转发', itemStyle: { color: '#ee6666' } }
            ],
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    });
}

// 显示错误消息
function showErrorMessage(message) {
    // 实现错误消息显示逻辑
    console.error(message);
    alert(message);
}

// 切换标签页
function switchTab(tabName) {
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 取消所有标签按钮的激活状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 显示选中的标签内容
    document.getElementById(tabName).classList.add('active');
    
    // 激活对应的标签按钮
    document.querySelector(`.tab-btn[onclick="switchTab('${tabName}')"]`).classList.add('active');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化标签页
    switchTab('overview');
});

// 浮动球动画
function createFloatingBalls(count) {
    const container = document.querySelector('.floating-balls');
    if (!container) return;
    container.innerHTML = ''; // Clear existing balls

    const colors = [
        'rgba(255, 255, 255, 0.1)',
        'rgba(255, 255, 255, 0.15)',
        'rgba(255, 255, 255, 0.2)'
    ];

    for (let i = 0; i < count; i++) {
        const ball = document.createElement('div');
        ball.classList.add('ball');
        const size = Math.random() * 60 + 20; // Size between 20px and 80px
        ball.style.width = `${size}px`;
        ball.style.height = `${size}px`;
        ball.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        ball.style.left = `${Math.random() * 100}%`;
        ball.style.top = `${Math.random() * 100}%`;
        ball.style.animationDuration = `${Math.random() * 10 + 5}s`; // Duration between 5s and 15s
        ball.style.animationDelay = `${Math.random() * 5}s`; // Delay up to 5s
        ball.style.boxShadow = `0 0 ${size / 4}px rgba(255, 255, 255, 0.1)`;
        container.appendChild(ball);
    }
}

// 初始化浮动球
createFloatingBalls(15); // 创建15个浮动球

// 窗口大小改变时重新生成浮动球
window.addEventListener('resize', () => {
    createFloatingBalls(15);
});

// 窗口大小改变时重新初始化图表
window.addEventListener('resize', () => {
    const charts = document.querySelectorAll('[id$="Chart"]');
    charts.forEach(chart => {
        const instance = echarts.getInstanceByDom(chart);
        if (instance) {
            instance.resize();
        }
    });
});