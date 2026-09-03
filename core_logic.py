import hashlib
import re
import threading
import time
import urllib.parse
import uuid
from datetime import datetime
from io import BytesIO

import pandas as pd
import requests
import streamlit as st

MAX_CONCURRENT = 10
IDLE_TIMEOUT_SECONDS = 600
QUEUE_POLL_SECONDS = 5
WAITING_STALE_SECONDS = QUEUE_POLL_SECONDS * 6
DEFAULT_TARGET_AMOUNT = 500000

API_URL = "https://apis.data.go.kr/1230000/ao/UsrInfoService02/getPrcrmntCorpBasicInfo02"

CHUNGNAM_REGIONS = ["천안", "아산", "공주", "보령", "서산", "논산", "계룡", "당진", "금산", "부여", "서천", "청양", "홍성", "예산", "태안"]
SCHOOL_LEVELS = ["학교(유)", "학교(초)", "학교(중)", "학교(고)", "학교(특수)", "교육지원청", "직속기관"]
CONTRACT_METHODS = ["수의계약", "입찰", "조달구매"]
COMPETITION_METHODS = [
    "1인수의(단일견적)", "2인수의(공개견적)", "제3자단가", "다수공급자2단계경쟁(MAS)",
    "우수조달", "중앙조달", "자체(제한경쟁)", "자체(일반경쟁)", "협상", "2단계(규격가격동시)",
]
PURCHASE_PURPOSES = ["교육용", "도서(간행물 등)", "그 외"]

FALLBACK_COLS = {"type": 1, "contract_method": 2, "contract_name": 4, "contract_date": 5, "amount": 6, "company": 16, "biz": 18, "address": 20}
HEADER_ALIASES = {
    "type": ["목적물", "목적물별", "계약구분", "구분", "계약종류"],
    "contract_method": ["계약방법", "계약 방식", "계약방식"],
    "competition_method": ["견적/경쟁방법", "견적경쟁방법", "견적방법", "경쟁방법"],
    "contract_name": ["계약명", "계약건명", "건명", "품명", "사업명"],
    "contract_date": ["계약일자", "계약일", "계약체결일", "계약일시"],
    "amount": ["계약금액(원)", "계약금액", "집행금액", "금액"],
    "company": ["업체명", "계약업체명", "계약상대자", "계약상대자명", "상호"],
    "biz": ["사업자등록번호", "사업자번호", "사업자 등록번호"],
    "address": ["주소", "업체주소", "사업장주소", "소재지주소"],
}

@st.cache_resource
def get_room_state():
    return {"active": {}, "waiting": {}, "lock": threading.RLock()}

def ensure_session_id():
    if "sid" in st.query_params: st.session_state.session_id = st.query_params["sid"]
    else:
        st.session_state.session_id = str(uuid.uuid4()); st.query_params["sid"] = st.session_state.session_id

def acquire_slot() -> bool:
    room=get_room_state(); now=time.time(); my_sid=st.session_state.session_id
    with room["lock"]:
        for sid in [sid for sid,t in room["active"].items() if sid != my_sid and now-t > IDLE_TIMEOUT_SECONDS]: room["active"].pop(sid,None)
        for sid in [sid for sid,(_,seen) in room["waiting"].items() if sid != my_sid and now-seen > WAITING_STALE_SECONDS]: room["waiting"].pop(sid,None)
        if my_sid in room["active"]:
            room["active"][my_sid]=now; room["waiting"].pop(my_sid,None); return True
        joined=room["waiting"].get(my_sid,(now,now))[0]; room["waiting"][my_sid]=(joined,now)
        order=sorted(room["waiting"].items(),key=lambda x:x[1][0]); free=MAX_CONCURRENT-len(room["active"])
        for sid,_ in order[:max(free,0)]: room["active"][sid]=now; room["waiting"].pop(sid,None)
        return my_sid in room["active"]

