# -*- coding: utf-8 -*-
"""
고전에 묻다 — 문학·질문·쓸모에 관한 독서토론실
2023학년도 고려대학교 일반전형-계열적합형(인문계열) 면접 지문을 활용한
학급 독서토론용 Streamlit 웹앱

실행 방법:
    pip install streamlit
    streamlit run reading_discussion_app.py
"""

import html
import random
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).parent / "opinions.db"


def get_connection():
    """매 호출마다 새 커넥션을 열어, 서로 다른 학생의 세션(스레드) 간 충돌을 피한다."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS opinions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            question TEXT NOT NULL,
            opinion TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn

# ============================================================
# 0. 페이지 설정 & 디자인 (한지 + 먹 + 낙관 인장 콘셉트)
# ============================================================

st.set_page_config(
    page_title="고전에 묻다 · 독서토론실",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

:root {
    --paper: #F4EFE2;
    --paper-card: #FBF8F1;
    --ink: #262220;
    --ink-soft: #5B564E;
    --jade: #33463C;
    --jade-soft: #4C6358;
    --seal: #9B2226;
    --gold: #A9822F;
    --hairline: #D8CFB8;
}

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

.stApp { background-color: var(--paper); color: var(--ink); }
.stApp p, .stApp li, .stApp span, .stApp label, .stApp div { color: var(--ink); }
[data-testid="stWidgetLabel"] p { color: var(--ink) !important; }
[data-testid="stMarkdownContainer"] { color: var(--ink); }
.stTextArea textarea, .stTextInput input, .stNumberInput input {
    background-color: var(--paper-card) !important; color: var(--ink) !important;
}
[data-baseweb="select"] * { color: var(--ink) !important; }
[data-testid="stAlert"] p { color: var(--ink) !important; }

section[data-testid="stSidebar"] {
    background-color: var(--jade);
}
section[data-testid="stSidebar"] * { color: #EFE9DA !important; }
section[data-testid="stSidebar"] .stRadio label { font-family: 'Noto Serif KR', serif; }

h1, h2, h3 { font-family: 'Noto Serif KR', serif !important; color: var(--jade) !important; }

hr.ink-rule { border: none; border-top: 1.5px solid var(--hairline); margin: 1.2rem 0; }

.hero {
    background: linear-gradient(135deg, var(--jade) 0%, var(--jade-soft) 100%);
    color: #F4EFE2; padding: 2.2rem 2.4rem; border-radius: 6px; margin-bottom: 1.6rem;
}
.hero h1 { color: #F4EFE2 !important; margin: 0 0 .5rem 0; font-size: 2.0rem; }
.hero p { color: #E7DFC9; font-size: 1.02rem; line-height: 1.7; margin: 0; }

.seal {
    display:inline-flex; align-items:center; justify-content:center;
    min-width: 2.1rem; height: 2.1rem; padding: 0 .3rem; border-radius: 50%;
    background: var(--seal); color: #F4EFE2; font-family:'Noto Serif KR', serif;
    font-weight:700; font-size:1.05rem; flex-shrink:0;
}

.passage-card {
    background: var(--paper-card); border-left: 5px solid var(--jade);
    border-radius: 4px; padding: 1.3rem 1.6rem; margin-bottom: 1.1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.passage-head { display:flex; align-items:center; gap:.7rem; margin-bottom:.6rem; }
.passage-title { font-family:'Noto Serif KR', serif; font-weight:700; font-size:1.15rem; color: var(--ink); }
.passage-source { color: var(--ink-soft); font-size:.86rem; }
.passage-body { color: var(--ink); line-height: 1.85; font-size: 1.0rem; white-space: pre-line; }
.hl { background: #F0DA9E; padding: 0 3px; border-radius: 2px; font-weight:600; }

.tag {
    display:inline-block; background:#EAE3CF; color: var(--jade); border:1px solid var(--hairline);
    padding: .15rem .6rem; border-radius: 999px; font-size: .78rem; margin: .15rem .3rem .15rem 0;
}

.q-card {
    background: var(--paper-card); border: 1px solid var(--hairline); border-radius: 6px;
    padding: 1.1rem 1.4rem; margin-bottom: .9rem;
}
.q-num {
    display:inline-flex; align-items:center; justify-content:center; width:1.8rem; height:1.8rem;
    border-radius:50%; background: var(--gold); color:#fff; font-weight:700; margin-right:.6rem;
}

.book-card {
    background: var(--paper-card); border-radius: 6px; padding: 1rem 1.2rem; height: 100%;
    border-top: 3px solid var(--gold);
}
.book-title { font-family:'Noto Serif KR', serif; font-weight:700; font-size:1.02rem; color: var(--ink); }
.book-author { color: var(--ink-soft); font-size: .85rem; margin-bottom:.4rem; }

.footer-note { color: var(--ink-soft); font-size:.82rem; text-align:center; margin-top:2rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def seal(text: str) -> str:
    return f'<div class="seal">{text}</div>'


# ============================================================
# 1. 데이터: 지문 원문
# ============================================================

PASSAGES = {
    "가": {
        "title": "문학은 왜 '쓸모없기에' 인간을 억압하지 않는가",
        "source": "김현, 문학의 무용성에 관한 비평문",
        "keywords": ["문학의 무용성", "억압에 대한 인식", "자기기만의 고발"],
        "body": (
            "문학은 권력에의 지름길이 아니며, 그런 의미에서 문학은 써먹는 것이 아니다. "
            "그러나 역설적이게도 문학은 그 써먹지 못한다는 것을 써먹고 있다. 문학을 함으로써 "
            "우리는 서유럽 한 위대한 지성이 탄식했듯 배고픈 사람 하나 구하지 못하며, 물론 "
            "출세하지도, 큰돈을 벌지도 못한다. 그러나 그것은 바로 그러한 점 때문에 인간을 "
            "억압하지 않는다. 인간에게 유용한 것은 대체로 그것이 유용하다는 것 때문에 인간을 "
            "억압한다. 억압된 욕망은 그것이 강력하게 억압되면 억압될수록 더욱 강하게 부정적으로 "
            "작용한다. 그러나 문학은 유용한 것이 아니기 때문에 인간을 억압하지 않는다. 억압하지 "
            "않는 문학은 억압하는 모든 것이 인간에게 부정적으로 작용하는 것을 보여준다. 인간은 "
            "문학을 통하여 억압하는 것과 억압당하는 것의 정체를 파악하고, 그 부정적 힘을 인지한다. "
            "그 부정적 힘의 인식은 인간으로 하여금 세계를 주체적으로 개조하지 않으면 안 된다는 "
            "당위성을 느끼게 한다. 인간은 문학을 통해, 그것에서 얻는 감동을 통해, 자기와 다른 "
            "형태의 인간의 기쁨과 슬픔과 고통을 확인하고 그것이 자기의 것일 수도 있다는 것을 "
            "느낀다. 문학은 배고픈 거지를 구하지 못한다. 그러나 인간을 억누르는 억압의 정체를 "
            "뚜렷하게 보여준다. 그리고 그것은 인간의 자기기만을 되돌아보고 날카롭게 고발한다."
        ),
    },
    "나": {
        "title": "질문한다는 것, 능동적 존재로서 살아있다는 것",
        "source": "질문의 의미에 관한 강연문",
        "keywords": ["질문의 능동성", "반성적 사유", "체제로부터의 자유"],
        "body": (
            "질문하는 일은 우리에게 지금도 여전히 중요합니다. 우리도 호모사피엔스이니까요. "
            "묻는다는 것은 살아있음을 뜻합니다. 아직, 기계는 많은 경우 입력된 정보를 질문 없이 "
            "받아들일 뿐입니다. 곧 질문하지 않는 사람은 기계에 불과하다고도 말할 수 있습니다. "
            "질문한다는 것은 사람으로서 능동적으로 존재한다는 의미가 있습니다. 어린아이들이 왜, "
            "뭔데, 하고 물으며 주위를 받아들이면서 한 명의 주체로 성장하는 것을 떠올릴 필요가 "
            "있습니다. 질문은 사유의 한 행위로, 이미 결정되어 있는 개념이나 미리 규정되어 내려오는 "
            "가치들을 선험적으로 무조건 수용하지 않기 때문에 발생합니다. 질문은 삶의 가능성을 "
            "제한하고 한계짓는 체제를 거스르면서 생명의 자연스러움을 회복하는 행위입니다. 세상의 "
            "단순 부속품이 되지 않으려면 질문해야 합니다. 또한, 질문하는 일은 반성한다는 의미입니다. "
            "반성한다는 것은 판단의 조건들을 성찰하고 사유한다는 것으로 곧 돌이켜보는 일이죠. "
            "반성은 모두가 확고하다고 여기는 현재의 질서에서 잠시 벗어나는 질문입니다."
        ),
    },
    "다": {
        "title": "쓸모 있음과 쓸모없음의 사이, 그리고 완전한 올바름",
        "source": "장자의 우화 두 편 — 산속의 나무 · 벗의 거위",
        "keywords": ["무용지용", "완전한 올바름", "외물에 규정받지 않음"],
        "body": (
            "장자가 산속을 거닐다가 가지와 잎사귀가 무성한 큰 나무를 보았는데 벌목하는 사람들이 "
            "그 옆에 머물러 있으면서도 그 나무를 베지 않았다. 그 까닭을 물었더니 \u201c쓸 만한 것이 "
            "없다.\u201d고 하였다. 장자가 말했다. \u201c이 나무는 쓸모가 없기 때문에 천수를 다할 수 "
            "있구나.\u201d\n\n"
            "장자가 산에서 나와 옛 친구의 집에서 묵게 되었다. 친구가 기뻐하며 아이 종에게 거위를 "
            "잡아서 요리하라고 시켰더니, 아이 종이 여쭙기를 \u201c한 마리는 잘 우는데, 한 마리는 "
            "울지 못합니다. 어느 것을 잡을까요?\u201d 하였다. 친구가 말했다. \u201c울지 못하는 놈을 "
            "잡아라.\u201d\n\n"
            "다음 날 제자가 장자에게 물었다. \u201c어제 산중의 나무는 쓸모없었기 때문에 천수를 다할 "
            "수 있었고 지금 주인집 거위는 쓸모없었기 때문에 죽었습니다. 선생께서는 장차 어디에 몸을 "
            "두시겠습니까?\u201d 장자가 웃으면서 말했다. \u201c나는 쓸모 있음과 쓸모없음의 사이에 "
            "머물 것이다. 그런데 쓸모 있음과 쓸모없음의 사이에 머무는 것은 한편으로는 그럴 듯하지만 "
            "아직 <span class='hl'>완전한 올바름</span>이 아니기 때문에 세속의 번거로움을 면치 못할 "
            "것이다. 하지만 도(道)와 덕(德)을 타고 어디든 정처 없이 떠다니듯 노니는 사람은 그렇지 "
            "않다. 명예도 없고 비방도 없이 한번은 하늘에 오르는 용이 되었다가 또 한번은 땅속을 기는 "
            "뱀이 되어 때와 함께 변화하면서 한 가지를 오로지 고집하는 것을 기꺼워하지 않는다. 한번 "
            "하늘 높이 올라가고 한번 땅속 깊이 내려감에 조화로움을 도량으로 삼아서 만물의 시초에 "
            "자유롭게 노닐며, 만물을 만물로 존재하게 하면서도 스스로는 외물(外物)에 의해 사물로 "
            "규정 받지 않으니 어떤 외물이 번거롭게 할 수 있겠는가! 이것이 옛날 신농과 황제가 "
            "지켰던 삶의 법칙이다.\u201d"
        ),
    },
    "라": {
        "title": "과학기술자의 사회적 책임과 반성적 사고 — 사하로프와 제너",
        "source": "과학자의 윤리적 책임에 관한 서술문",
        "keywords": ["반성적 사고", "사회적 책임", "사하로프", "제너"],
        "body": (
            "과학기술자는 과학의 양면을 제대로 파악하여 인류의 복지에 긍정적으로 기여하려는 선한 "
            "의도와 사회적 책임을 가져야 한다. 과학이 우리의 삶에 엄청난 영향을 미치고 있는 만큼 "
            "과학 기술자는 사회적 책임과 의무로부터 결코 자유로울 수 없으며, 전문가로서 그에 "
            "상응하는 윤리적 책임과 자기 정당화의 의무를 지니고 있어야 한다. 과학적 지식을 사회의 "
            "선을 위해 사용하고자 할 때 가장 중요한 것은 반성적 사고이다. 반성적 사고를 통해 과학 "
            "기술은 보다 바람직한 방향으로 나아갈 것이다. 따라서 반성적 사고는 과학기술자들의 행위를 "
            "규제하고 억압하는 것이 아니라 과학기술자들이 인류에 해악을 끼치지 않고 바른 방향으로 "
            "나아갈 수 있도록 해주는 길잡이라고 할 수 있다.\n\n"
            "소비에트 연방의 안드레이 사하로프는 20세기 후반 수소폭탄 개발에 결정적으로 기여했다. "
            "당시 그는 동서 냉전의 상황에서 조국의 군사적 열세를 만회하는 데 도움이 되고 싶다는 "
            "생각으로 개발에 매진하여 정부로부터 그 공로를 크게 인정받았다. 하지만 시간이 지날수록 "
            "자신의 판단과 행동이 옳았던가를 되짚어 보며, 나중에는 소비에트 체제에 대한 저항 운동에 "
            "적극적으로 나서게 되었다.\n\n"
            "영국의 제너는 18세기 후반 천연두를 예방하기 위해 우두법(牛痘法)을 개발했다. 시행 "
            "초기에는 대중의 몰이해로 많은 반대에 부딪혔으나, 그는 우두법의 효능을 확신하고 설득에 "
            "나섰다. 이후 영국 과학계로부터 그 효능을 인정받아 우두법이 널리 보급되었다."
        ),
    },
}

# ============================================================
# 2. 데이터: 핵심 개념 해설
# ============================================================

CONCEPTS = [
    {
        "title": "① 문학의 '무용함'이 만드는 유용함 — (가)",
        "body": (
            "김현은 문학이 배고픈 사람을 구하지도, 출세를 시켜주지도 못하는 '쓸모없는' 것이라는 "
            "점에서 출발합니다. 그런데 바로 이 쓸모없음이 문학을 특별하게 만듭니다. 세상의 유용한 "
            "것들(돈, 권력, 지식)은 유용하다는 이유로 인간을 억압하지만, 문학은 유용하지 않기 "
            "때문에 억압하지 않습니다. 오히려 문학은 그 억압의 정체를 '보여주는' 역할을 합니다. "
            "즉 문학은 '쓸모없음'을 통해 '억압을 인식하게 하는' 다른 차원의 쓸모를 갖게 되는 "
            "역설적 구조입니다."
        ),
        "extend": (
            "확장 질문: 우리가 '쓸모없다'고 여기는 다른 활동(음악 감상, 산책, 낙서, 게임)도 "
            "비슷한 역설을 가질 수 있을까요? '무언가에 저항하기 위해 아무 쓸모가 없어야 한다'는 "
            "역설은 문학에만 해당될까요, 다른 예술 장르에도 적용될까요?"
        ),
    },
    {
        "title": "② 질문 = 능동적 주체 되기 — (나)",
        "body": (
            "이 글은 질문을 '기계와 인간을 가르는 기준'으로 제시합니다. 기계는 입력된 정보를 "
            "그대로 받아들이지만, 인간은 '왜?'라고 물으며 스스로 판단의 주체가 됩니다. 질문은 "
            "이미 정해진 개념과 가치를 무비판적으로 받아들이지 않는 행위이며, 동시에 '반성' — "
            "즉 자기 판단의 근거를 되짚어보는 행위이기도 합니다."
        ),
        "extend": (
            "확장 질문: AI가 점점 정교한 질문을 만들어낼 수 있게 된 지금, '질문하는 능력'을 "
            "인간과 기계를 구분하는 기준으로 계속 쓸 수 있을까요? 이 글이 쓰였을 때와 지금 "
            "우리가 다르게 답해야 할 부분이 있을까요?"
        ),
    },
    {
        "title": "③ 장자의 '완전한 올바름' — (다)",
        "body": (
            "장자는 '쓸모 있음과 쓸모없음의 사이'에 머무는 태도조차 아직 '완전한 올바름'이 "
            "아니라고 말합니다. 왜냐하면 그 태도는 여전히 '유용함/무용함'이라는 기준 자체를 "
            "전제하고 그 사이에서 줄타기를 하는 것이기 때문입니다. 장자가 말하는 완전한 "
            "올바름이란, 애초에 유용/무용이라는 외부의 잣대(외물)로 자신을 규정받지 않는 상태, "
            "즉 그 기준 자체를 초월하는 경지입니다."
        ),
        "extend": (
            "확장 질문: (가)의 김현이 말하는 문학의 '무용함'은 장자의 기준으로 보면 아직 "
            "'완전한 올바름'에 도달했다고 할 수 있을까요, 아닐까요? 그 이유를 '유용함이라는 "
            "잣대에서 완전히 자유로운가'라는 질문으로 따져 봅시다."
        ),
    },
    {
        "title": "④ 과학자의 반성적 사고와 사회적 책임 — (라)",
        "body": (
            "이 글은 반성적 사고를 과학자를 '억압'하는 규제가 아니라 '바른 방향으로 이끄는 "
            "길잡이'로 설명합니다. 사하로프는 처음엔 애국심이라는 '유용함'에 이끌려 무기 개발에 "
            "매진했지만, 시간이 지나며 스스로 되짚어보는 반성을 거쳐 체제에 저항하는 쪽으로 "
            "나아갑니다. 반면 제너는 처음부터 인류의 복지(우두법 보급)라는 목적을 향해 나아갔고, "
            "대중의 반대에도 자신의 확신을 설득으로 관철시켰습니다."
        ),
        "extend": (
            "확장 질문: 사하로프의 '뒤늦은 반성'과 제너의 '일관된 확신'은 둘 다 '반성적 "
            "사고'의 사례로 볼 수 있을까요? 결과가 좋았다고 해서 그 과정의 반성까지 "
            "긍정적으로 평가할 수 있을까요?"
        ),
    },
]

# ============================================================
# 3. 데이터: 토론 질문
# ============================================================

OFFICIAL_QUESTIONS = [
    {
        "num": "논제 1",
        "q": "제시문 (가)의 '문학'과 제시문 (나)의 '질문'의 유사성을 설명하시오.",
        "direction": (
            "'문학'과 '질문' 모두 (1) 이미 정해진 개념·가치·질서를 무비판적으로 수용하지 않고, "
            "(2) 억압/체제의 정체를 스스로 인식하게 만들며, (3) 인간을 수동적 존재가 아닌 능동적 "
            "주체로 세운다는 공통점이 있습니다. 두 글의 핵심어를 하나씩 짝지어 비교하면 구조가 "
            "잘 드러납니다."
        ),
    },
    {
        "num": "논제 2",
        "q": "제시문 (다)의 밑줄 친 부분(완전한 올바름)을 토대로, 제시문 (가)를 평가하시오.",
        "direction": (
            "핵심은 '완전한 올바름'이 유용/무용의 기준 자체를 초월한 경지라는 점입니다. (가)의 "
            "김현은 '무용하기 때문에 유용하다'는 논리를 펴는데, 이는 결국 무용함을 다시 유용함으로 "
            "환원하려는 시도이기도 합니다. 즉 (가)는 아직 유용/무용의 틀 안에 머물러 있어 장자가 "
            "말하는 '완전한 올바름'에는 이르지 못했다고 평가할 수 있습니다."
        ),
    },
    {
        "num": "논제 3",
        "q": "제시문 (가), (나), (다)를 종합하여 제시문 (라)의 '사하로프'와 '제너'의 행적에 대해 "
             "자신의 의견을 자유롭게 말해 보시오.",
        "direction": (
            "세 제시문의 개념 도구(문학의 억압 인식, 질문·반성의 능동성, 완전한 올바름)를 각각 "
            "사하로프와 제너의 사례에 적용해 보세요. 예: 사하로프는 초기엔 애국심(유용함)에 이끌려 "
            "질문·반성이 부족했으나 이후 체제에 저항하며 반성적 주체가 되었고, 제너는 처음부터 "
            "인류 복지라는 목적의식과 확신을 갖고 반대를 설득했다는 점에서 대비됩니다. 둘 중 누가 "
            "'완전한 올바름'에 더 가까웠는지, 혹은 둘 다 아직 도달하지 못했는지 자신의 논리로 "
            "판단해 보세요."
        ),
    },
]

EXTENDED_QUESTIONS = {
    "이해 확인 질문": [
        "(가)에서 '억압하지 않는 문학'이 실제로 하는 일은 무엇인가요? 본문에서 근거를 찾아 말해보세요.",
        "(나)에서 '질문하지 않는 사람은 기계에 불과하다'는 말의 의미를 자신의 언어로 풀어보세요.",
        "(다)에서 '쓸모 있음과 쓸모없음의 사이'와 '완전한 올바름'은 어떻게 다른가요?",
    ],
    "비판적 사고 질문": [
        "문학이 정말로 '유용하지 않기 때문에' 인간을 억압하지 않는다는 (가)의 논리에 반박할 수 있는 지점은 없을까요? (예: 문학이 특정 이념을 선전하는 도구로 쓰인 역사적 사례)",
        "'질문하지 않으면 기계와 같다'는 (나)의 주장은 너무 단정적인 것 아닐까요? 질문하지 않아도 능동적으로 살아가는 경우는 없을까요?",
        "장자의 '완전한 올바름'은 현실에서 실천 가능한 삶의 태도일까요, 아니면 이상적 관념에 가까울까요?",
    ],
    "삶과 연결하는 질문": [
        "내가 최근에 '쓸모없다'고 생각했지만 돌아보니 의미가 있었던 경험이 있나요?",
        "나는 평소에 얼마나 '질문'하며 살고 있나요? 당연하게 받아들이는 것 중 다시 물어볼 만한 것은 무엇인가요?",
        "만약 내가 사하로프나 제너와 같은 상황에 놓인 과학기술자라면, 어떤 기준으로 판단을 내리고 싶은가요?",
    ],
    "찬반 토론 질문": [
        "찬반: '쓸모없는 것이야말로 진짜 쓸모 있다'는 주장에 찬성하는가, 반대하는가?",
        "찬반: 사하로프처럼 나중에 반성하고 저항한 과학자와, 제너처럼 처음부터 확신을 갖고 밀어붙인 과학자 중 더 책임 있는 태도를 보인 쪽은 누구인가?",
        "찬반: 반성적 사고는 (라)의 말처럼 정말 과학자를 '억압하지 않는 길잡이'일 뿐일까, 실질적으로는 '규제'로 작동하는 것은 아닐까?",
    ],
}

# ============================================================
# 4. 데이터: 추천 도서
# ============================================================

BOOKS = {
    "문학은 왜 필요한가 — (가) 확장": [
        ("행복한 책읽기", "김현", "이 지문 저자가 남긴 독서 일기",
         "비평가 김현이 세상을 떠나기 전인 1985년 12월부터 1989년 12월까지 4년간 쓴 사적인 일기 모음이다. 그날그날 읽은 책과 본 영화에 대한 짧은 단상부터, 다가오는 죽음을 마주하며 삶을 돌아보는 깊은 사유까지 담겨 있다. 논리적인 비평문과는 다른 결의 글이라, (가) 지문에서 문학의 무용함과 억압하지 않는 힘을 말한 저자의 육성을 훨씬 더 가까이서 만날 수 있다."),
        ("문학이란 무엇인가", "장 폴 사르트르 (정명환 옮김)", "참여문학의 입장에서 본 문학론",
         "사르트르가 1947년 발표한 문학론으로, 글을 쓰고 읽는다는 것이 세계에 대한 하나의 태도를 드러내는 행위이며, 작가는 그 글을 통해 독자의 자유에 호소한다고 주장한다. '문학이 무엇을 할 수 있는가'라는 질문에 참여문학의 입장에서 정면으로 답하는 책으로, 문학이 아무것도 구하지 못한다는 (가)의 무용론과 나란히 놓고 비교하며 읽으면 좋은 대조를 이룬다."),
        ("무한한 대화", "모리스 블랑쇼", "끝나지 않는 '대화'로서의 문학",
         "블랑쇼가 1969년에 펴낸 문학·언어론 모음집이다. 그는 문학을 하나의 결론으로 정리되지 않는 끝없는 '대화'로 보고, 파편적으로 이어지는 글쓰기가 어떻게 고정된 의미와 전체화된 담론에서 벗어나 세계를 새롭게 사유하게 하는지를 탐구한다. 다소 밀도가 높은 철학서이지만, (가)에서 말하는 문학의 무용함과 저항의 힘이라는 문제의식을 훨씬 더 깊은 층위로 확장해서 읽을 수 있게 해준다."),
    ],
    "질문과 사유의 힘 — (나) 확장": [
        ("소크라테스의 변명", "플라톤", "질문하는 삶의 원형",
         "사형 재판에 선 소크라테스가 자신을 변호하며 남긴 말을 제자 플라톤이 기록한 대화편이다. 그는 '캐묻지 않는 삶은 살 가치가 없다'고 말하며, 죽음 앞에서도 끝까지 질문을 멈추지 않는 태도를 보여준다. 정해진 권위와 통념에 안주하지 않고 스스로 묻는 사람이 되라는 이 책의 메시지는, (나)에서 말하는 '질문하는 삶'의 원형을 역사 속 실제 인물을 통해 확인하게 해준다."),
        ("생각의 지도", "리처드 니스벳 (최인철 옮김)", "동서양의 서로 다른 사고방식",
         "심리학자 리처드 니스벳이 동양과 서양이 세계를 인식하고 사고하는 방식 자체가 다르다는 것을 여러 심리 실험을 통해 실증적으로 보여주는 책이다. 우리가 당연하다고 여기는 사고방식조차 문화적으로 형성된 습관일 수 있다는 사실은, '질문하지 않으면 정해진 개념을 무조건 받아들이게 된다'는 (나)의 주장을 다른 각도에서, 더 넓은 시야로 다시 생각해보게 만든다."),
        ("무지한 스승", "자크 랑시에르 (양창렬 옮김)", "스스로 배우는 지적 해방",
         "랑시에르가 19세기 프랑스 교사 조제프 자코토의 실험적 교육 사례를 바탕으로 쓴 교육철학서다. 그는 가르치는 사람이 지식을 일방적으로 주입하지 않아도, 배우는 사람이 스스로 지적 능력을 발휘해 알아갈 수 있다는 '지적 해방'을 주장한다. 이미 정해진 개념과 권위를 그대로 받아들이지 않는다는 (나)의 질문 정신을, 교육이라는 구체적인 장면 속에서 다시 확인할 수 있는 책이다."),
    ],
    "장자와 무용지용 — (다) 확장": [
        ("삶의 실력, 장자", "최진석", "강의로 풀어낸 장자 철학",
         "동양철학자 최진석이 강의를 바탕으로 펴낸 장자 해설서다. 사람들이 흔히 오해하는 것과 달리 장자는 현실에서 도피한 사람이 아니라, 세상이 정해준 틀에 자신을 가두지 않고 끊임없이 내면의 두께를 단련해간 사람이라고 설명한다. 쓸모 있음과 쓸모없음의 경계마저 넘어서는 (다)의 '완전한 올바름'이라는 개념을, 오늘날의 언어로 훨씬 쉽게 풀어 이해할 수 있게 도와주는 입문서다."),
        ("장자", "오강남 풀이", "원문 우화 모음과 해설",
         "동양철학자 오강남이 장자 원문의 여러 우화들을 알기 쉬운 우리말로 옮기고 친절한 해설을 붙인 대중적인 책이다. (다) 지문에 나온 쓸모없는 나무와 우는 거위 이야기 외에도, 나비의 꿈이나 우물 안 개구리 같은 장자의 다른 유명한 우화들을 함께 읽으며 '무용지용'과 '완전한 올바름'에 관한 사유를 훨씬 더 폭넓고 깊게 확인할 수 있다."),
        ("숲에서 자본주의를 껴안다", "모타니 고스케 · NHK히로시마 취재팀", "쓸모없던 자원의 재발견",
         "지역경제학자 모타니 고스케와 NHK 히로시마 취재팀이 일본의 산골 마을을 직접 취재해 쓴 책이다. 그동안 버려지던 목재 폐기물을 연료로 재활용하는 등, 아무 쓸모가 없다고 여겨지던 자원을 되살려 돈에 크게 의존하지 않는 경제 공동체를 되살리는 실제 사례들을 보여준다. 무엇을 '쓸모없다'고 규정할지 그 기준 자체를 다시 묻게 만드는, 매우 현실적인 사례 모음이다."),
    ],
    "과학자의 책임과 윤리 — (라) 확장": [
        ("사하로프 회고록", "안드레이 사하로프", "본인이 직접 쓴 자서전",
         "안드레이 사하로프 자신이 쓴 자서전으로, 한국어판은 상·중·하 3권으로 출간되었다. 소련의 수소폭탄 개발을 주도했던 물리학자가 어떻게 무기 개발에 대한 회의를 느끼고 인권운동가로 전향했는지, 노벨평화상 수상과 그 이후 이어진 유배·가택연금 생활까지 본인의 목소리로 직접 기록했다. (라) 지문 속 사하로프의 '뒤늦은 반성'을 실제 당사자의 서술로 확인할 수 있는 가장 직접적인 자료다."),
        ("코스모스", "칼 세이건", "과학자의 겸허함과 책임감",
         "천문학자 칼 세이건이 우주의 탄생부터 인류 문명의 역사까지를 넘나들며 쓴 대중 과학서의 고전이다. 과학이 인류에게 안겨주는 경이로움을 생생히 전하는 동시에, 그 강력한 지식을 다루는 인간이 마땅히 지녀야 할 겸허함과 책임감에 대해서도 이야기한다. 과학기술자의 반성적 사고를 강조하는 (라)의 문제의식과 나란히 두고 읽기에 좋은 책이다."),
        ("침묵의 봄", "레이첼 카슨", "반성적 사고가 바꾼 정책",
         "해양생물학자 레이첼 카슨이 1962년에 발표한 책으로, 살충제 DDT가 새와 곤충을 비롯한 생태계 전체를 어떻게 서서히 파괴하는지를 치밀한 과학적 근거로 고발했다. 대중과 산업계의 거센 반발에도 자신의 연구 결과를 굽히지 않고 알린 한 과학자의 문제 제기가 실제로 사회와 정책을 바꾼 사례로, (라)가 말하는 '반성적 사고에서 사회적 실천으로'라는 흐름을 구체적으로 보여준다."),
    ],
}

# ============================================================
# 5. 사이드바 내비게이션
# ============================================================

st.sidebar.markdown("## 📜 고전 열람실")
st.sidebar.markdown("2023 고려대 계열적합형 · 인문계열 지문")
page = st.sidebar.radio(
    "이동",
    [
        "🏠 시작하기",
        "📖 지문 읽기",
        "🧭 핵심 개념 해설",
        "💬 토론 질문",
        "🗣️ 의견 나누기",
        "✍️ 논술 가이드",
        "📚 추천 도서",
        "🕰️ 토론 진행 도구",
    ],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption("학급 독서토론용으로 제작된 웹앱입니다. 원문 출처: 2023학년도 고려대학교 수시모집 일반전형-계열적합형 면접고사 자료.")

# session_state 초기화
if "notes" not in st.session_state:
    st.session_state.notes = {}


# ============================================================
# 페이지: 시작하기
# ============================================================

if page == "🏠 시작하기":
    st.markdown(
        """
        <div class="hero">
            <h1>고전에 묻다</h1>
            <p>
            문학은 왜 '쓸모없기에' 자유로운가? 질문한다는 것은 왜 살아있다는 증거인가?<br>
            장자가 말한 '완전한 올바름'이란 무엇인가? 그리고 과학자는 자신의 발견 앞에서<br>
            어떻게 책임져야 하는가 — 네 개의 제시문이 던지는 질문을 따라, 오늘 우리 반의 토론을 시작합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("### 이 웹앱으로 할 수 있는 것")
        st.markdown(
            """
            - **📖 지문 읽기**: 네 개 지문 (가)·(나)·(다)·(라)를 한 화면에서 나란히 읽습니다.
            - **🧭 핵심 개념 해설**: 각 지문의 핵심 개념을 쉽게 풀이하고, 확장 질문으로 사고를 넓힙니다.
            - **💬 토론 질문**: 실제 논제 3개 + 확장 토론 질문을 함께 다루고, 무작위로 질문을 뽑아 토론을 진행할 수 있습니다.
            - **✍️ 논술 가이드**: 채점 기준에 기반한 답안 개요 작성 틀을 제공합니다.
            - **📚 추천 도서**: 주제별로 더 읽어볼 책을 추천합니다.
            - **🕰️ 토론 진행 도구**: 조 편성, 발언 순서 뽑기, 타이머를 제공합니다.
            """
        )
    with col2:
        st.markdown("### 오늘의 토론 지도")
        for label, info in PASSAGES.items():
            st.markdown(
                f"""<div class="passage-card" style="padding:.8rem 1.1rem;">
                <div class="passage-head">{seal(label)}<span class="passage-title" style="font-size:1rem;">{info['title']}</span></div>
                </div>""",
                unsafe_allow_html=True,
            )

