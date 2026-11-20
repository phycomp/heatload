from streamlit import columns, container, dataframe, error, expander, image, info, markdown, page_link, plotly_chart, selectbox, set_page_config, sidebar, subheader, success, tabs, title, radio, text_input, empty, session_state
from pandas import DataFrame
from plotly.graph_objects import Bar, Figure, Indicator
# 3. Main Streamlit App - Home Dashboard

import streamlit as st
import pandas as pd
from plotly.express import bar
from datetime import datetime, date
import calendar

from 庫 import get_db_cursor

set_page_config(
    page_title="KPI Ticket Tracking System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; }
    .sub-header { font-size: 1.2rem; color: #666; margin-bottom: 20px; }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   padding: 20px; border-radius: 10px; color: white; }
    .metric-value { font-size: 2rem; font-weight: bold; }
    .metric-label { font-size: 0.9rem; opacity: 0.9; }
    .status-completed { color: #28a745; font-weight: bold; }
    .status-in_progress { color: #ffc107; font-weight: bold; }
    .status-pending { color: #6c757d; font-weight: bold; }
    .status-delayed { color: #dc3545; font-weight: bold; }
    .status-cancelled { color: #6c757d; font-weight: bold; text-decoration: line-through; }
    .priority-critical { background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .priority-high { background: #fd7e14; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .priority-medium { background: #ffc107; color: black; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .priority-low { background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

def get_status_badge(status):
    status_map = {
        'completed': '<span class="status-completed">✅ 已完成</span>',
        'in_progress': '<span class="status-in_progress">🔄 進行中</span>',
        'pending': '<span class="status-pending">⏳ 待處理</span>',
        'delayed': '<span class="status-delayed">⚠️ 延遲</span>',
        'cancelled': '<span class="status-cancelled">❌ 已取消</span>'
    }
    return status_map.get(status, status)

def get_priority_badge(priority):
    priority_map = {
        'critical': '<span class="priority-critical">🔴 緊急</span>',
        'high': '<span class="priority-high">🟠 高</span>',
        'medium': '<span class="priority-medium">🟡 中</span>',
        'low': '<span class="priority-low">🟢 低</span>'
    }
    return priority_map.get(priority, priority)

def 載入():
    """Load all dashboard data from database"""
    data = {}
    
    with get_db_cursor(dict_cursor=True) as cur:
        # Overall statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'delayed') as delayed,
                ROUND(AVG(progress_pct), 2) as avg_progress,
                ROUND(SUM(weight * progress_pct) / NULLIF(SUM(weight), 0), 2) as weighted_progress
            FROM kpi_tickets
        """)
        data['overall'] = cur.fetchone()
        
        # Department statistics
        cur.execute("""
            SELECT 
                d.dept_name,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE t.status = 'completed') as completed,
                ROUND(COUNT(*) FILTER (WHERE t.status = 'completed') * 100.0 / NULLIF(COUNT(*), 0), 2) as achievement_rate,
                ROUND(SUM(t.weight * t.progress_pct) / NULLIF(SUM(t.weight), 0), 2) as weighted_progress
            FROM kpi_tickets t
            JOIN kpi_categories c ON t.category_id = c.category_id
            JOIN departments d ON c.dept_id = d.dept_id
            GROUP BY d.dept_name
            ORDER BY d.dept_name
        """)
        data['dept_stats'] = cur.fetchall()
        
        # Monthly achievement
        cur.execute("""
            SELECT 
                year_num,
                dept_name,
                TO_CHAR(report_month, 'YYYY-MM') as month_str,
                total_tickets,
                completed_count,
                achievement_rate,
                weighted_progress
            FROM v_monthly_achievement
            ORDER BY year_num, dept_name, month_str
        """)
        data['monthly'] = cur.fetchall()
        
        # Period achievement
        cur.execute("""
            SELECT 
                year_num,
                dept_name,
                period_type,
                total_tickets,
                completed_count,
                achievement_rate,
                weighted_progress,
                completed_weight,
                total_weight
            FROM v_period_achievement
            ORDER BY year_num, dept_name
        """)
        data['period'] = cur.fetchall()
        
        # Status distribution by year
        cur.execute("""
            SELECT 
                year_num,
                status,
                COUNT(*) as count
            FROM kpi_tickets
            GROUP BY year_num, status
            ORDER BY year_num, status
        """)
        data['status_by_year'] = cur.fetchall()
        
        # Priority distribution
        cur.execute("""
            SELECT 
                priority,
                COUNT(*) as count
            FROM kpi_tickets
            GROUP BY priority
            ORDER BY 
                CASE priority 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    ELSE 4 
                END
        """)
        data['priority_dist'] = cur.fetchall()
        
        # Recent progress updates
        cur.execute("""
            SELECT 
                p.progress_date,
                t.kpi_item,
                d.dept_name,
                p.progress_pct,
                p.actual_value,
                p.notes
            FROM kpi_progress p
            JOIN kpi_tickets t ON p.ticket_id = t.ticket_id
            JOIN kpi_categories c ON t.category_id = c.category_id
            JOIN departments d ON c.dept_id = d.dept_id
            ORDER BY p.progress_date DESC, p.created_at DESC
            LIMIT 10
        """)
        data['recent_progress'] = cur.fetchall()
        
        # Overdue tickets
        cur.execute("""
            SELECT 
                t.ticket_id,
                t.kpi_item,
                d.dept_name,
                t.due_date,
                t.progress_pct,
                t.status
            FROM kpi_tickets t
            JOIN kpi_categories c ON t.category_id = c.category_id
            JOIN departments d ON c.dept_id = d.dept_id
            WHERE t.due_date < CURRENT_DATE 
              AND t.status NOT IN ('completed', 'cancelled')
            ORDER BY t.due_date
        """)
        data['overdue'] = cur.fetchall()
    
    return data

def render_overview_metrics(data):
    """Render overview metric cards"""
    overall = data['overall']
    狀態.code(overall)
    col1, col2, col3, col4, col5 = columns(5)
    
    with col1:
        markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{overall[0]}</div>
                <div class="metric-label">總KPI項目</div>
            </div>
        """, unsafe_allow_html=True)#'total_tickets'
    
    with col2:
        markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                <div class="metric-value">{overall[1]}</div>
                <div class="metric-label">已完成</div>
            </div>
        """, unsafe_allow_html=True)#'completed'
    
    with col3:
        markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="metric-value">{overall[2]}</div>
                <div class="metric-label">進行中</div>
            </div>
        """, unsafe_allow_html=True)  #'in_progress'
    
    with col4:
        completion_rate = round(overall[1] / overall[0] * 100, 1) if overall[0] > 0 else 0 #'completed', 'total_tickets', 'total_tickets'
        markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-value">{completion_rate}%</div>
                <div class="metric-label">完成率</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <div class="metric-value">{overall[6]}%</div>
                <div class="metric-label">加權進度</div>
            </div>
        """, unsafe_allow_html=True)  #'weighted_progress'

def render_charts(data):
    """Render dashboard charts"""
    markdown("---")
    
    col1, col2 = columns(2)
    
    with col1:
        subheader("📊 各部門達成率")
        if data['dept_stats']:
            df_dept = DataFrame(data['dept_stats'], columns=['dept_name', 'achievement_rate'])
            #df_dept
            fig = bar(df_dept, x=0, #'dept_name', 
                y=1, #'achievement_rate',
                color=2, #'achievement_rate',
                color_continuous_scale='RdYlGn',
                text=1, #'achievement_rate',
                height=350,
                labels={'dept_name':'部門', 'achievement_rate':'達成率 (%)'},
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(showlegend=False, margin=dict(t=30, b=30))
            plotly_chart(fig, use_container_width=True)
    
    with col2:
        subheader("🎯 狀態分佈")
        if data['status_by_year']:
            df_status = DataFrame(data['status_by_year'])
            status_map = {'completed': '已完成', 'in_progress': '進行中', 'pending': '待處理', 'delayed': '延遲', 'cancelled': '已取消'}
            df_status['status_zh'] = df_status['status'].map(status_map)
            
            fig = pie(
                df_status, 
                values='count', 
                names='status_zh',
                color='status',
                color_discrete_map={
                    'completed': '#28a745',
                    'in_progress': '#ffc107',
                    'pending': '#6c757d',
                    'delayed': '#dc3545',
                    'cancelled': '#adb5bd'
                },
                height=350
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False, margin=dict(t=30, b=30))
            plotly_chart(fig, use_container_width=True)
    
    col3, col4 = columns(2)
    
    with col3:
        subheader("📈 各部門加權進度")
        if data['dept_stats']:
            df_dept = DataFrame(data['dept_stats'])
            fig = Figure()
            fig.add_trace(Bar(
                x=df_dept['dept_name'],
                y=df_dept['weighted_progress'],
                marker_color=['#667eea', '#f093fb', '#4facfe', '#fa709a'],
                text=[f"{v:.1f}%" for v in df_dept['weighted_progress']],
                textposition='outside'
            ))
            fig.update_layout(
                xaxis_title='部門',
                yaxis_title='加權進度 (%)',
                yaxis_range=[0, 100],
                height=350,
                margin=dict(t=30, b=30)
            )
            plotly_chart(fig, use_container_width=True)
    
    with col4:
        subheader("⚡ 優先級分佈")
        if data['priority_dist']:
            df_prio = DataFrame(data['priority_dist'])
            prio_map = {'critical': '緊急', 'high': '高', 'medium': '中', 'low': '低'}
            df_prio['priority_zh'] = df_prio['priority'].map(prio_map)
            
            fig = bar(
                df_prio,
                x='priority_zh',
                y='count',
                color='priority',
                color_discrete_map={
                    'critical': '#dc3545',
                    'high': '#fd7e14',
                    'medium': '#ffc107',
                    'low': '#28a745'
                },
                labels={'priority_zh': '優先級', 'count': '數量'},
                text='count',
                height=350
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, margin=dict(t=30, b=30))
            plotly_chart(fig, use_container_width=True)

def render_period_achievement(data):
    """Render period (monthly/mid-year/annual) achievement"""
    markdown("---")
    subheader("📅 達成率分析 (月 / 期中 / 年度)")
    
    tab1, tab2, tab3 = tabs(["🗓️ 月度達成率", "📊 期中達成率", "🏆 年度達成率"])
    
    with tab1:
        if data['monthly']:
            df_monthly = DataFrame(data['monthly'])
            
            # Year filter
            years = sorted(df_monthly['year_num'].unique())
            selected_year = selectbox("選擇年度", years, key="monthly_year")
            
            df_filtered = df_monthly[df_monthly['year_num'] == selected_year]
            
            fig = line(
                df_filtered,
                x='month_str',
                y='achievement_rate',
                color='dept_name',
                markers=True,
                labels={'month_str': '月份', 'achievement_rate': '達成率 (%)', 'dept_name': '部門'},
                height=400
            )
            fig.update_layout(yaxis_range=[0, 100], margin=dict(t=30, b=30))
            plotly_chart(fig, use_container_width=True)
            
            # Monthly data table
            with expander("📋 月度詳細數據"):
                df_display = df_filtered[['dept_name', 'month_str', 'total_tickets', 'completed_count', 'achievement_rate', 'weighted_progress']]
                df_display.columns = ['部門', '月份', '總項目', '已完成', '達成率(%)', '加權進度(%)']
                dataframe(df_display, use_container_width=True)
    
    with tab2:
        if data['period']:
            df_period = DataFrame(data['period'])
            
            fig = bar(
                df_period,
                x='dept_name',
                y='achievement_rate',
                color='year_num',
                barmode='group',
                labels={'dept_name': '部門', 'achievement_rate': '達成率 (%)', 'year_num': '年度'},
                text='achievement_rate',
                height=400
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(yaxis_range=[0, 100], margin=dict(t=30, b=30))
            plotly_chart(fig, use_container_width=True)
            
            with expander("📋 期中詳細數據"):
                df_display = df_period[['year_num', 'dept_name', 'total_tickets', 'completed_count', 'achievement_rate', 'weighted_progress', 'completed_weight', 'total_weight']]
                df_display.columns = ['年度', '部門', '總項目', '已完成', '達成率(%)', '加權進度(%)', '已完成權重', '總權重']
                dataframe(df_display, use_container_width=True)
    
    with tab3:
        if data['period']:
            df_annual = DataFrame(data['period'])
            
            # Gauge charts for each department
            cols = columns(min(4, len(df_annual)))
            for idx, (_, row) in enumerate(df_annual.iterrows()):
                with cols[idx % 4]:
                    fig = Figure(Indicator(
                        mode="gauge+number+delta",
                        value=row['achievement_rate'],
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': f"{row['dept_name']}<br>Year {row['year_num']}", 'font': {'size': 14}},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#1f77b4"},
                            'steps': [
                                {'range': [0, 50], 'color': "#ffcccc"},
                                {'range': [50, 80], 'color': "#ffffcc"},
                                {'range': [80, 100], 'color': "#ccffcc"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 80
                            }
                        }
                    ))
                    fig.update_layout(height=250, margin=dict(t=20, b=20))
                    plotly_chart(fig, use_container_width=True)

def render_recent_activity(data):
    """Render recent activity and alerts"""
    markdown("---")
    
    col1, col2 = columns(2)
    
    with col1:
        subheader("📝 最近進度更新")
        if data['recent_progress']:
            for item in data['recent_progress'][:5]:
                with container():
                    markdown(f"""
                        <div style="padding: 10px; border-left: 4px solid #667eea; margin-bottom: 10px; background: #f8f9fa;">
                            <b>{item['kpi_item']}</b> <span style="color: #666;">({item['dept_name']})</span><br>
                            <span style="color: #1f77b4;">進度: {item['progress_pct']}%</span> | 
                            <span style="color: #28a745;">實際值: {item['actual_value'] or 'N/A'}</span><br>
                            <small style="color: #999;">{item['progress_date']} - {item['notes'] or ''}</small>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            info("暫無進度更新記錄")
    
    with col2:
        subheader("⚠️ 逾期項目警示")
        if data['overdue']:
            for item in data['overdue']:
                days_overdue = (date.today() - item['due_date']).days
                with container():
                    markdown(f"""
                        <div style="padding: 10px; border-left: 4px solid #dc3545; margin-bottom: 10px; background: #fff5f5;">
                            <b>{item['kpi_item']}</b> <span style="color: #666;">({item['dept_name']})</span><br>
                            <span style="color: #dc3545;">⚠️ 逾期 {days_overdue} 天</span> | 
                            <span>截止: {item['due_date']}</span> | 
                            <span>進度: {item['progress_pct']}%</span>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            success("🎉 目前無逾期項目")
# ============================================
# MAIN APP
# ============================================
    # Sidebar
#from 庫同步 import runQuery
MENU, 表單=[], ['載入', '圖表', '控管']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  image("https://img.icons8.com/color/96/000000/ticket.png", width=80)
  title("導航選單")
  markdown("### 📍 快速連結")
  #page_link("pages/1_KPI_Management.py", label="📝 KPI 管理 (CRUD)", icon="📝")
  #page_link("pages/2_Progress_Update.py", label="📈 進度更新", icon="📈")
  #page_link("pages/3_Reports_Analytics.py", label="📊 報表分析", icon="📊")
  markdown("### 📅 當前日期")
  info(f"**{date.today().strftime('%Y年%m月%d日')}**")
  markdown("### 👤 使用者")
  角色=radio("角色", ["管理員", "部門經理", "工程師"], key="user_role", horizontal=True)
狀態=empty()
  #狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[0]: #控管
    # Load data
    #try:
    data = session_state['data']=載入() #load_dashboard_dataexcept Exception as e: #    error(f"載入資料失敗: {e}") info("請確認 PostgreSQL 資料庫已正確設定並執行 schema.sql")
    # Overview metrics
    狀態.code(data)
    render_overview_metrics(data)
    
elif menu==MENU[1]: #
    data = session_state['data']
    # Charts
    render_charts(data)
    
elif menu==MENU[2]: #
    # Period achievement
    render_period_achievement(data)
    
elif menu==MENU[3]: #
    # Recent activity
    render_recent_activity(data)
    
with sidebar:
    markdown('<div class="main-header">📊 KPI Ticket Tracking System</div>', unsafe_allow_html=True)
    markdown('<div class="sub-header">量子傳輸線三年計畫 - 績效追蹤管理平台</div>', unsafe_allow_html=True)
    markdown("<center><small>© 2026 KPI Ticket Tracking System | Quantum Transmission Line Project</small></center>", unsafe_allow_html=True)