def waiting_status():
    room=get_room_state(); my_sid=st.session_state.session_id
    with room["lock"]:
        order=sorted(room["waiting"].items(),key=lambda x:x[1][0]); active=len(room["active"]); waiting=len(room["waiting"])
    pos=next((i+1 for i,(sid,_) in enumerate(order) if sid==my_sid),None); return active,waiting,pos

def release_slot():
    room=get_room_state()
    with room["lock"]: room["active"].pop(st.session_state.session_id,None); room["waiting"].pop(st.session_state.session_id,None)

def touch_slot():
    room=get_room_state()
    with room["lock"]:
        if st.session_state.session_id in room["active"]: room["active"][st.session_state.session_id]=time.time()

def normalize_header(value): return re.sub(r"[\s\n\r\t()（）\[\]{}_/·ㆍ.-]+","",str(value or "")).lower()
def normalize_biz_no(value):
    if pd.isna(value): return ""
    digits=re.sub(r"\D","",re.sub(r"\.0$","",str(value).strip())); return digits if len(digits)==10 else ""

def get_api_key():
    try:
        key = st.secrets.get("datagokr", "")
    except Exception:
        key = ""
    if not key:
        raise RuntimeError("Streamlit Secrets에 'datagokr' API 키가 설정되지 않았습니다.")
    return str(key).strip()

@st.cache_data(show_spinner=False,ttl=86400)
def get_addr_api(biz_num):
    biz_clean=normalize_biz_no(biz_num)
    if not biz_clean: return None
    params={"serviceKey":urllib.parse.unquote(get_api_key()),"pageNo":"1","numOfRows":"10","type":"json","inqryDiv":"3","bizno":biz_clean}
    try:
        res=requests.get(API_URL,params=params,timeout=10); res.raise_for_status(); data=res.json()
        if "nkoneps.com.response.ResponseError" in data: return None
        items=data.get("response",{}).get("body",{}).get("items")
        if not items: return None
        item_list=items if isinstance(items,list) else items.get("item",[])
        if isinstance(item_list,dict): item_list=[item_list]
        if item_list:
            first=item_list[0]; return f"{first.get('adrs','')} {first.get('dtlAdrs','')}".strip() or None
    except (requests.RequestException,ValueError,TypeError,KeyError): return None
    return None

@st.cache_data(show_spinner=False)
def load_excel_normalized(file_bytes: bytes,min_cols:int=21):
    d=pd.read_excel(BytesIO(file_bytes)); headers=[str(c).strip() for c in d.columns]; d.columns=range(d.shape[1])
    if d.shape[1] < min_cols: d=d.reindex(columns=range(min_cols)); headers.extend([f"열{i+1}" for i in range(len(headers),min_cols)])
    return d,tuple(headers)

def file_fingerprint(files): return tuple((f.name,hashlib.sha256(f.getvalue()).hexdigest()) for f in files)
def find_source_col(headers,key):
    normalized=[normalize_header(h) for h in headers]
    for alias in HEADER_ALIASES.get(key,[]):
        a=normalize_header(alias)
        for i,h in enumerate(normalized):
            if h==a or (a and a in h): return i
    fallback=FALLBACK_COLS.get(key); return fallback if fallback is not None and fallback < len(headers) else None

def source_col(headers,key):
    idx=find_source_col(headers,key); return FALLBACK_COLS.get(key) if idx is None else idx

def safe_value(row,idx,default=""):
    if idx is None or idx>=len(row): return default
    value=row.iloc[idx]; return default if pd.isna(value) else value

def missing_address_mask(series):
    text=series.astype(str).str.strip(); return series.isna() | text.eq("") | text.str.lower().isin(["nan","none","null"])
def categorize_region_code(addr,target_region):
    text=str(addr or "").strip()
    if target_region and target_region in text: return 1
    if "충남" in text or "충청남도" in text: return 2
    return 3

def region_label(code): return {1:"충남도내(관내)",2:"충남도내(관외)",3:"타시도"}.get(code,"타시도")
def shorten_address(addr):
    text=re.sub(r"\s+"," ",str(addr or "").strip())
    if not text or text.lower() in ("nan","none"): return ""
    text=text.replace("충청남도","충남"); parts=text.split(); return text if len(parts)<=2 else " ".join(parts[:2])