# ============================================================
# 페이지: 지문 읽기
# ============================================================

elif page == "📖 지문 읽기":
    st.header("📖 지문 읽기")
    st.caption("네 지문을 나란히 읽으며, 각 글의 핵심 주장을 표시해 두세요.")

    tabs = st.tabs([f"{k} — {v['title'][:14]}..." for k, v in PASSAGES.items()])
    for tab, (label, info) in zip(tabs, PASSAGES.items()):
        with tab:
            tags_html = "".join(f'<span class="tag">#{kw}</span>' for kw in info["keywords"])
            st.markdown(
                f"""
                <div class="passage-card">
                    <div class="passage-head">
                        {seal(label)}
                        <div>
                            <div class="passage-title">{info['title']}</div>
                            <div class="passage-source">{info['source']}</div>
                        </div>
                    </div>
                    <div class="passage-body">{info['body']}</div>
                    <div style="margin-top:.8rem;">{tags_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if label == "다":
                st.info("💡 노란 형광 표시(**완전한 올바름**)는 실제 시험지의 밑줄 친 부분입니다. 논제 2번에서 이 표현을 반드시 활용하세요.")

# ============================================================
# 페이지: 핵심 개념 해설
# ============================================================

elif page == "🧭 핵심 개념 해설":
    st.header("🧭 핵심 개념 해설")
    st.caption("각 지문의 핵심 개념을 정리하고, 더 깊이 생각해볼 확장 질문을 함께 담았습니다.")

    for c in CONCEPTS:
        with st.expander(c["title"], expanded=False):
            st.markdown(c["body"])
            st.markdown(
                f"""<div style="background:#EAE3CF; border-radius:6px; padding:.8rem 1rem; margin-top:.6rem;">
                🔎 <b>{c['extend'].split(':')[0]}:</b>{c['extend'].split(':',1)[1]}
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<hr class='ink-rule'>", unsafe_allow_html=True)
    st.subheader("네 지문을 잇는 하나의 흐름")
    st.markdown(
        """
        네 지문은 사실 하나의 질문으로 이어집니다: **"우리는 무엇을, 어떤 기준으로 '쓸모 있다'고
        판단하는가?"**

        - (가)와 (나)는 '무용해 보이는 것'(문학, 질문)이 오히려 억압에서 벗어나게 해준다고 말합니다.
        - (다)는 한 걸음 더 나아가, 유용/무용이라는 기준 자체를 넘어서는 것이 '완전한 올바름'이라고 말합니다.
        - (라)는 이 모든 논의를 실제 인물(사하로프, 제너)의 구체적 선택에 적용해 볼 수 있는 사례를 제공합니다.

        토론할 때는 이 순서(가→나→다→라)를 따라가며, "지금 우리는 어떤 기준으로 사하로프와 제너를
        평가하고 있는가?"를 계속 되짚어 보면 논의가 훨씬 깊어집니다.
        """
    )

# ============================================================
# 페이지: 토론 질문
# ============================================================

elif page == "💬 토론 질문":
    st.header("💬 토론 질문")

    sub = st.radio("질문 유형 선택", ["🎯 실제 논제 3개", "🌱 확장 토론 질문", "🎲 무작위 질문 뽑기"], horizontal=True)

    if sub == "🎯 실제 논제 3개":
        st.caption("고려대 면접고사에 실제로 출제된 논제입니다. 방향성 힌트를 참고해 조별로 논의해보세요.")
        for item in OFFICIAL_QUESTIONS:
            with st.container():
                st.markdown(
                    f"""<div class="q-card">
                    <div><span class="q-num">{item['num'][-1]}</span><b>{item['num']}</b></div>
                    <p style="margin-top:.6rem; font-weight:500;">{item['q']}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
                with st.expander("🧭 논의 방향성 힌트 보기"):
                    st.write(item["direction"])
                note_key = f"note_official_{item['num']}"
                st.session_state.notes[note_key] = st.text_area(
                    "우리 조의 생각 정리", key=note_key, height=90,
                    placeholder="토론 후 우리 조의 결론이나 핵심 논리를 적어보세요.",
                )

    elif sub == "🌱 확장 토론 질문":
        st.caption("실제 논제를 넘어, 더 넓고 깊게 생각해볼 수 있는 질문들입니다.")
        for category, qs in EXTENDED_QUESTIONS.items():
            st.markdown(f"#### {category}")
            for i, q in enumerate(qs):
                st.markdown(f"- {q}")
            st.markdown("")

    else:  # 무작위 질문 뽑기
        st.caption("발표할 조나 학생을 정한 뒤, 아래 버튼으로 무작위 질문을 뽑아 즉석 토론을 진행해보세요.")
        all_extended = [(cat, q) for cat, qs in EXTENDED_QUESTIONS.items() for q in qs]

        if "drawn_question" not in st.session_state:
            st.session_state.drawn_question = None

        if st.button("🎲 질문 뽑기", type="primary"):
            st.session_state.drawn_question = random.choice(all_extended)

        if st.session_state.drawn_question:
            cat, q = st.session_state.drawn_question
            st.markdown(
                f"""<div class="q-card" style="border:2px solid var(--seal);">
                <span class="tag">{cat}</span>
                <p style="margin-top:.6rem; font-size:1.1rem; font-weight:600;">{q}</p>
                </div>""",
                unsafe_allow_html=True,
            )

# ============================================================
# 페이지: 의견 나누기 (친구들과 실시간 누적 공유)
# ============================================================

elif page == "🗣️ 의견 나누기":
    st.header("🗣️ 의견 나누기")
    st.caption(
        "이름과 의견을 남기면, 이 웹앱에 접속한 학급 친구들 모두가 함께 볼 수 있어요. "
        "(같은 서버 주소로 접속했을 때만 서로의 의견이 공유됩니다.)"
    )

    conn = get_connection()
    question_options = [f"{q['num']} — {q['q']}" for q in OFFICIAL_QUESTIONS] + ["기타 (자유 주제)"]

    with st.form("opinion_form", clear_on_submit=True):
        name = st.text_input("이름", placeholder="예: 김민준")
        chosen_q = st.selectbox("어떤 논제에 대한 의견인가요?", question_options)
        opinion = st.text_area("내 의견", height=120, placeholder="이 논제에 대한 나의 생각을 자유롭게 적어보세요.")
        submitted = st.form_submit_button("✍️ 의견 남기기", type="primary")
        if submitted:
            if not name.strip() or not opinion.strip():
                st.warning("이름과 의견을 모두 입력해주세요.")
            else:
                conn.execute(
                    "INSERT INTO opinions (name, question, opinion, created_at) VALUES (?, ?, ?, ?)",
                    (name.strip(), chosen_q, opinion.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")),
                )
                conn.commit()
                st.success("의견이 등록되었습니다! 아래 목록에서 바로 확인할 수 있어요.")

    st.markdown("<hr class='ink-rule'>", unsafe_allow_html=True)

    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.subheader("📋 친구들이 남긴 의견 모아보기")
    with top_col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()

    filter_q = st.selectbox("논제별로 필터링해서 보기", ["전체 보기"] + question_options, key="filter_q")

    cur = conn.cursor()
    if filter_q == "전체 보기":
        rows = cur.execute(
            "SELECT name, question, opinion, created_at FROM opinions ORDER BY id DESC"
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT name, question, opinion, created_at FROM opinions WHERE question = ? ORDER BY id DESC",
            (filter_q,),
        ).fetchall()

    if not rows:
        st.info("아직 등록된 의견이 없습니다. 첫 의견을 남겨보세요!")
    else:
        st.caption(f"현재 {len(rows)}개의 의견이 등록되어 있습니다.")
        for name, question, opinion, created_at in rows:
            safe_name = html.escape(name)
            safe_question = html.escape(question)
            safe_opinion = html.escape(opinion).replace("\n", "<br>")
            st.markdown(
                f"""<div class="q-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b>{safe_name}</b>
                        <span style="color:var(--ink-soft); font-size:.8rem;">{created_at}</span>
                    </div>
                    <div class="passage-source" style="margin:.3rem 0;">{safe_question}</div>
                    <p style="margin-top:.4rem; white-space:normal;">{safe_opinion}</p>
                </div>""",
                unsafe_allow_html=True,
            )

    conn.close()

# ============================================================
# 페이지: 논술 가이드
# ============================================================

elif page == "✍️ 논술 가이드":
    st.header("✍️ 논술 가이드")
    st.caption("실제 채점 기준을 바탕으로, 답안의 뼈대를 세우는 개요 작성 도구입니다.")

    st.subheader("📋 채점 기준 체크리스트")
    st.markdown(
        """
        - **논제 1**: '문학'과 '질문'의 특징을 각각 정확히 짚고, 두 개념의 구조적 유사성을 체계적으로 설명했는가?
        - **논제 2**: 장자가 말한 '완전한 올바름'(유용/무용의 기준 자체를 초월함)을 정확히 이해했는가? 그것을 (가)의 문학론에 타당하게 적용했는가?
        - **논제 3**: (가)·(나)·(다)의 개념을 종합적으로 활용해 사하로프와 제너 두 사례를 각각 타당하게 평가했는가? 자신의 의견을 설득력 있게 전개했는가?
        """
    )

    st.markdown("<hr class='ink-rule'>", unsafe_allow_html=True)
    st.subheader("🖋️ 개요 작성 틀 (서론-본론-결론)")

    essay_target = st.selectbox("어떤 논제의 개요를 작성할까요?", [q["num"] + " — " + q["q"] for q in OFFICIAL_QUESTIONS])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**서론**")
        st.text_area("핵심 개념을 한 문장으로 정의하며 시작", key="essay_intro", height=140,
                     placeholder="예: 문학과 질문은 모두 정해진 가치를 그대로 받아들이지 않는 행위라는 점에서...")
    with c2:
        st.markdown("**본론**")
        st.text_area("근거를 지문에서 인용·요약하며 논리적으로 전개", key="essay_body", height=140,
                     placeholder="예: (가)에서는 ~라고 하였고, (나)에서는 ~라고 하였다. 이 둘은...")
    with c3:
        st.markdown("**결론**")
        st.text_area("자신의 판단(의견)을 명확히 정리하며 마무리", key="essay_conclusion", height=140,
                     placeholder="예: 따라서 나는 사하로프의 행적을 ~라고 평가한다. 왜냐하면...")

    st.markdown("<hr class='ink-rule'>", unsafe_allow_html=True)
    st.subheader("✅ 답안 작성 팁")
    st.markdown(
        """
        1. **개념어를 정확히 짚고 시작하기**: '억압하지 않는 문학', '완전한 올바름', '반성적 사고' 같은 지문 속 핵심어를 그대로 활용하면 논지가 분명해집니다.
        2. **지문 간 대응 관계 만들기**: (가)-(나), (다)-(가), (가)(나)(다)-(라)처럼 지문끼리 짝을 지어 비교하면 '종합적으로 고려'했다는 인상을 줍니다.
        3. **자유롭게 말하되 근거는 지문 안에서**: 논제 3번처럼 '자유롭게 의견을 말하라'는 요구는 있는 그대로의 감상이 아니라, 지문의 논리를 바탕으로 한 '설득력 있는' 주장을 뜻합니다.
        4. **결론에서 판단을 회피하지 않기**: '둘 다 맞다'보다는 '어떤 기준에서 누가 더 ~했다'처럼 구체적인 판단을 내리는 것이 채점 기준(타당하고 적실한 평가)에 부합합니다.
        """
    )

# ============================================================
# 페이지: 추천 도서
# ============================================================

elif page == "📚 추천 도서":
    st.header("📚 확장 독서를 위한 추천 도서")
    st.caption("각 지문의 주제를 더 깊이 탐구할 수 있는 책들입니다. 조별로 한 권씩 골라 다음 토론을 준비해보세요.")

    for theme, books in BOOKS.items():
        st.markdown(f"### {theme}")
        cols = st.columns(len(books))
        for col, (title, author, reason, summary) in zip(cols, books):
            with col:
                st.markdown(
                    f"""<div class="book-card">
                        <div class="book-title">{title}</div>
                        <div class="book-author">{author}</div>
                        <span class="tag">{reason}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
                with st.expander("책 내용 요약 보기"):
                    st.write(summary)
        st.markdown("")

# ============================================================
# 페이지: 토론 진행 도구
# ============================================================

elif page == "🕰️ 토론 진행 도구":
    st.header("🕰️ 토론 진행 도구")

    tool_tab1, tool_tab2, tool_tab3 = st.tabs(["👥 조 편성", "🎙️ 발언 순서 뽑기", "⏱️ 토론 타이머"])

    with tool_tab1:
        st.subheader("조 편성기")
        names_raw = st.text_area("학급 친구들 이름을 한 줄에 한 명씩 입력하세요", height=180,
                                  placeholder="김민준\n이서연\n박도윤\n...")
        group_size = st.slider("한 조당 인원 수", min_value=2, max_value=6, value=4)
        if st.button("🔀 조 편성하기"):
            names = [n.strip() for n in names_raw.splitlines() if n.strip()]
            if len(names) < 2:
                st.warning("이름을 2명 이상 입력해주세요.")
            else:
                random.shuffle(names)
                groups = [names[i:i + group_size] for i in range(0, len(names), group_size)]
                for idx, g in enumerate(groups, 1):
                    st.markdown(f"**{idx}조**: {', '.join(g)}")

    with tool_tab2:
        st.subheader("발언 순서 뽑기")
        names_raw2 = st.text_area("발언할 사람 이름을 한 줄에 한 명씩 입력하세요", height=180,
                                   placeholder="김민준\n이서연\n박도윤\n...", key="speak_names")
        if st.button("🎲 순서 뽑기"):
            names2 = [n.strip() for n in names_raw2.splitlines() if n.strip()]
            if len(names2) < 1:
                st.warning("이름을 1명 이상 입력해주세요.")
            else:
                random.shuffle(names2)
                for i, n in enumerate(names2, 1):
                    st.markdown(f"{i}번째 발언: **{n}**")

    with tool_tab3:
        st.subheader("토론 타이머")
        st.caption("조별 토론 시간을 재는 타이머입니다. 시작 버튼을 누르면 카운트다운이 시작됩니다.")
        minutes = st.number_input("몇 분으로 설정할까요?", min_value=1, max_value=60, value=8)
        timer_html = f"""
        <div style="font-family:'Noto Sans KR',sans-serif; text-align:center; padding: 1rem;
                    background:#FBF8F1; border-radius:8px; border:1px solid #D8CFB8;">
            <div id="timer-display" style="font-size:3rem; font-weight:700; color:#33463C; font-family:'Noto Serif KR',serif;">
                {int(minutes):02d}:00
            </div>
            <button id="start-btn" style="margin:.4rem; padding:.5rem 1.2rem; border:none; border-radius:6px;
                    background:#9B2226; color:white; font-weight:600; cursor:pointer;">시작</button>
            <button id="pause-btn" style="margin:.4rem; padding:.5rem 1.2rem; border:none; border-radius:6px;
                    background:#A9822F; color:white; font-weight:600; cursor:pointer;">일시정지</button>
            <button id="reset-btn" style="margin:.4rem; padding:.5rem 1.2rem; border:none; border-radius:6px;
                    background:#5B564E; color:white; font-weight:600; cursor:pointer;">초기화</button>
        </div>
        <script>
            const totalSeconds = {int(minutes)} * 60;
            let remaining = totalSeconds;
            let timerInterval = null;
            const display = document.getElementById('timer-display');

            function updateDisplay() {{
                const m = Math.floor(remaining / 60);
                const s = remaining % 60;
                display.textContent = String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
                if (remaining <= 0) {{
                    display.style.color = '#9B2226';
                    display.textContent = "시간 종료!";
                }}
            }}

            document.getElementById('start-btn').onclick = function() {{
                if (timerInterval) return;
                timerInterval = setInterval(function() {{
                    if (remaining > 0) {{
                        remaining -= 1;
                        updateDisplay();
                    }} else {{
                        clearInterval(timerInterval);
                        timerInterval = null;
                    }}
                }}, 1000);
            }};

            document.getElementById('pause-btn').onclick = function() {{
                clearInterval(timerInterval);
                timerInterval = null;
            }};

            document.getElementById('reset-btn').onclick = function() {{
                clearInterval(timerInterval);
                timerInterval = null;
                remaining = totalSeconds;
                display.style.color = '#33463C';
                updateDisplay();
            }};

            updateDisplay();
        </script>
        """
        st.iframe(timer_html, height=180)

# ============================================================
# 공통 푸터
# ============================================================

st.markdown(
    f"""<div class="footer-note">고전에 묻다 · 학급 독서토론용 웹앱 · 생성일 {datetime.now().strftime('%Y-%m-%d')}</div>""",
    unsafe_allow_html=True,
)
