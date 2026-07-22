import streamlit as st
import anthropic

# --- ページ基本設定 ---
st.set_page_config(
    page_title="プロンプトジェネレーター",
    page_icon="🪄",
    layout="centered"
)

st.title("🪄 プロンプトジェネレーター")
st.caption("簡単な単語やアイデアから、指定したAIモデルに最適な詳細プロンプトを自動作成します。")

# --- APIキーの取得 ---
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
    client = anthropic.Anthropic(api_key=api_key)
except Exception:
    st.error("⚠️ ANTHROPIC_API_KEY が設定されていません。Streamlit Cloud の Secrets を確認してください。")
    st.stop()

# --- 入力フォーム ---
st.subheader("1. パラメータ設定")

col1, col2 = st.columns(2)

with col1:
    output_lang = st.selectbox(
        "🌐 出力言語",
        ["日本語", "英語"]
    )

with col2:
    target_model = st.selectbox(
        "🤖 対象モデル",
        ["Claude (Anthropic)", "ChatGPT (OpenAI)", "Midjourney / Stable Diffusion"]
    )

keyword_input = st.text_input(
    "💡 単語 / アイデア (必須)",
    placeholder="例: ブログ記事の要約、レトロなサイバーパンクの街並み"
)

custom_rules = st.text_area(
    "⚙️ 独自ルール / 制約条件 (任意)",
    placeholder="例:\n- 必ず表形式で出力させる指示を入れる\n- 初心者にもわかりやすいトーンで出力させる",
    height=120
)

generate_btn = st.button("✨ 詳細プロンプトを生成する", type="primary", use_container_width=True)

# --- 生成処理 ---
if generate_btn:
    if not keyword_input.strip():
        st.warning("⚠️ 単語またはアイデアを入力してください。")
    else:
        with st.spinner("Claude が最適プロンプトを生成中..."):
            model_instructions = ""
            if "Claude" in target_model:
                model_instructions = "- XMLタグ（例: <context>, <instructions>）を使用した構造化プロンプトにしてください。"
            elif "ChatGPT" in target_model:
                model_instructions = "- Markdownの見出しや役割定義（「あなたは〜です」）を効果的に使用してください。"
            elif "Midjourney" in target_model:
                model_instructions = "- 画像生成AI向けの英文プロンプト形式（画質・スタイル・パラメーター）にしてください。"

            system_prompt = f"""あなたはプロンプトエンジニアリングのスペシャリストです。
ユーザーから渡される情報をもとに、指定されたAIモデルが最高のパフォーマンスを発揮する詳細プロンプトを作成してください。

【出力条件】
1. 指定言語: {output_lang} で出力してください。（※画像生成用モデルの場合は原則英語）
2. 対象モデル: {target_model}
3. 対象モデル向け最適化ルール:
{model_instructions}
4. ユーザー指定の独自ルール:
{custom_rules if custom_rules.strip() else "なし"}

【出力フォーマット】
説明や挨拶などの前置き・後置きは一切不要です。ユーザーがそのままコピーして使えるプロンプト本文のみを出力してください。
"""

            user_prompt = f"以下の単語/アイデアをもとに詳細プロンプトを作成してください:\n\n{keyword_input}"

            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                generated_prompt = response.content[0].text

                st.subheader("2. 生成結果")
                st.code(generated_prompt, language="markdown")
                st.success("✅ 右上のアイコンからワンクリックでコピーできます。")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")