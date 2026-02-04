# PDF生成モジュール

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Indenter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from pathlib import Path
from PIL import Image as PILImage

# 画像フォルダのパス（Streamlit Cloud対応）
IMAGE_FOLDER = Path(__file__).parent / "images"

# フォント設定
FONT_NAME = "HeiseiKakuGo-W5"
FONT_REGISTERED = False

def register_font():
    """日本語フォントを登録"""
    global FONT_REGISTERED, FONT_NAME
    if FONT_REGISTERED:
        return

    # まずCIDフォント（組み込み日本語フォント）を試す
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        FONT_NAME = "HeiseiKakuGo-W5"
        FONT_REGISTERED = True
        return
    except Exception:
        pass

    # 次にシステムフォントを試す
    BASE_DIR = Path(__file__).parent
    FONT_PATHS = [
        Path("C:/Windows/Fonts/msgothic.ttc"),  # Windows
        Path("C:/Windows/Fonts/meiryo.ttc"),
    ]

    for font_path in FONT_PATHS:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("JapaneseFont", str(font_path)))
                FONT_NAME = "JapaneseFont"
                FONT_REGISTERED = True
                return
            except Exception:
                continue

    # フォントが見つからない場合はデフォルトを使用
    FONT_NAME = "Helvetica"
    FONT_REGISTERED = True


def get_product_image(image_filename, max_width=10*mm, max_height=10*mm):
    """商品画像を取得（縦横比を維持、存在しない場合は空文字を返す）"""
    if not image_filename:
        return ""

    image_path = IMAGE_FOLDER / image_filename
    if image_path.exists():
        try:
            # Pillowで元画像のサイズを取得
            with PILImage.open(str(image_path)) as img:
                orig_width, orig_height = img.size

            # 縦横比を維持しながら、max_width/max_height内に収める
            ratio = min(max_width / orig_width, max_height / orig_height)
            new_width = orig_width * ratio
            new_height = orig_height * ratio

            return Image(str(image_path), width=new_width, height=new_height)
        except Exception:
            return ""
    return ""


def get_logo_image(max_width=50*mm, max_height=15*mm):
    """ロゴ画像を取得（縦横比を維持）"""
    logo_path = IMAGE_FOLDER / "2foods_logo.png"
    if logo_path.exists():
        try:
            with PILImage.open(str(logo_path)) as img:
                orig_width, orig_height = img.size

            ratio = min(max_width / orig_width, max_height / orig_height)
            new_width = orig_width * ratio
            new_height = orig_height * ratio

            return Image(str(logo_path), width=new_width, height=new_height)
        except Exception:
            return None
    return None


