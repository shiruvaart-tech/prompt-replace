import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="画像生成プロンプトジェネレーター", page_icon="🎨", layout="centered")

st.title("🎨 画像生成プロンプトジェネレーター")
st.caption("単語やイメージから、指定したUIツール・モデルに最適化された画像プロンプトを作成します（Gemini Free API版）。")

# --- APIキー取得 ＆ Gemini クライアント初期化 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("⚠️ GEMINI_API_KEY が設定されていません。Streamlit の Settings > Secrets を確認してください。")
    st.stop()

# --- パラメータ選択 ---
st.subheader("1. 環境・モデル設定")

col1, col2 = st.columns(2)

with col1:
    ui_tool = st.selectbox(
        "🛠️ 使用ツール (UI)",
        ["AUTOMATIC1111 (WebUI) / Forge", "ComfyUI", "WebUI / Webサービス (Krea / Midjourney等)"]
    )

with col2:
    model_arch = st.selectbox(
        "🧠 モデルアーキテクチャ",
        [
            "Krea 2 (Krea AI)",
            "Pony XL (SDXL)",
            "Illustrious XL (SDXL)",
            "FLUX.1",
            "SDXL (標準/1.5互換)",
            "Anima / その他"
        ]
    )

col3, col4 = st.columns(2)

with col3:
    style_type = st.selectbox(
        "🎭 描画スタイル",
        ["アニメ・イラスト (Anime / Manga)", "リアル・実写 (Photorealistic)", "3D / Concept Art", "指定なし (自動判断)"]
    )

with col4:
    output_lang = st.selectbox(
        "🌐 出力プロンプト言語",
        ["英語 (推奨)", "日本語 (解説付き)"]
    )

keyword_input = st.text_input(
    "💡 単語 / ポーズ / シチュエーション (必須)",
    placeholder="例: 黒髪ロングの巫女、神社、桜が舞っている、笑顔",
)

custom_rules = st.text_area(
    "⚙️ 独自ルール / クリップボード用メモ (任意)",
    placeholder="例:\n- 構図はmedium shotを指定する\n- Lora用トリガーワード: my_character を先頭に入れる\n- ネガティブプロンプトも出力する",
    height=100
)

generate_btn = st.button("✨ 専用プロンプトを生成する", type="primary", use_container_width=True)

# --- 生成処理 ---
if generate_btn:
    if not keyword_input.strip():
        st.warning("⚠️ 単語またはアイデアを入力してください。")
    else:
        with st.spinner("Gemini がモデル別プロンプトを構築中..."):

            # --- モデルごとのプロンプト生成プロトコル定義 ---
            arch_instruction = ""
            
            if "Krea 2" in model_arch:
                arch_instruction = """
- Krea 2 の最新レンダリングエンジンに最適化された、詳細かつ表現豊かな「英語の自然言語（文章）」を中心に記述してください。
- 被写体の詳細、表情、衣装、周囲のアトモスフィア（雰囲気）、ライティング（例: cinematic lighting, soft volumetric rays）、カメラ構図（例: wide angle shot, 85mm lens, depth of field）を具体的にテキストで描写してください。
- カンマ区切りのタグ羅列よりも、意味の通った詳細な描写文（Description Style）を優先してください。
"""
            elif "Pony" in model_arch:
                arch_instruction = """
- Pony XL特有のトリガー/品質タグ（例: score_9, score_8_up, score_7_up, source_anime 等）を先頭に必ず配置してください。
- 要素の記述にはカンマ区切りのDanbooruスタイルのタグ（1girl, long hair, black hair, smile, shrine, cherry blossoms等）を使用してください。
"""
            elif "Illustrious" in model_arch:
                arch_instruction = """
- Illustrious XLに最適化された Danbooru タグ中心の構成にしてください。
- 品質タグ（masterpiece, highly detailed等）や画風指定タグを効果的に配置してください。
"""
            elif "FLUX" in model_arch:
                arch_instruction = """
- FLUX.1のテキストエンコーダー（T5）の強みを活かし、カンマ区切りタグではなく「詳細で具体的にシーンを描写した英語の自然言語（文章）」で記述してください。
- 被写体、衣装、ポーズ、照明、背景、構図、カメラの画角を文章で詳しく描写してください。
"""
            elif "SDXL" in model_arch:
                arch_instruction = """
- 自然言語による文脈記述と、カンマ区切りの強調タグ（(masterpiece:1.2), (detailed background:1.1)等）をバランスよく組み合わせてください。
"""
            else:
                arch_instruction = """
- 対象モデルに一般的な高品質タグと明確な描画要素（カンマ区切り）で構成してください。
"""

            # --- ツール(UI)ごとのプロトコル定義 ---
            tool_instruction = ""
            if "ComfyUI" in ui_tool:
                tool_instruction = """
- ComfyUIのCLIP Text Encodeノードに貼り付けやすいよう、ポーズ/キャラクター/背景/品質などのノードごとの分離（または明確なセクション分け）を意識したテキスト構造にしてください。
"""
            elif "WebUI" in ui_tool:
                tool_instruction = """
- WebUIの「Prompt」および「Negative Prompt」欄にそのままコピペして使えるフォーマットで出力してください。
"""

            # --- システムプロンプトの組み立て ---
            system_instruction = f"""あなたは画像生成AI（Krea 2, Stable Diffusion, ComfyUI, FLUX等）のプロンプトエンジニアリングのスペシャリストです。
ユーザーが与えた単語/シチュエーションをもとに、指定されたツールおよびモデルアーキテクチャで最高の画質・再現度が得られる画像生成プロンプトを作成してください。

【環境設定】
1. UIツール: {ui_tool} ({tool_instruction})
2. モデルアーキテクチャ: {model_arch} ({arch_instruction})
3. 指定スタイル: {style_type}
4. ユーザー指定の独自ルール: {custom_rules if custom_rules.strip() else "なし"}

【出力フォーマットルール】
- 前置きや挨拶は不要です。そのままコピーして使えるコードブロック形式で出力してください。
- Krea 2 や FLUX などの自然言語メインのモデルでは Negative Prompt は原則不要ですが、モデルや独自ルールで求められている場合のみ出力してください。
- 出力言語指定が「英語 (推奨)」の場合は、プロンプト本体は純粋な英語で出力してください。
"""

            user_prompt = f"以下の要素から画像生成プロンプトを作成してください:\n\n{keyword_input}"

            try:# Gemini 1.5 Flash モデルを使用して生成
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                ),
            )
                
                generated_prompt = response.text

                st.subheader("2. 生成されたプロンプト")
                st.code(generated_prompt, language="markdown")
                st.success("✅ 生成完了！右上のコピーアイコンでクリップボードにコピーできます。")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
