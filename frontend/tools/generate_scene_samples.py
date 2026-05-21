from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random


ROOT = Path("/Users/medusa/Desktop/snap Extract")
OUT = ROOT / "demo_sample_files_public" / "chinese_samples"


def register_fonts():
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="STSong-Light", fontSize=18, leading=24, spaceAfter=8
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading2"], fontName="STSong-Light", fontSize=13, leading=19, spaceBefore=8, spaceAfter=6
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName="STSong-Light", fontSize=10.5, leading=16, spaceAfter=4
        ),
        "meta": ParagraphStyle(
            "meta", parent=base["BodyText"], fontName="STSong-Light", fontSize=9.5, leading=14, textColor=colors.HexColor("#4b5563")
        ),
    }


def build_contract_pdf(path: Path, title: str, meta_rows, sections):
    s = styles()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    story = [Paragraph(title, s["title"]), Spacer(1, 4)]
    meta = Table(meta_rows, colWidths=[32 * mm, 120 * mm])
    meta.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("LEADING", (0, 0), (-1, -1), 14),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#374151")),
                ("LINEBELOW", (0, -1), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 10))
    for sec_title, paragraphs in sections:
        story.append(Paragraph(sec_title, s["h1"]))
        for p in paragraphs:
            story.append(Paragraph(p, s["body"]))
        story.append(Spacer(1, 4))
    doc.build(story)


def generate_contracts():
    draft_meta = [
        ["合同名称", "深港科技创新合作区 BIM 平台建设服务合同（初稿）"],
        ["甲方", "深圳市福田区机关事务管理局"],
        ["乙方", "深圳飞渡致成科技有限公司"],
        ["项目标的", "BIM 平台建设、试运行与售后服务"],
        ["总金额", "人民币 197,800 元"],
    ]
    draft_sections = [
        ("一、付款条款", [
            "1. 合同总金额为人民币 197,800 元，分三期支付：首期 30%，二期 60%，末期 10%。",
            "2. 甲方在合同签订后 5 个工作日内支付首期款；二期款在初验通过后支付；末期款在终验完成后支付。",
        ]),
        ("二、建设与交付", [
            "1. 乙方应在合同签订后 30 天内完成 BIM 平台建设交付，并配合甲方完成试运行。",
            "2. 乙方提交阶段成果、部署说明及测试记录后，甲方可组织初验。",
        ]),
        ("三、验收条款", [
            "1. 甲方在收到成果申请后 5 个工作日内完成初验。",
            "2. 平台试运行满 1 个月后，甲方在 5 个工作日内完成终验确认。",
        ]),
        ("四、违约责任与售后", [
            "1. 任一方违约，应按实际损失承担赔偿责任。",
            "2. 保修期为 6 个月；售后服务要求 7×24 小时响应，一般情况 48 小时内到场。",
        ]),
    ]
    build_contract_pdf(OUT / "contract_scene_main_v2.pdf", "深港科技创新合作区 BIM 平台建设服务合同", draft_meta, draft_sections)

    mod_meta = [
        ["文件名称", "深港科技创新合作区 BIM 平台建设服务合同（修改版）"],
        ["修改来源", "甲方 / 乙方综合修订版"],
        ["甲方", "深圳市福田区机关事务管理局"],
        ["乙方", "深圳飞渡致成科技有限公司"],
        ["用途", "用于条款差异对比与签署前评审"],
    ]
    mod_sections = [
        ("一、付款条款修改", [
            "【甲方修改】首期付款改为在初验通过后 5 个工作日内支付，不再沿用“签约后支付”口径。",
            "【乙方意见】乙方保留签约后支付首期款的诉求，认为完全后移至验收后将显著增加项目启动现金流压力。",
        ]),
        ("二、建设周期修改", [
            "【乙方修改】建设周期调整为 45 天，并补充“甲方接口、账号、环境延迟提供的，工期相应顺延”。",
            "【甲方意见】甲方版本暂未接受建设周期延长，要求维持 30 天主交付周期。",
        ]),
        ("三、验收默认规则修改", [
            "【甲方修改】未书面确认前不得视为验收通过。",
            "【乙方修改】逾期未反馈视为默认通过，以避免项目长期悬置。",
        ]),
        ("四、违约责任与售后修改", [
            "【乙方修改】新增“乙方赔偿责任上限不超过合同总额 10%”条款。",
            "【甲方修改】重大故障需在 24 小时内到场，并提供临时替代方案；重大损失仍主张按实际损失承担。",
        ]),
    ]
    build_contract_pdf(OUT / "contract_scene_modified_v2.pdf", "深港科技创新合作区 BIM 平台建设服务合同（修改版）", mod_meta, mod_sections)