def normalize_contract_type(value):
    text=str(value or "").strip()
    for key in ("공사","용역","물품"):
        if key in text: return key
    return text

def classify_purchase_purpose(contract_name):
    text=re.sub(r"\s+","",str(contract_name or ""))
    if not text: return "그 외"
    if "도서" in text and not any(k in text for k in ["교과용도서","교과서","업무용간행물","신문"]): return "도서(간행물 등)"
    if any(k in text for k in ["간식","우유","급식","식재료","식대","도시락","피복","화초","청소용","시설관리"]): return "그 외"
    edu=["학습준비물","교재","교구","수업","교육활동","교육운영","교육과정","놀이자료","미술재료","특성화프로그램","체험활동","체험학습","과학재료","창의","유아용","교수학습","특수학급","방과후","늘봄","돌봄"]
    return "교육용" if any(k in text for k in edu) else "그 외"

def display_headers(raw_headers,width):
    headers=list(raw_headers[:width]); headers += [f"열{i+1}" for i in range(len(headers),width)] if len(headers)<width else []
    seen={}; out=[]
    for h in headers:
        base=str(h or "열"); seen[base]=seen.get(base,0)+1; out.append(base if seen[base]==1 else f"{base}_{seen[base]}")
    return out

def to_datetime_or_blank(value):
    if value in (None,"") or (isinstance(value,float) and pd.isna(value)): return ""
    try: return pd.to_datetime(value).to_pydatetime()
    except Exception: return str(value)
def format_money(value):
    try: return int(round(float(value)))
    except Exception: return 0

def records_from_source(df,headers,target_amount,target_region):
    cols={k:find_source_col(headers,k) for k in HEADER_ALIASES}; amount_col,biz_col,addr_col,type_col=(source_col(headers,k) for k in ["amount","biz","address","type"])
    amount=pd.to_numeric(df.iloc[:,amount_col],errors="coerce").fillna(0); work=df.loc[amount>=target_amount]; records=[]
    for _,row in work.iterrows():
        ctype=normalize_contract_type(safe_value(row,type_col))
        if ctype not in ["공사","용역","물품"]: continue
        address_full=str(safe_value(row,addr_col,"")).strip(); address_missing=not address_full or address_full.lower() in ("nan","none","null"); contract_name=str(safe_value(row,cols.get("contract_name"),"")).strip()
        records.append({"목적물":ctype,"계약방법":str(safe_value(row,cols.get("contract_method"),"")).strip(),"견적경쟁방법":str(safe_value(row,cols.get("competition_method"),"")).strip(),"계약명":contract_name,"계약일자":to_datetime_or_blank(safe_value(row,cols.get("contract_date"),"")),"계약금액":format_money(safe_value(row,amount_col,0)),"업체명":str(safe_value(row,cols.get("company"),"")).strip(),"주소":shorten_address(address_full),"소재지":region_label(categorize_region_code(address_full,target_region)),"구입목적":classify_purchase_purpose(contract_name) if ctype=="물품" else "","비고":"주소 미확인 → 타시도 임시분류" if address_missing else ""})
    return records

def aggregate_records(records):
    base={(t,loc):[0,0] for t in ["공사","용역","물품"] for loc in [1,2,3]}; edu={loc:[0,0] for loc in [1,2,3]}; book={loc:[0,0] for loc in [1,2,3]}; loc_map={"충남도내(관내)":1,"충남도내(관외)":2,"타시도":3}
    for rec in records:
        t=rec["목적물"]; loc=loc_map.get(rec["소재지"],3); amt=format_money(rec["계약금액"]); base[(t,loc)][0]+=1; base[(t,loc)][1]+=amt
        if t=="물품" and rec["구입목적"]=="교육용": edu[loc][0]+=1; edu[loc][1]+=amt
        if t=="물품" and str(rec["구입목적"]).startswith("도서"): book[loc][0]+=1; book[loc][1]+=amt
    return base,edu,book