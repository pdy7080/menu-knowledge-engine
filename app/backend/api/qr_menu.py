"""
QR Menu API Routes - Sprint 3 P2-1
Dynamic multi-language menu page generation
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from database import get_db
from models import Shop, MenuVariant, CanonicalMenu
import uuid

router = APIRouter(prefix="/qr", tags=["qr"])


# ===========================
# QR Menu Page
# ===========================
@router.get("/{shop_code}", response_class=HTMLResponse)
async def get_qr_menu_page(
    shop_code: str,
    lang: str = "en",  # en, ja, zh
    db: AsyncSession = Depends(get_db)
):
    """
    QR 메뉴 페이지 생성 (P2-1)

    동적으로 생성되는 다국어 메뉴 페이지

    Args:
        shop_code: 식당 코드 (QR 코드에 인코딩됨)
        lang: 표시 언어 (en, ja, zh)

    Returns:
        HTML 페이지
    """
    # Get shop info
    shop_result = await db.execute(
        select(Shop).where(Shop.shop_code == shop_code)
    )
    shop = shop_result.scalars().first()

    if not shop:
        raise HTTPException(status_code=404, detail=f"Shop not found: {shop_code}")

    # Get menu variants for this shop
    variants_result = await db.execute(
        select(MenuVariant)
        .where(MenuVariant.shop_id == shop.id)
        .where(MenuVariant.is_active == True)
        .order_by(MenuVariant.display_order)
    )
    variants = variants_result.scalars().all()

    # Get canonical menus
    menu_data = []
    for variant in variants:
        if variant.canonical_menu_id:
            canonical_result = await db.execute(
                select(CanonicalMenu).where(CanonicalMenu.id == variant.canonical_menu_id)
            )
            canonical = canonical_result.scalars().first()

            if canonical:
                # Get localized description
                description = ""
                if canonical.explanation_short:
                    if isinstance(canonical.explanation_short, dict):
                        description = canonical.explanation_short.get(lang, canonical.explanation_short.get("en", ""))
                    else:
                        description = canonical.explanation_short

                menu_data.append({
                    "name_ko": variant.menu_name_ko or canonical.name_ko,
                    "name_en": canonical.name_en,
                    "description": description,
                    "price": variant.price_display,
                    "spice_level": canonical.spice_level,
                    "allergens": canonical.allergens or [],
                    "image_url": canonical.image_url,
                })

    # Generate HTML
    html = generate_qr_menu_html(
        shop_name=shop.name_ko,
        shop_code=shop_code,
        menus=menu_data,
        current_lang=lang
    )

    return html


def generate_qr_menu_html(
    shop_name: str,
    shop_code: str,
    menus: list,
    current_lang: str = "en"
) -> str:
    """
    QR 메뉴 HTML 생성

    Args:
        shop_name: 식당 이름
        shop_code: 식당 코드
        menus: 메뉴 리스트
        current_lang: 현재 언어

    Returns:
        HTML 문자열
    """
    # Language labels
    lang_labels = {
        "en": {"title": "Menu", "spice": "Spice Level", "allergens": "Allergens"},
        "ja": {"title": "メニュー", "spice": "辛さ", "allergens": "アレルゲン"},
        "zh": {"title": "菜单", "spice": "辣度", "allergens": "过敏原"}
    }

    labels = lang_labels.get(current_lang, lang_labels["en"])

    # Build menu items HTML
    menu_items_html = ""
    for menu in menus:
        spice_emoji = "🌶️" * (menu["spice_level"] or 0) if menu["spice_level"] else "-"
        allergens_text = ", ".join(menu["allergens"]) if menu["allergens"] else "None"

        menu_items_html += f"""
        <div class="menu-item">
            <div class="menu-header">
                <div class="menu-names">
                    <h3 class="menu-name-ko">{menu["name_ko"]}</h3>
                    <p class="menu-name-en">{menu["name_en"]}</p>
                </div>
                {f'<div class="menu-price">{menu["price"]}</div>' if menu["price"] else ''}
            </div>
            <p class="menu-description">{menu["description"]}</p>
            <div class="menu-info">
                <div class="info-item">
                    <span class="info-label">{labels["spice"]}:</span>
                    <span>{spice_emoji}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">{labels["allergens"]}:</span>
                    <span>{allergens_text}</span>
                </div>
            </div>
        </div>
        """

    # Generate full HTML
    html = f"""
<!DOCTYPE html>
<html lang="{current_lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{shop_name} - {labels["title"]}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Sans KR', -apple-system, sans-serif;
            background: #FFF8F0;
            color: #1A1A1A;
            line-height: 1.6;
            padding: 1rem;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: #E85D3A;
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        .shop-name {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        .lang-switcher {{
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
        }}

        .lang-btn {{
            padding: 0.5rem 1rem;
            border: 2px solid white;
            background: transparent;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s;
        }}

        .lang-btn.active {{
            background: white;
            color: #E85D3A;
        }}

        .lang-btn:hover {{
            background: rgba(255,255,255,0.2);
        }}

        .menu-list {{
            padding: 2rem;
        }}

        .menu-item {{
            padding: 1.5rem;
            border-bottom: 2px solid #E0E0E0;
        }}

        .menu-item:last-child {{
            border-bottom: none;
        }}

        .menu-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}

        .menu-names {{
            flex: 1;
        }}

        .menu-name-ko {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #1A1A1A;
            margin-bottom: 0.25rem;
        }}

        .menu-name-en {{
            font-size: 1rem;
            color: #666;
        }}

        .menu-price {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #E85D3A;
            white-space: nowrap;
            margin-left: 1rem;
        }}

        .menu-description {{
            color: #444;
            margin-bottom: 0.75rem;
            line-height: 1.5;
        }}

        .menu-info {{
            display: flex;
            gap: 1.5rem;
            font-size: 0.9rem;
        }}

        .info-item {{
            display: flex;
            gap: 0.5rem;
        }}

        .info-label {{
            font-weight: 600;
            color: #666;
        }}

        .footer {{
            background: #F5F5F5;
            padding: 1.5rem;
            text-align: center;
            font-size: 0.85rem;
            color: #888;
        }}

        @media (max-width: 600px) {{
            .menu-header {{
                flex-direction: column;
            }}

            .menu-price {{
                margin-left: 0;
                margin-top: 0.5rem;
            }}

            .menu-info {{
                flex-direction: column;
                gap: 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="shop-name">{shop_name}</h1>
            <p>{labels["title"]}</p>
            <div class="lang-switcher">
                <a href="/qr/{shop_code}?lang=en" class="lang-btn {'active' if current_lang == 'en' else ''}">English</a>
                <a href="/qr/{shop_code}?lang=ja" class="lang-btn {'active' if current_lang == 'ja' else ''}">日本語</a>
                <a href="/qr/{shop_code}?lang=zh" class="lang-btn {'active' if current_lang == 'zh' else ''}">中文</a>
            </div>
        </div>

        <div class="menu-list">
            {menu_items_html}
        </div>

        <div class="footer">
            Powered by Menu Knowledge Engine
        </div>
    </div>
</body>
</html>
    """

    return html
