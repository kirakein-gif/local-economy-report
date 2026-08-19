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
st.set_page_config(page_title="지역경제활성화 자동 집계 시스템", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# --- 커스텀 CSS 디자인 주입 ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #f8fafc;
    }
    
    [data-testid="stSidebar"] {
        background-color: rgb(52, 73, 94) !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] {
        background-color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] * {
        color: #333333 !important;
        fill: #333333 !important;
    }
    
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
    
    div.stDownloadButton > button {
        background-color: #059669;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease 0s;
        width: 100%;
    }
    div.stDownloadButton > button:hover {
        background-color: #047857;
        transform: translateY(-2px);
    }
    
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
TARGET_AMOUNT = 500000

# ★ 변환하신 템플릿의 긴 문자열을 아래 따옴표 사이에 반드시 넣어주십시오.
TEMPLATE_BASE64 = ""

# ---------------------------------------------------------
# 2. 로직: API 주소 가져오기 (검증된 구조 반영)
# ---------------------------------------------------------
def get_addr_api(biz_num, corp_name):
    if pd.isna(biz_num):
        return None
    biz_clean = str(biz_num).replace("-", "").strip()
    
    params = {
        "serviceKey": urllib.parse.unquote(MY_G2B_API_KEY),
        "pageNo": "1",
        "numOfRows": "10",
        "type": "json",
        "inqryDiv": "3",
        "bizno": biz_clean,
    }
    
    try:
        res = requests.get(API_URL, params=params, verify=False, timeout=5)
        data = res.json()
        
        body = data.get("response", {}).get("body", {}) or {}
        items = body.get("items")
        
        if items:
            item_list = items if isinstance(items, list) else items.get("item", [])
            if isinstance(item_list, dict):
                item_list = [item_list]
                
            if item_list and len(item_list) > 0:
                it = item_list[0]
                return f"{it.get('adrs', '')} {it.get('dtlAdrs', '')}".strip()
                
    except Exception:
        pass
        
    return None

# ---------------------------------------------------------
# 3. 메인 UI 및 데이터 흐름
# ---------------------------------------------------------
st.markdown('<h1 class="main-title">📊 지역경제활성화 자동 집계 시스템</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.header("📂 데이터 업로드")
    target_region = st.selectbox("기준 지역 선택", CHUNGNAM_REGIONS, index=0)
    data_file = st.file_uploader("자료관리목록 엑셀 업로드", type=["xls", "xlsx"])

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
    
    st.subheader("📈 데이터 처리 현황")
    met1, met2, met3 = st.columns(3)
    met1.metric("업로드된 유효 데이터", f"{is_valid_biz.sum()}건")
    met2.metric("집계 대상 (50만 원 이상)", f"{total_target_rows}건")
    if missing_count > 0:
        met3.metric("주소 누락 (조치 필요)", f"{missing_count}건", delta="-작업 진행 필요", delta_color="inverse")
    else:
        met3.metric("주소 누락", "0건", delta="모두 채워짐!", delta_color="normal")
    st.markdown("---")
    
    with st.sidebar:
        st.markdown("---")
        st.header("📍 주소 자동 채우기")
        if st.button("1️⃣ 파일 내 주소 자체 채우기", use_container_width=True):
            known_addrs = df.dropna(subset=[df.columns[ADDR_COL]]).set_index(df.columns[BIZ_COL])[df.columns[ADDR_COL]].to_dict()
            df[df.columns[ADDR_COL]] = df[df.columns[ADDR_COL]].fillna(df[df.columns[BIZ_COL]].map(known_addrs))
            st.session_state.df = df
            st.rerun()

        if st.button("2️⃣ 조달청 API 검색", use_container_width=True):
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
        st.success("✨ 집계 대상(50만 원 이상)의 주소가 모두 채워졌습니다! 좌측 메뉴에서 결과를 다운로드하세요.")
        
    with st.sidebar:
        st.markdown("---")
        st.header("📥 결과물 다운로드")
        
        raw_output = BytesIO()
        with pd.ExcelWriter(raw_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        raw_output.seek(0)
        
        st.download_button(
            label="📥 1. 주소 완료 원본(Raw)",
            data=raw_output,
            file_name="주소완료_자료관리목록.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
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
                label="🚀 2. 최종 실적보고서(서식)",
                data=output,
                file_name=f"지역경제활성화_실적보고({target_region}기준).xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"⚠️ 템플릿 로딩 중 오류가 발생했습니다: {e}")

        st.markdown("---")
        st.caption("개발: 천안버들유치원 나대현<br>문의 및 오류 신고는 메신저로 부탁드립니다.", unsafe_allow_html=True)
else:
    st.info("👈 왼쪽 사이드바에서 자료관리목록 엑셀 파일을 먼저 업로드해 주세요.")
    
    with st.sidebar:
        st.markdown("---")
        st.caption("개발: 천안버들유치원 나대현<br>문의 및 오류 신고는 메신저로 부탁드립니다.", unsafe_allow_html=True)