def fit_font(text, candidates, size):
    for p in candidates:
        try:
            return ImageFont.truetype(str(p), size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_receipt_image():
    width, height = 1800, 1200
    img = Image.new("RGB", (width, height), "#efe5d0")
    draw = ImageDraw.Draw(img)
    random.seed(7)
    for _ in range(240):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(1, 3)
        c = random.randint(220, 245)
        draw.ellipse((x, y, x + r, y + r), fill=(c, c - 5, c - 12))

    paper = Image.new("RGBA", (1220, 780), (247, 242, 231, 255))
    pdraw = ImageDraw.Draw(paper)
    pdraw.rounded_rectangle((0, 0, 1219, 779), radius=16, outline=(190, 176, 150), width=3, fill=(249, 244, 235))

    font_paths = [
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8/88d6cc32a907955efa1d014207889413890573be.asset/AssetData/Kaiti.ttc"),
        Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc"),
        Path("/System/Library/Fonts/Supplemental/NotoSansKaithi-Regular.ttf"),
    ]
    title_font = fit_font("深圳", font_paths, 46)
    body_font = fit_font("深圳", font_paths, 34)
    small_font = fit_font("深圳", font_paths, 26)

    lines = [
        ("商务出行手写单据", title_font, (90, 70)),
        ("单据编号：SZ-2025-0131", small_font, (92, 145)),
        ("日期：2025-01-09", body_font, (92, 215)),
        ("出发地：深圳湾科技生态园", body_font, (92, 290)),
        ("目的地：福田高铁站", body_font, (92, 360)),
        ("事由：客户会后返程", body_font, (92, 430)),
        ("金额：人民币肆拾捌元柒角伍分  ¥48.75", body_font, (92, 500)),
        ("支付方式：微信支付", body_font, (92, 570)),
        ("商户：深港出行", body_font, (92, 640)),
        ("经办人：王敏", body_font, (760, 640)),
    ]
    ink = (48, 52, 61)
    for text, font, pos in lines:
        jitter = (random.randint(-2, 2), random.randint(-2, 2))
        pdraw.text((pos[0] + jitter[0], pos[1] + jitter[1]), text, fill=ink, font=font)

    pdraw.line((86, 190, 1130, 190), fill=(170, 155, 130), width=2)
    pdraw.line((86, 705, 1130, 705), fill=(170, 155, 130), width=2)
    pdraw.text((86, 724), "备注：用于市内商务出行报销，需与 2025-01-09 对账单流水核验。", fill=(92, 96, 107), font=small_font)

    paper = paper.rotate(-3.2, expand=True, resample=Image.Resampling.BICUBIC)
    img.paste(paper, (260, 165), paper)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
    OUT.joinpath("statement_scene_receipt_v2.jpg").parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT / "statement_scene_receipt_v2.jpg", quality=92)


def generate_bank_statement():
    s = styles()
    path = OUT / "statement_scene_bank_v2.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm, bottomMargin=14 * mm)
    story = [
        Paragraph("中国建设银行企业账户交易明细", s["title"]),
        Paragraph("账户名称：深圳飞渡致成科技有限公司　账户尾号：6222 **** 1038　账期：2025-01-01 至 2025-01-31", s["meta"]),
        Spacer(1, 8),
    ]
    data = [
        ["交易日期", "交易摘要", "借方(支出)", "贷方(收入)", "余额"],
        ["2025-01-03", "工资入账", "", "120,000.00", "286,520.60"],
        ["2025-01-07", "云服务器续费", "2,480.00", "", "284,040.60"],
        ["2025-01-09", "深港出行服务 / 商务打车", "48.75", "", "283,991.85"],
        ["2025-01-11", "供应商转账", "", "25,600.00", "309,591.85"],
        ["2025-01-15", "会议室租赁", "1,280.00", "", "308,311.85"],
        ["2025-01-18", "房租代扣", "6,120.00", "", "302,191.85"],
        ["2025-01-22", "广告投放", "4,800.00", "", "297,391.85"],
        ["2025-01-24", "ATM 取现", "2,000.00", "", "295,391.85"],
        ["2025-01-28", "报销款退回", "", "860.00", "296,251.85"],
    ]
    table = Table(data, colWidths=[25 * mm, 78 * mm, 28 * mm, 28 * mm, 28 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "STSong-Light"),
                ("FONTNAME", (0, 1), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.2),
                ("LEADING", (0, 0), (-1, -1), 13),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5eef9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("关键核对线索：2025-01-09 / 深港出行服务 / 48.75 元，与手写单据的日期、商户和金额一致。", s["body"]))
    story.append(Paragraph("说明：本样例为演示用途生成的企业流水，专门用于“手写单据 + 银行流水核验”场景。", s["meta"]))
    doc.build(story)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    register_fonts()
    generate_contracts()
    generate_receipt_image()
    generate_bank_statement()
    print("generated:")
    for p in [
        OUT / "contract_scene_main_v2.pdf",
        OUT / "contract_scene_modified_v2.pdf",
        OUT / "statement_scene_receipt_v2.jpg",
        OUT / "statement_scene_bank_v2.pdf",
    ]:
        print(p)


if __name__ == "__main__":
    main()
