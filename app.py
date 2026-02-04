# 2foods 見積書作成アプリ（Streamlit版）

import streamlit as st
import pandas as pd
from datetime import datetime, date
from pathlib import Path

from products import PRODUCTS, WATER_LOT_PATTERNS, RECIPIENTS, STAFF_LIST, SALES_AREAS
from database import save_quote, get_all_quotes, delete_quote, search_quotes
from pdf_generator import generate_pdf, get_pdf_filename

# 画像フォルダのパス
IMAGE_FOLDER = Path(r"G:\共有ドライブ\TWO\2foods\04_Strategic Sales\90_Sales\2Snack\00_全体ファイル\マスタ管理\画像")

# ページ設定
st.set_page_config(
    page_title="2foods 見積書作成アプリ",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        color: #333;
        border-bottom: 3px solid #d4a700;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .product-card {
        border: 2px solid #eee;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background: white;
    }
    .product-card-selected {
        border-color: #d4a700 !important;
        background: #fffef5 !important;
    }
    .stButton>button {
        background-color: #d4a700;
        color: white;
    }
    .stButton>button:hover {
        background-color: #b89000;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """メイン関数"""

    # サイドバー：ナビゲーション
    st.sidebar.title("メニュー")
    page = st.sidebar.radio(
        "ページ選択",
        ["見積書作成", "見積履歴", "商品マスター"],
        label_visibility="collapsed"
    )

    if page == "見積書作成":
        show_quote_form()
    elif page == "見積履歴":
        show_quote_history()
    else:
        show_product_master()


def show_quote_form():
    """見積書作成フォーム"""

    st.markdown('<h1 class="main-header">2foods 見積書作成アプリ</h1>', unsafe_allow_html=True)

    # === 基本情報セクション ===
    st.subheader("📋 基本情報")

    col1, col2 = st.columns(2)

    with col1:
        # 送付先
        recipient_options = ["-- 選択 --"] + RECIPIENTS + ["その他（直接入力）"]
        recipient_select = st.selectbox("送付先（企業名）", recipient_options)

        if recipient_select == "その他（直接入力）":
            recipient = st.text_input("送付先を入力", key="recipient_input")
        elif recipient_select != "-- 選択 --":
            recipient = recipient_select
        else:
            recipient = ""

        # 対象小売名
        retailer = st.text_input("対象小売名（任意）", placeholder="例：セブンイレブン")
        show_retailer = st.checkbox("見積に表示", value=True, key="show_retailer")

    with col2:
        # 担当者
        staff = st.selectbox("担当者", STAFF_LIST)

        # 日付
        quote_date = st.date_input("日付", value=date.today())

        # 販売エリア
        sales_area_options = st.multiselect(
            "販売エリア（複数選択可）",
            SALES_AREAS,
            default=["全国"]
        )
        # 「全国」が含まれている場合は全国のみ
        if "全国" in sales_area_options:
            sales_area = "全国"
        else:
            sales_area = "、".join(sales_area_options)

    st.divider()

    # === 商品選択セクション ===
    st.subheader("🛒 商品選択")

    # セッション状態の初期化
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = {}
    if 'water_selections' not in st.session_state:
        st.session_state.water_selections = {}

    # 商品をグリッド表示
    cols = st.columns(3)

    for idx, product in enumerate(PRODUCTS):
        col_idx = idx % 3

        with cols[col_idx]:
            # 2Water専用の処理
            if product.get('is_water'):
                render_water_product(product)
            else:
                render_normal_product(product, idx)

    st.divider()

    # === 備考セクション ===
    st.subheader("📝 備考")

    col1, col2 = st.columns(2)

    with col1:
        note_validity = st.checkbox("見積有効期限：次回提出時まで", value=True)
        note_leadtime = st.checkbox("リードタイム：中2-3日（受注〆時間 AM11:00）", value=True)

    with col2:
        note_water = st.checkbox("2Water CeramideはLT最大7日発生します。", value=True)
        note_noreturn = st.checkbox("返品不可", value=True)

    additional_notes = st.text_area("追加事項", placeholder="追加の備考があれば入力してください")

    # 備考をまとめる
    notes_list = []
    if note_validity:
        notes_list.append("・見積有効期限：次回提出時まで")
    if note_leadtime:
        notes_list.append("・リードタイム：中2-3日（受注〆時間 AM11:00）")
    if note_water:
        notes_list.append("・2Water CeramideはLT最大7日発生します。")
    if note_noreturn:
        notes_list.append("・返品不可")
    if additional_notes:
        notes_list.append(f"・{additional_notes}")
    notes = "\n".join(notes_list)

    st.divider()

    # === 確認・生成 ===
    st.subheader("✅ 確認・生成")

    # 選択された商品を収集
    selected_products = collect_selected_products()

    # プレビュー表示
    if selected_products:
        st.write(f"**選択商品数**: {len(selected_products)}件")
        preview_df = pd.DataFrame([
            {
                "商品名": p['name'],
                "卸価格": f"{p['wholesale_price']}円",
                "特別条件": p.get('special_condition', '-')
            }
            for p in selected_products
        ])
        st.dataframe(preview_df, hide_index=True, use_container_width=True)

    # ボタン
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        create_btn = st.button("📄 見積書を作成", type="primary", use_container_width=True)

    # 見積書作成処理
    if create_btn:
        # バリデーション
        if not recipient:
            st.error("送付先を入力してください")
            st.stop()
        if not selected_products:
            st.error("商品を選択してください")
            st.stop()
        if not sales_area:
            st.error("販売エリアを選択してください")
            st.stop()

        # PDF生成
        try:
            pdf_data = generate_pdf(
                recipient=recipient,
                retailer=retailer,
                show_retailer=show_retailer,
                staff=staff,
                quote_date=str(quote_date),
                sales_area=sales_area,
                products=selected_products,
                notes=notes
            )

            # データベースに保存
            quote_id = save_quote(
                quote_date=str(quote_date),
                recipient=recipient,
                retailer=retailer,
                staff=staff,
                sales_area=sales_area,
                products=selected_products,
                notes=notes
            )

            # セッションに保存
            st.session_state.pdf_data = pdf_data
            st.session_state.pdf_filename = get_pdf_filename(recipient, str(quote_date))
            st.session_state.last_quote_id = quote_id

            st.rerun()  # 画面を再描画してダウンロードボタンを表示

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

    # PDFダウンロードボタン（作成後に表示）
    if 'pdf_data' in st.session_state and st.session_state.pdf_data:
        st.success(f"見積書を作成しました！（履歴ID: {st.session_state.get('last_quote_id', '-')}）")

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.download_button(
                label="⬇️ PDFダウンロード",
                data=st.session_state.pdf_data,
                file_name=st.session_state.pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        with col2:
            if st.button("🔄 新規作成", use_container_width=True):
                st.session_state.pdf_data = None
                st.session_state.pdf_filename = None
                st.session_state.last_quote_id = None
                st.rerun()


def render_normal_product(product, idx):
    """通常商品のカード表示"""

    key_prefix = f"product_{idx}"
    is_selected = st.session_state.selected_products.get(idx, {}).get('selected', False)

    with st.container():
        # 画像と商品情報を横並び
        img_col, info_col = st.columns([1, 3])

        with img_col:
            # 商品画像を表示
            image_path = IMAGE_FOLDER / product.get('image', '')
            if image_path.exists():
                st.image(str(image_path), width=80)
            else:
                st.write("📦")  # 画像がない場合はアイコン

        with info_col:
            # チェックボックスと商品名
            selected = st.checkbox(
                f"**{product['name']}**",
                value=is_selected,
                key=f"{key_prefix}_check"
            )

            # 商品詳細
            st.caption(f"JAN: {product['jan']} | 容量: {product['volume']} | ケース入数: {product['case_qty']}")
            st.caption(f"想定小売: ¥{product['retail_price']} | 賞味期限: D{product['shelf_life']}")

        # 仕切価格と特別条件
        col1, col2 = st.columns(2)
        with col1:
            wholesale_price = st.number_input(
                "卸価格（円）",
                value=product['wholesale_price'],
                min_value=0,
                key=f"{key_prefix}_price"
            )
        with col2:
            special_condition = st.text_input(
                "特別条件",
                placeholder="例：5、5円",
                key=f"{key_prefix}_special"
            )

        # セッション状態を更新
        st.session_state.selected_products[idx] = {
            'selected': selected,
            'product': product,
            'wholesale_price': wholesale_price,
            'special_condition': special_condition
        }

        st.markdown("---")


def render_water_product(product):
    """2Water専用のカード表示"""

    # 画像と商品情報を横並び
    img_col, info_col = st.columns([1, 3])

    with img_col:
        image_path = IMAGE_FOLDER / product.get('image', '')
        if image_path.exists():
            st.image(str(image_path), width=80)
        else:
            st.write("📦")

    with info_col:
        st.markdown(f"**{product['name']}**")
        st.caption(f"JAN: {product['jan']} | 容量: {product['volume']} | ケース入数: {product['case_qty']}")
        st.caption(f"想定小売: ¥{product['retail_price']} | 賞味期限: D{product['shelf_life']}")

    st.write("**ロット別価格設定:**")

    for i, lot in enumerate(WATER_LOT_PATTERNS):
        key_prefix = f"water_{i}"
        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            selected = st.checkbox(
                lot['lot'],
                key=f"{key_prefix}_check"
            )
        with col2:
            price = st.number_input(
                "卸価格",
                value=lot['default_price'],
                min_value=0,
                key=f"{key_prefix}_price",
                label_visibility="collapsed"
            )
        with col3:
            special = st.text_input(
                "特別条件",
                placeholder="例：5",
                key=f"{key_prefix}_special",
                label_visibility="collapsed"
            )

        # セッション状態を更新
        st.session_state.water_selections[i] = {
            'selected': selected,
            'lot': lot['lot'],
            'product': product,
            'wholesale_price': price,
            'special_condition': special
        }

    st.markdown("---")


def collect_selected_products():
    """選択された商品を収集"""

    selected = []

    # 通常商品
    for idx, data in st.session_state.selected_products.items():
        if data.get('selected'):
            product = data['product'].copy()
            product['wholesale_price'] = data['wholesale_price']
            product['special_condition'] = data.get('special_condition', '')
            selected.append(product)

    # 2Water
    for i, data in st.session_state.water_selections.items():
        if data.get('selected'):
            product = data['product'].copy()
            product['order_lot'] = data['lot']
            product['wholesale_price'] = data['wholesale_price']
            product['special_condition'] = data.get('special_condition', '')
            selected.append(product)

    return selected


def show_quote_history():
    """見積履歴ページ"""

    st.markdown('<h1 class="main-header">見積履歴</h1>', unsafe_allow_html=True)

    # フィルター
    col1, col2, col3 = st.columns(3)

    with col1:
        search_keyword = st.text_input("検索（送付先・対象小売）", placeholder="キーワード入力")
    with col2:
        filter_staff = st.selectbox("担当者フィルター", ["すべて"] + STAFF_LIST)
    with col3:
        date_range = st.date_input(
            "日付範囲",
            value=[],
            key="date_filter"
        )

    # データ取得
    start_date = None
    end_date = None
    if date_range and len(date_range) == 2:
        start_date = str(date_range[0])
        end_date = str(date_range[1])

    staff_filter = filter_staff if filter_staff != "すべて" else None
    keyword_filter = search_keyword if search_keyword else None

    quotes = search_quotes(
        keyword=keyword_filter,
        start_date=start_date,
        end_date=end_date,
        staff=staff_filter
    )

    # 履歴表示
    st.write(f"**検索結果**: {len(quotes)}件")

    if not quotes:
        st.info("履歴がありません")
        return

    # テーブル形式で表示
    for quote in quotes:
        with st.expander(
            f"📄 {quote['quote_date']} | {quote['recipient']} | {quote.get('retailer', '-')} | {quote['staff']}",
            expanded=False
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**送付先**: {quote['recipient']}")
                st.write(f"**対象小売**: {quote.get('retailer', '-')}")
                st.write(f"**担当者**: {quote['staff']}")
                st.write(f"**販売エリア**: {quote['sales_area']}")
                st.write(f"**作成日時**: {quote['created_at']}")

                # 商品一覧
                st.write("**商品:**")
                products = quote.get('products', [])
                if products:
                    for p in products:
                        st.caption(f"・{p['name']} - {p['wholesale_price']}円")

            with col2:
                # 再ダウンロードボタン
                if st.button("📥 PDF再生成", key=f"dl_{quote['id']}"):
                    try:
                        pdf_data = generate_pdf(
                            recipient=quote['recipient'],
                            retailer=quote.get('retailer', ''),
                            show_retailer=bool(quote.get('retailer')),
                            staff=quote['staff'],
                            quote_date=quote['quote_date'],
                            sales_area=quote['sales_area'],
                            products=quote['products'],
                            notes=quote.get('notes', '')
                        )
                        st.download_button(
                            label="⬇️ ダウンロード",
                            data=pdf_data,
                            file_name=get_pdf_filename(quote['recipient'], quote['quote_date']),
                            mime="application/pdf",
                            key=f"pdf_{quote['id']}"
                        )
                    except Exception as e:
                        st.error(f"エラー: {str(e)}")

                # 削除ボタン
                if st.button("🗑️ 削除", key=f"del_{quote['id']}"):
                    delete_quote(quote['id'])
                    st.success("削除しました")
                    st.rerun()


def show_product_master():
    """商品マスターページ"""

    st.markdown('<h1 class="main-header">商品マスター</h1>', unsafe_allow_html=True)

    st.write(f"**登録商品数**: {len(PRODUCTS)}件")

    # 商品データをDataFrame用に整形
    product_data = []
    for p in PRODUCTS:
        product_data.append({
            "商品名": p['name'],
            "ブランド": p.get('brand', '-'),
            "カテゴリ": p.get('category', '-'),
            "JANコード": p['jan'],
            "ITFコード": p['itf'],
            "ケースJAN": p.get('case_jan', '-'),
            "容量": p['volume'],
            "ケース入数": p['case_qty'],
            "想定小売価格": f"¥{p['retail_price']}",
            "標準卸価格": f"¥{p['wholesale_price']}",
            "賞味期限": f"D{p['shelf_life']}",
            "温度帯": p['temperature'],
            "発注ロット": p.get('order_lot', '-'),
        })

    df = pd.DataFrame(product_data)

    # テーブル表示
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        height=500
    )

    st.divider()

    # 商品カード形式での詳細表示
    st.subheader("📦 商品詳細")

    for product in PRODUCTS:
        with st.expander(f"**{product['name']}**", expanded=False):
            col1, col2 = st.columns([1, 3])

            with col1:
                # 商品画像
                image_path = IMAGE_FOLDER / product.get('image', '')
                if image_path.exists():
                    st.image(str(image_path), width=120)
                else:
                    st.write("📦 画像なし")

            with col2:
                st.write(f"**ブランド**: {product.get('brand', '-')}")
                st.write(f"**カテゴリ**: {product.get('category', '-')}")
                st.write(f"**販売者**: {product.get('seller', '-')}")
                st.divider()
                st.write(f"**JANコード**: {product['jan']}")
                st.write(f"**ITFコード**: {product['itf']}")
                st.write(f"**ケースJAN**: {product.get('case_jan', '-')}")
                st.divider()
                st.write(f"**容量**: {product['volume']}")
                st.write(f"**ケース入数**: {product['case_qty']}")
                st.write(f"**発注ロット**: {product.get('order_lot', '-')}")
                st.divider()
                st.write(f"**想定小売価格**: ¥{product['retail_price']}")
                st.write(f"**標準卸価格**: ¥{product['wholesale_price']}")
                st.write(f"**賞味期限**: D{product['shelf_life']}")
                st.write(f"**温度帯**: {product['temperature']}")


if __name__ == "__main__":
    main()