def generate_pdf(recipient, retailer, show_retailer, staff, quote_date, sales_area, products, notes):
    """見積書PDFを生成"""
    register_font()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=2*mm,
        rightMargin=2*mm,
        topMargin=5*mm,
        bottomMargin=5*mm
    )

    elements = []

    # スタイル設定
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=14,
        leading=18,
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        leftIndent=4*mm,  # 表のNo列と揃える
    )
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
    )

    # ヘッダー情報
    formatted_date = quote_date.replace("-", "/")
    retailer_text = f"{retailer}様" if show_retailer and retailer else ""

    # ロゴ画像を取得（縦横比維持）
    logo = get_logo_image(max_width=50*mm, max_height=15*mm)
    if logo is None:
        logo = Paragraph("<b>2foods</b>", title_style)

    # 右寄せスタイル
    right_style = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        alignment=2,  # 右寄せ
    )

    header_data = [
        [
            logo,
            "",
            Paragraph(f"株式会社TWO<br/>担当：StrategicPlanning&amp;Sales　{staff}<br/>連絡先：2foods-sales@two2.jp", right_style)
        ],
        [
            "",
            "",
            ""
        ],
        [
            Paragraph(f"送付先：{recipient}様<br/>対象小売企業名：{retailer_text}", normal_style),
            "",
            Paragraph(f"電話番号：03-6869-0010<br/>FAX番号：03-4496-4769<br/>日付：{formatted_date}", right_style)
        ]
    ]

    header_table = Table(header_data, colWidths=[120*mm, 40*mm, 110*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('VALIGN', (2, 0), (2, 1), 'BOTTOM'),  # 会社情報は下揃え
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('SPAN', (0, 0), (0, 1)),  # ロゴを1-2行目にまたがらせる
        ('SPAN', (2, 0), (2, 1)),  # 会社情報を1-2行目にまたがらせる
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 5*mm))

    # 商品テーブル
    # 特別条件があるかチェック
    has_special = any(p.get('special_condition') for p in products)

    # セル内で改行可能なスタイル
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=7,
        leading=8,
        alignment=1,  # 中央揃え
    )

    # ヘッダー用スタイル（白文字・中央揃え）
    header_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=7,
        leading=8,
        alignment=1,  # 中央揃え
        textColor=colors.white,
    )

    # ヘッダー行（改行対応）
    # A4横: 297mm、左右マージン2mm×2 = 使用可能幅 293mm
    if has_special:
        table_headers = [
            'No', '画像', '温度帯', '販売者', '商品名', 'JANコード', 'ITFコード', 'ケースJAN',
            '容量', Paragraph('ケース<br/>入数', header_style), Paragraph('想定<br/>小売価格', header_style),
            '卸価格', Paragraph('特別<br/>条件', header_style), Paragraph('販売<br/>エリア', header_style),
            Paragraph('発注<br/>ロット', header_style), Paragraph('賞味<br/>期限', header_style)
        ]
        # 合計: 293mm（16列）- 商品名・容量を拡大
        col_widths = [6*mm, 12*mm, 10*mm, 10*mm, 44*mm, 23*mm, 25*mm, 23*mm,
                     12*mm, 12*mm, 16*mm, 12*mm, 11*mm, 12*mm, 24*mm, 11*mm]
    else:
        table_headers = [
            'No', '画像', '温度帯', '販売者', '商品名', 'JANコード', 'ITFコード', 'ケースJAN',
            '容量', Paragraph('ケース<br/>入数', header_style), Paragraph('想定<br/>小売価格', header_style),
            '卸価格', Paragraph('販売<br/>エリア', header_style), Paragraph('発注<br/>ロット', header_style),
            Paragraph('賞味<br/>期限', header_style)
        ]
        # 合計: 293mm（15列）- 商品名・容量を拡大
        col_widths = [6*mm, 12*mm, 10*mm, 10*mm, 52*mm, 24*mm, 26*mm, 24*mm,
                     13*mm, 13*mm, 17*mm, 13*mm, 13*mm, 26*mm, 12*mm]

    table_data = [table_headers]

    # 商品データ行
    for i, p in enumerate(products):
        special = p.get('special_condition', '')
        # 数値のみの場合は「円」を付ける
        if special and str(special).isdigit():
            special = f"¥{special}"

        # 商品画像を取得
        product_image = get_product_image(p.get('image', ''), max_width=10*mm, max_height=10*mm)

        # 発注ロットは改行対応
        order_lot = p.get('order_lot', '')
        # 改行ルール: 「（」の前、「以上」の前で改行
        order_lot_formatted = order_lot.replace('（', '<br/>（').replace('以上', '<br/>以上')
        order_lot_para = Paragraph(order_lot_formatted, cell_style)

        if has_special:
            row = [
                str(i + 1),
                product_image,
                p.get('temperature', ''),
                p.get('seller', 'TWO'),
                p.get('name', ''),
                p.get('jan', ''),
                p.get('itf', ''),
                p.get('case_jan', ''),
                p.get('volume', ''),
                p.get('case_qty', ''),
                f"¥{p.get('retail_price', '')}",
                f"¥{p.get('wholesale_price', '')}",
                special,
                sales_area,
                order_lot_para,
                f"D{p.get('shelf_life', '')}"
            ]
        else:
            row = [
                str(i + 1),
                product_image,
                p.get('temperature', ''),
                p.get('seller', 'TWO'),
                p.get('name', ''),
                p.get('jan', ''),
                p.get('itf', ''),
                p.get('case_jan', ''),
                p.get('volume', ''),
                p.get('case_qty', ''),
                f"¥{p.get('retail_price', '')}",
                f"¥{p.get('wholesale_price', '')}",
                sales_area,
                order_lot_para,
                f"D{p.get('shelf_life', '')}"
            ]
        table_data.append(row)

    # 空行を追加して最低6行にする
    while len(table_data) < 7:  # ヘッダー + 6行
        empty_row = [''] * len(table_headers)
        table_data.append(empty_row)

    product_table = Table(table_data, colWidths=col_widths, rowHeights=[None] + [14*mm] * (len(table_data) - 1))
    product_table.setStyle(TableStyle([
        # ヘッダースタイル
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d4a700')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # 枠線
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        # 交互の背景色
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    elements.append(product_table)

    # 備考欄
    if notes:
        elements.append(Spacer(1, 5*mm))
        # 備考用スタイル
        notes_style = ParagraphStyle(
            'Notes',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=9,
            leading=12,
        )
        notes_text = "<b>▼備考</b><br/>" + notes.replace("\n", "<br/>")
        # Indenterで左側にスペースを追加（表のNo列と揃える）
        elements.append(Indenter(left=12*mm))
        elements.append(Paragraph(notes_text, notes_style))
        elements.append(Indenter(left=-12*mm))  # 元に戻す

    # PDF生成
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def get_pdf_filename(recipient, quote_date):
    """PDFファイル名を生成"""
    # YYMMDD形式
    date_parts = quote_date.split('-')
    yymmdd = date_parts[0][2:] + date_parts[1] + date_parts[2]
    return f"{yymmdd}_{recipient}様_お見積書.pdf"
