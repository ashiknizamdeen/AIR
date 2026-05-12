import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5-20251001"

MARKETS = [
    "ROW", "Japanese", "Korean", "Mandarin", "Malay",
    "Cambodian", "Thai", "Vietnamese", "Sri Lankan",
]

LOCATIONS = ["Bangkok", "Kuala Lumpur", "Mumbai", "Warsaw", "Manila"]

FLOWS = ["CM", "IDVASS", "IDVAAS HALO", "IGPO", "MESSENGER", "PI", "MULTI-SKILL"]

METRICS = [
    "Maxbill", "Utilization", "Volumes", "AHT", "Decision AHT",
    "Throughput", "No handle count", "No handle AHT",
    "Skip count", "Skip AHT", "Transfer out count", "Transfer out AHT",
    "Reason%", "Accuracy%", "Precision%", "Recall%", "Other",
]

# None = agent assesses from context; otherwise a fixed criticality hint
METRIC_CRITICALITY = {
    "Maxbill":            "High",
    "Utilization":        "Medium",
    "Volumes":            "Medium",
    "AHT":                "Medium",
    "Decision AHT":       "Medium",
    "Throughput":         None,
    "No handle count":    None,
    "No handle AHT":      None,
    "Skip count":         "Low",
    "Skip AHT":           "Low",
    "Transfer out count": None,
    "Transfer out AHT":   None,
    "Reason%":            "Low",
    "Accuracy%":          "Low",
    "Precision%":         "Low",
    "Recall%":            "Low",
    "Other":              "Low",
}

# ── Market → available flows (subset per market for demo realism) ─────────────
MARKET_FLOWS = {
    "ROW":        ["CM", "IDVASS", "IGPO", "MESSENGER", "PI"],
    "Japanese":   ["CM", "IDVAAS HALO", "IGPO", "MESSENGER"],
    "Korean":     ["CM", "PI", "MULTI-SKILL", "MESSENGER"],
    "Mandarin":   ["CM", "IDVASS", "IGPO", "PI"],
    "Malay":      ["CM", "MESSENGER", "PI", "MULTI-SKILL"],
    "Cambodian":  ["CM", "IGPO", "MESSENGER"],
    "Thai":       ["CM", "IDVASS", "PI", "MULTI-SKILL"],
    "Vietnamese": ["CM", "IDVAAS HALO", "MESSENGER", "IGPO"],
    "Sri Lankan": ["CM", "PI", "MESSENGER"],
}

# ── 10 reviewers per market ───────────────────────────────────────────────────
MARKET_REVIEWERS = {
    "ROW": [
        "alex_row", "jordan_row", "morgan_row", "casey_row", "riley_row",
        "taylor_row", "sam_row", "jamie_row", "quinn_row", "reese_row",
    ],
    "Japanese": [
        "yuki_jp", "haruto_jp", "sakura_jp", "kenji_jp", "aiko_jp",
        "hana_jp", "ren_jp", "sota_jp", "miku_jp", "taro_jp",
    ],
    "Korean": [
        "jisoo_kr", "minjun_kr", "hyunjin_kr", "sooyeon_kr", "taehyun_kr",
        "yuna_kr", "junho_kr", "seulgi_kr", "jaehyun_kr", "nayeon_kr",
    ],
    "Mandarin": [
        "wei_cn", "fang_cn", "ming_cn", "ling_cn", "hong_cn",
        "xiao_cn", "jun_cn", "mei_cn", "ping_cn", "lei_cn",
    ],
    "Malay": [
        "ahmad_my", "nurul_my", "wei_my", "farah_my", "rajan_my",
        "hafiz_my", "aishah_my", "azrul_my", "siti_my", "hazwan_my",
    ],
    "Cambodian": [
        "sophea_kh", "dara_kh", "chan_kh", "mony_kh", "ratana_kh",
        "vanna_kh", "pisey_kh", "sokha_kh", "bunna_kh", "rith_kh",
    ],
    "Thai": [
        "somchai_th", "nattaya_th", "prayuth_th", "siriporn_th", "wanchai_th",
        "kanya_th", "jirat_th", "ploypailin_th", "thanakorn_th", "sunan_th",
    ],
    "Vietnamese": [
        "nguyen_vn", "tran_vn", "le_vn", "pham_vn", "hoang_vn",
        "do_vn", "vu_vn", "dang_vn", "bui_vn", "dao_vn",
    ],
    "Sri Lankan": [
        "nimal_lk", "kumari_lk", "ruwan_lk", "dilani_lk", "chamara_lk",
        "priya_lk", "saman_lk", "thilini_lk", "arjuna_lk", "malika_lk",
    ],
}


