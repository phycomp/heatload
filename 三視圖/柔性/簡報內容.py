from streamlit import markdown, columns, info
from re import sub as reSub, match as reMatch

def 簡報內容(slides_data, theme_cfg):
    # 逐頁渲染卡片預覽
    for idx, slide in enumerate(slides_data, 1):
        markdown(f"#### Slide {idx}: {slide['title']}")
        
        # 使用 HTML/CSS 模擬 PPT 畫面
        if slide.get("is_main_title") or (idx == 1 and len(slides_data) > 1):
            # 封面頁 CSS
            preview_html = f"""
            <div style="
                background-color: {theme_cfg['hex_bg']};
                border-radius: 10px;
                padding: 40px;
                margin-bottom: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                min-height: 250px;
            ">
                <p style="color: {theme_cfg['hex_accent']}; font-weight: bold; font-size: 14px; letter-spacing: 2px; margin-bottom: 8px;">PRESENTATION</p>
                <h1 style="color: {theme_cfg['hex_title']}; font-size: 32px; margin-top: 0; margin-bottom: 16px;">{slide['title']}</h1>
                <div style="color: {theme_cfg['hex_text']}; font-size: 16px; line-height: 1.6;">
                    {"<br>".join([reSub(r'\*\*(.*?)\*\*', f'<strong style="color:{theme_cfg["hex_accent"]}">\1</strong>', line.strip()) for line in slide['content'] if line.strip()])[:300]}
                </div>
            </div>
            """
        else:
            # 內容頁 CSS
            內容 = []
            for line in slide['content']:
                line_str = line.strip()
                if not line_str:
                    continue
                # 替換粗體
                formatted_line = reSub(r'\*\*(.*?)\*\*', f'<strong style="color:{theme_cfg["hex_accent"]}">\1</strong>', line_str)
                if line_str.startswith('#'):
                    clean = reSub(r'^[#]+\s*', '', formatted_line)
                    內容.append(f'<p style="color: {theme_cfg["hex_accent"]}; font-weight: bold; font-size: 18px; margin-top: 10px; margin-bottom: 4px;">{clean}</p>')
                elif line_str.startswith('-') or line_str.startswith('*') or reMatch(r'^\d+\.', line_str):
                    clean = reSub(r'^[-*•\d\.]+\s*', '', formatted_line)
                    內容.append(f'<li style="color: {theme_cfg["hex_text"]}; font-size: 15px; margin-bottom: 6px;">{clean}</li>')
                else:
                    內容.append(f'<p style="color: {theme_cfg["hex_text"]}; font-size: 15px; margin-bottom: 8px;">{formatted_line}</p>')
            
            content_body = "".join(內容)
            
            preview_html = f"""
            <div style="
                background-color: {theme_cfg['hex_bg']};
                border-radius: 10px;
                padding: 24px;
                margin-bottom: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            ">
                <h2 style="color: {theme_cfg['hex_title']}; font-size: 24px; margin-top: 0; margin-bottom: 16px;">{slide['title']}</h2>
                <div style="
                    background-color: {theme_cfg['hex_card']};
                    border: 1px solid {theme_cfg['card_border']};
                    border-radius: 8px;
                    padding: 20px;
                ">
                    <ul style="margin: 0; padding-left: 20px;">
                        {content_body}
                    </ul>
                </div>
            </div>
            """
        
        # 呈現卡片與講稿
        col1, col2 = columns([3, 1])
        with col1:
            markdown(preview_html, unsafe_allow_html=True)
        with col2:
            markdown("**🎙️ 演講者備忘錄 / 講稿**")
            if slide['notes']:
                info(slide['notes'])
            else:
                info("無備忘錄講稿")

