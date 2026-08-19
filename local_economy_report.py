import streamlit as st
import pandas as pd
import openpyxl
import requests
import urllib.parse
import base64
from io import BytesIO

# ---------------------------------------------------------
# 1. 환경 설정 및 상수
# ---------------------------------------------------------
st.set_page_config(page_title="지역경제활성화 자동 집계 시스템", page_icon="📊", layout="wide")

# --- 커스텀 CSS 디자인 주입 ---
st.markdown("""
<style>
    /* 우측 상단 기본 메뉴 및 하단 로고 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 전체 배경색 미세 조정 */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* 버튼 스타일 세련되게 변경 */
    div.stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease 0s;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    div.stButton > button:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* 다운로드 버튼은 색상을 다르게(초록색 톤) */
    div.stDownloadButton > button {
        background-color: #059669;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease 0s;
    }
    div.stDownloadButton > button:hover {
        background-color: #047857;
        transform: translateY(-2px);
    }
    
    /* 메인 타이틀 디자인 */
    .main-title {
        color: #1e293b;
        font-weight: 800;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

MY_G2B_API_KEY = "V%2FBFQCvaQlP%2F3ebvSQyuncyYbTzwqIxQ5yDO%2Fc%2FnX3YTRLd3ZZXxTeNhVd99xGMLoQOWLSwS7x%2BJ07aIn7Fk0w%3D%3D"
API_URL = "https://apis.data.go.kr/1230000/ao/UsrInfoService02/getPrcrmntCorpBasicInfo02"
CHUNGNAM_REGIONS = ["천안", "아산", "공주", "보령", "서산", "논산", "계룡", "당진", "금산", "부여", "서천", "청양", "홍성", "예산", "태안"]
TARGET_AMOUNT = 500000  # 집계 기준 금액

# ★ 변환하신 템플릿의 긴 문자열을 아래 따옴표 사이에 반드시 넣어주십시오.
TEMPLATE_BASE64 = "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"

# ---------------------------------------------------------
# 2. 로직: API 주소 가져오기
# ---------------------------------------------------------
def get_addr_api(biz_num, corp_name):
    if pd.isna(biz_num) or pd.isna(corp_name):
        return None
    biz_clean = str(biz_num).replace("-", "").strip()
    corp_clean = str(corp_name).strip()
    params = {
        'serviceKey': urllib.parse.unquote(MY_G2B_API_KEY),
        'pageNo': '1', 'numOfRows': '10', 'type': 'json',
        'bizno': biz_clean, 'corpNm': corp_clean
    }
    try:
        res = requests.get(API_URL, params=params, verify=False, timeout=5)
        items = res.json().get('response', {}).get('body', {}).get('items', [])
        if isinstance(items, list) and items:
            return f"{items[0].get('adrs', '')} {items[0].get('dtlAdrs', '')}".strip()
    except: pass
    return None

# ---------------------------------------------------------
# 3. 메인 UI
# ---------------------------------------------------------
st.markdown('<h1 class="main-title">📊 지역경제활성화 자동 집계 시스템</h1>', unsafe_allow_html=True)

with st.expander("💡 시스템 사용 방법 안내 (클릭하여 열기)"):
    st.markdown("""
    1. 왼쪽 메뉴에서 **기준 지역**을 선택하고 **자료관리목록 엑셀**을 업로드합니다.
    2. 데이터가 인식되면, **[1. 파일 내 자체 대조]** 버튼을 눌러 기존 데이터로 주소를 채웁니다.
    3. 남은 빈칸은 **[2. 조달청 API 검색]** 버튼을 눌러 자동으로 채웁니다.
    4. 자동화로도 찾아내지 못한 업체는 표를 통해 직접 입력 후 일괄 적용합니다.
    5. 하단의 **결과물 다운로드** 버튼을 눌러 최종 서식을 받습니다.
    """)

with st.sidebar:
    st.header("📂 1. 데이터 업로드")
    target_region = st.selectbox("기준 지역 선택", CHUNGNAM_REGIONS, index=0)
    data_file = st.file_uploader("자료관리목록 엑셀 업로드", type=["xls", "xlsx"])
    
    st.markdown("---")
    st.caption("개발: 천안버들유치원 나대현\n\n문의 및 오류 신고는 메신저로 부탁드립니다.")

if data_file:
    if 'df' not in st.session_state:
        st.session_state.df = pd.read_excel(data_file)
    
    df = st.session_state.df
    
    AMT_COL = 6
    COMP_COL = 16 
    BIZ_COL = 18
    ADDR_COL = 20
    
    biz_col_data = df.iloc[:, BIZ_COL].astype(str).str.strip()
    is_valid_biz = (biz_col_data.str.len() >= 8) & (~biz_col_data.str.contains("Unnamed|nan|None", case=False, na=False))
    
    amt_data = pd.to_numeric(df.iloc[:, AMT_COL], errors='coerce').fillna(0)
    is_target_amt = amt_data >= TARGET_AMOUNT
    
    target_mask = is_valid_biz & is_target_amt
    total_target_rows = target_mask.sum()
    
    missing_mask = df.iloc[:, ADDR_COL].isna() | (df.iloc[:, ADDR_COL].astype(str).str.strip() == "") | (df.iloc[:, ADDR_COL].astype(str).str.strip() == "nan")
    missing_indices = df[missing_mask & target_mask].index
    missing_count = len(missing_indices)
    
    # --- 대시보드 메트릭 영역 ---
    st.subheader("📈 데이터 처리 현황")
    met1, met2, met3 = st.columns(3)
    met1.metric("업로드된 유효 데이터", f"{is_valid_biz.sum()}건")
    met2.metric("집계 대상 (50만 원 이상)", f"{total_target_rows}건")
    if missing_count > 0:
        met3.metric("주소 누락 (조치 필요)", f"{missing_count}건", delta="-작업 필요", delta_color="inverse")
    else:
        met3.metric("주소 누락", "0건", delta="완벽함!", delta_color="normal")
    
    st.markdown("---")
    
    # --- 버튼 영역 ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("1️⃣ 파일 내 동일 사업자로 주소 채우기"):
            known_addrs = df.dropna(subset=[df.columns[ADDR_COL]]).set_index(df.columns[BIZ_COL])[df.columns[ADDR_COL]].to_dict()
            df[df.columns[ADDR_COL]] = df[df.columns[ADDR_COL]].fillna(df[df.columns[BIZ_COL]].map(known_addrs))
            st.session_state.df = df
            st.rerun()

    with col2:
        if st.button("2️⃣ 조달청 API로 나머지 주소 자동 검색"):
            if missing_count == 0:
                st.info("채울 주소가 없습니다.")
            else:
                progress_bar = st.progress(0, text="조달청 서버 검색 중...")
                filled_api = 0
                for i, idx in enumerate(missing_indices):
                    addr = get_addr_api(df.iat[idx, BIZ_COL], df.iat[idx, COMP_COL])
                    if addr:
                        df.iat[idx, ADDR_COL] = addr
                        filled_api += 1
                    progress_bar.progress((i + 1) / len(missing_indices), text=f"{i+1}/{len(missing_indices)}건 완료")
                st.session_state.df = df
                st.rerun()

    st.markdown("---")
    
    # --- 수동 입력 영역 ---
    if missing_count > 0:
        missing_df = df.loc[missing_indices]
        unique_missing = missing_df.drop_duplicates(subset=[df.columns[BIZ_COL]])
        
        st.warning(f"🚨 아직 주소를 찾지 못한 고유 업체가 **{len(unique_missing)}곳** 있습니다. 아래 표에서 주소를 입력해 주세요.")
        
        edit_data = {
            '업체명': unique_missing.iloc[:, COMP_COL].astype(str).replace('nan', '정보없음'),
            '사업자번호': unique_missing.iloc[:, BIZ_COL].astype(str),
            '비즈노 검색링크': unique_missing.iloc[:, BIZ_COL].apply(
                lambda x: f"https://bizno.net/?area=&query={str(x).strip()}" if pd.notna(x) else ""
            ),
            '주소 수동 입력칸': [""] * len(unique_missing)
        }
        edit_df = pd.DataFrame(edit_data, index=unique_missing.index)
        
        edited_df = st.data_editor(
            edit_df,
            column_config={
                "비즈노 검색링크": st.column_config.LinkColumn("비즈노 링크", display_text="🔍 비즈노에서 찾기"),
                "주소 수동 입력칸": st.column_config.TextColumn("📝 주소 수동 입력칸 (여기에 타이핑)")
            },
            disabled=["업체명", "사업자번호", "비즈노 검색링크"],
            use_container_width=True
        )
        
        if st.button("💾 입력한 주소 원본에 일괄 적용하기"):
            apply_count = 0
            for idx in edited_df.index:
                new_addr = edited_df.at[idx, '주소 수동 입력칸']
                biz_num = edited_df.at[idx, '사업자번호']
                
                if new_addr and str(new_addr).strip():
                    mask = (df.iloc[:, BIZ_COL].astype(str).str.strip() == biz_num)
                    df.loc[mask, df.columns[ADDR_COL]] = str(new_addr).strip()
                    apply_count += 1
                    
            if apply_count > 0:
                st.session_state.df = df
                st.rerun()
            else:
                st.warning("입력된 주소가 없습니다.")
    else:
        st.success("✨ 집계 대상(50만 원 이상)의 주소가 모두 채워졌습니다! 아래에서 결과를 다운로드하세요.")
        
    st.markdown("---")
    st.subheader("📥 최종 결과물 다운로드")
        
    col3, col4 = st.columns(2)
    
    with col3:
        raw_output = BytesIO()
        with pd.ExcelWriter(raw_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        raw_output.seek(0)
        st.download_button(
            label="📥 1. 주소 입력 완료된 원본(Raw) 다운로드",
            data=raw_output,
            file_name="주소완료_자료관리목록.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with col4:
        if st.button("🚀 2. 최종 보고서(서식유지) 집계 생성"):
            calc_df = df.copy()
            calc_df['금액'] = pd.to_numeric(calc_df.iloc[:, AMT_COL], errors='coerce')
            calc_df = calc_df[calc_df['금액'] >= TARGET_AMOUNT].copy()
            
            def categorize_region(addr):
                addr_str = str(addr)
                if target_region in addr_str: return 1 
                elif "충남" in addr_str or "충청남도" in addr_str: return 2
                else: return 3
                
            calc_df['지역구분'] = calc_df.iloc[:, ADDR_COL].apply(categorize_region)
            
            results = {
                ('공사', 1): [0, 0], ('공사', 2): [0, 0], ('공사', 3): [0, 0],
                ('용역', 1): [0, 0], ('용역', 2): [0, 0], ('용역', 3): [0, 0],
                ('물품', 1): [0, 0], ('물품', 2): [0, 0], ('물품', 3): [0, 0],
            }
            
            for _, row in calc_df.iterrows():
                g_type = str(row.iloc[1]).strip()
                g_loc = row['지역구분']
                amount = row['금액']
                if (g_type, g_loc) in results:
                    results[(g_type, g_loc)][0] += 1
                    results[(g_type, g_loc)][1] += amount
            
            try:
                wb = openpyxl.load_workbook(BytesIO(base64.b64decode(TEMPLATE_BASE64)))
                ws = wb.active
                
                for row in ws.iter_rows(min_row=1, max_row=4):
                    for cell in row:
                        if type(cell).__name__ != 'MergedCell':
                            if isinstance(cell.value, str) and "천안" in cell.value:
                                cell.value = cell.value.replace("천안", target_region)
                
                ws['B5'] = results[('공사', 1)][0]; ws['B6'] = results[('공사', 1)][1]
                ws['C5'] = results[('공사', 2)][0]; ws['C6'] = results[('공사', 2)][1]
                ws['D5'] = results[('공사', 3)][0]; ws['D6'] = results[('공사', 3)][1]
                
                ws['F5'] = results[('용역', 1)][0]; ws['F6'] = results[('용역', 1)][1]
                ws['G5'] = results[('용역', 2)][0]; ws['G6'] = results[('용역', 2)][1]
                ws['H5'] = results[('용역', 3)][0]; ws['H6'] = results[('용역', 3)][1]
                
                ws['J5'] = results[('물품', 1)][0]; ws['J6'] = results[('물품', 1)][1]
                ws['K5'] = results[('물품', 2)][0]; ws['K6'] = results[('물품', 2)][1]
                ws['L5'] = results[('물품', 3)][0]; ws['L6'] = results[('물품', 3)][1]
                
                output = BytesIO()
                wb.save(output)
                output.seek(0)
                
                st.download_button(
                    label="📥 완성된 실적보고서 다운로드",
                    data=output,
                    file_name=f"지역경제활성화_실적보고({target_region}기준).xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"⚠️ 템플릿 로딩 중 오류가 발생했습니다: {e}")
else:
    st.info("👈 왼쪽 사이드바에서 자료관리목록 엑셀 파일을 업로드해 주세요.")