REVIEWER_FLOWS = {
    # ROW — flows: CM, IDVASS, IGPO, MESSENGER, PI
    "alex_row":   ["CM"],       "jordan_row": ["IDVASS"],
    "morgan_row": ["MESSENGER"],"casey_row":  ["PI"],
    "riley_row":  ["CM"],       "taylor_row": ["IGPO"],
    "sam_row":    ["CM"],       "jamie_row":  ["IDVASS"],
    "quinn_row":  ["MESSENGER"],"reese_row":  ["IGPO"],

    # Japanese — flows: CM, IDVAAS HALO, IGPO, MESSENGER
    "yuki_jp":   ["CM"],        "haruto_jp": ["CM"],
    "sakura_jp": ["IDVAAS HALO"],"kenji_jp": ["MESSENGER"],
    "aiko_jp":   ["IGPO"],      "hana_jp":   ["CM"],
    "ren_jp":    ["IDVAAS HALO"],"sota_jp":  ["IDVAAS HALO"],
    "miku_jp":   ["MESSENGER"], "taro_jp":   ["IGPO"],

    # Korean — flows: CM, PI, MULTI-SKILL, MESSENGER
    "jisoo_kr":   ["CM"],       "minjun_kr":  ["PI"],
    "hyunjin_kr": ["CM"],       "sooyeon_kr": ["MESSENGER"],
    "taehyun_kr": ["PI"],       "yuna_kr":    ["CM"],
    "junho_kr":   ["PI"],       "seulgi_kr":  ["MULTI-SKILL"],
    "jaehyun_kr": ["MESSENGER"],"nayeon_kr":  ["MULTI-SKILL"],

    # Mandarin — flows: CM, IDVASS, IGPO, PI
    "wei_cn":  ["CM"],  "fang_cn": ["IGPO"],
    "ming_cn": ["CM"],  "ling_cn": ["IDVASS"],
    "hong_cn": ["PI"],  "xiao_cn": ["CM"],
    "jun_cn":  ["IGPO"],"mei_cn":  ["IDVASS"],
    "ping_cn": ["PI"],  "lei_cn":  ["IGPO"],

    # Malay — flows: CM, MESSENGER, PI, MULTI-SKILL
    "ahmad_my":  ["CM"],        "nurul_my":  ["MESSENGER"],
    "wei_my":    ["CM"],        "farah_my":  ["PI"],
    "rajan_my":  ["MESSENGER"], "hafiz_my":  ["CM"],
    "aishah_my": ["MULTI-SKILL"],"azrul_my": ["PI"],
    "siti_my":   ["MESSENGER"], "hazwan_my": ["MULTI-SKILL"],

    # Cambodian — flows: CM, IGPO, MESSENGER
    "sophea_kh": ["CM"],       "dara_kh":   ["MESSENGER"],
    "chan_kh":   ["CM"],       "mony_kh":   ["IGPO"],
    "ratana_kh": ["MESSENGER"],"vanna_kh":  ["CM"],
    "pisey_kh":  ["IGPO"],     "sokha_kh":  ["CM"],
    "bunna_kh":  ["MESSENGER"],"rith_kh":   ["IGPO"],

    # Thai — flows: CM, IDVASS, PI, MULTI-SKILL
    "somchai_th":    ["CM"],          "nattaya_th":    ["PI"],
    "prayuth_th":    ["CM"],          "siriporn_th":   ["IDVASS"],
    "wanchai_th":    ["PI"],          "kanya_th":      ["CM"],
    "jirat_th":      ["MULTI-SKILL"], "ploypailin_th": ["PI"],
    "thanakorn_th":  ["IDVASS"],      "sunan_th":      ["MULTI-SKILL"],

    # Vietnamese — flows: CM, IDVAAS HALO, MESSENGER, IGPO
    "nguyen_vn": ["CM"],        "tran_vn":   ["MESSENGER"],
    "le_vn":     ["CM"],        "pham_vn":   ["IDVAAS HALO"],
    "hoang_vn":  ["IGPO"],      "do_vn":     ["CM"],
    "vu_vn":     ["MESSENGER"], "dang_vn":   ["IDVAAS HALO"],
    "bui_vn":    ["IGPO"],      "dao_vn":    ["MESSENGER"],

    # Sri Lankan — flows: CM, PI, MESSENGER
    "nimal_lk":   ["CM"],       "kumari_lk":  ["PI"],
    "ruwan_lk":   ["CM"],       "dilani_lk":  ["MESSENGER"],
    "chamara_lk": ["PI"],       "priya_lk":   ["CM"],
    "saman_lk":   ["MESSENGER"],"thilini_lk": ["PI"],
    "arjuna_lk":  ["CM"],       "malika_lk":  ["MESSENGER"],
}

SEVERITY_COLORS = {
    "Critical": "#FF4B4B",
    "High":     "#FF8C00",
    "Medium":   "#FFC300",
    "Low":      "#00C853",
    "Unknown":  "#888888",
}

SEVERITY_ICONS = {
    "Critical": "🔴",
    "High":     "🟠",
    "Medium":   "🟡",
    "Low":      "🟢",
    "Unknown":  "⚪",
}
