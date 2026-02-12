"""
Menu Upload Service - B2B 메뉴 일괄 업로드 처리
"""
import csv
import json
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException

from models.menu_upload import MenuUploadTask, MenuUploadDetail, UploadStatus, MenuItemStatus
from models.restaurant import Restaurant
from models.canonical_menu import CanonicalMenu
from utils.retry import async_retry
from openai import OpenAI
from config import settings


class MenuUploadService:
    """메뉴 일괄 업로드 처리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def process_upload(
        self,
        restaurant_id: uuid.UUID,
        file: UploadFile
    ) -> MenuUploadTask:
        """
        메뉴 파일 업로드 처리

        1. 파일 검증
        2. 파싱 (CSV 또는 JSON)
        3. 각 메뉴 처리 (번역, 저장)
        4. 결과 반환
        """
        # 1. Restaurant 존재 확인
        restaurant = await self._verify_restaurant(restaurant_id)

        # 2. Upload Task 생성
        upload_task = MenuUploadTask(
            restaurant_id=restaurant_id,
            file_name=file.filename,
            file_type=self._get_file_type(file.filename),
            status=UploadStatus.pending.value
        )
        self.db.add(upload_task)
        await self.db.commit()
        await self.db.refresh(upload_task)

        try:
            # 3. 파일 읽기
            content = await file.read()

            # 4. 파싱
            menus = await self._parse_file(content, upload_task.file_type)

            # 5. Upload Task 업데이트 (처리 시작)
            upload_task.status = UploadStatus.processing.value
            upload_task.started_at = datetime.utcnow()
            upload_task.total_menus = len(menus)
            await self.db.commit()

            # 6. 각 메뉴 처리
            await self._process_menus(upload_task, menus)

            # 7. Upload Task 완료
            upload_task.status = UploadStatus.completed.value
            upload_task.completed_at = datetime.utcnow()
            await self.db.commit()

            return upload_task

        except Exception as e:
            # 실패 처리
            upload_task.status = UploadStatus.failed.value
            upload_task.error_log = str(e)
            upload_task.completed_at = datetime.utcnow()
            await self.db.commit()
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def _verify_restaurant(self, restaurant_id: uuid.UUID) -> Restaurant:
        """Restaurant 존재 확인"""
        result = await self.db.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        restaurant = result.scalars().first()

        if not restaurant:
            raise HTTPException(status_code=404, detail=f"Restaurant {restaurant_id} not found")

        return restaurant

    def _get_file_type(self, filename: str) -> str:
        """파일 확장자로 타입 판별"""
        if filename.endswith('.csv'):
            return 'csv'
        elif filename.endswith('.json'):
            return 'json'
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or JSON")

    async def _parse_file(self, content: bytes, file_type: str) -> List[Dict[str, Any]]:
        """파일 파싱"""
        if file_type == 'csv':
            return await self._parse_csv(content)
        elif file_type == 'json':
            return await self._parse_json(content)
        else:
            raise ValueError(f"Unknown file type: {file_type}")

    async def _parse_csv(self, content: bytes) -> List[Dict[str, Any]]:
        """CSV 파싱"""
        try:
            # UTF-8 디코딩
            text = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text))

            menus = []
            for row_num, row in enumerate(reader, start=1):
                menu = {
                    'row_number': row_num,
                    'name_ko': row.get('name_ko', '').strip(),
                    'name_en': row.get('name_en', '').strip(),
                    'description_en': row.get('description_en', '').strip(),
                    'price': int(row.get('price', 0)) if row.get('price') else None
                }

                # 필수 필드 검증
                if not menu['name_ko']:
                    raise ValueError(f"Row {row_num}: name_ko is required")

                menus.append(menu)

            return menus

        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid CSV encoding. Use UTF-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")

    async def _parse_json(self, content: bytes) -> List[Dict[str, Any]]:
        """JSON 파싱"""
        try:
            data = json.loads(content)

            if not isinstance(data, dict) or 'menus' not in data:
                raise ValueError("JSON must have 'menus' array")

            menus = []
            for row_num, menu_data in enumerate(data['menus'], start=1):
                menu = {
                    'row_number': row_num,
                    'name_ko': menu_data.get('name_ko', '').strip(),
                    'name_en': menu_data.get('name_en', '').strip(),
                    'description_en': menu_data.get('description_en', '').strip(),
                    'price': menu_data.get('price')
                }

                # 필수 필드 검증
                if not menu['name_ko']:
                    raise ValueError(f"Menu {row_num}: name_ko is required")

                menus.append(menu)

            return menus

        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"JSON parsing error: {str(e)}")

    async def _process_menus(
        self,
        upload_task: MenuUploadTask,
        menus: List[Dict[str, Any]]
    ):
        """각 메뉴 처리"""
        for menu_data in menus:
            try:
                # 중복 체크
                is_duplicate = await self._check_duplicate(menu_data['name_ko'])

                if is_duplicate:
                    # 중복 메뉴 (건너뛰기)
                    detail = MenuUploadDetail(
                        upload_task_id=upload_task.id,
                        name_ko=menu_data['name_ko'],
                        name_en=menu_data.get('name_en'),
                        description_en=menu_data.get('description_en'),
                        price=menu_data.get('price'),
                        status=MenuItemStatus.skipped.value,
                        error_message="Duplicate menu",
                        row_number=menu_data.get('row_number')
                    )
                    self.db.add(detail)
                    upload_task.skipped += 1

                else:
                    # 새 메뉴 생성
                    created_menu_id = await self._create_menu(menu_data)

                    detail = MenuUploadDetail(
                        upload_task_id=upload_task.id,
                        name_ko=menu_data['name_ko'],
                        name_en=menu_data.get('name_en'),
                        description_en=menu_data.get('description_en'),
                        price=menu_data.get('price'),
                        status=MenuItemStatus.success.value,
                        created_menu_id=created_menu_id,
                        row_number=menu_data.get('row_number')
                    )
                    self.db.add(detail)
                    upload_task.successful += 1

            except Exception as e:
                # 실패한 메뉴
                detail = MenuUploadDetail(
                    upload_task_id=upload_task.id,
                    name_ko=menu_data['name_ko'],
                    name_en=menu_data.get('name_en'),
                    status=MenuItemStatus.failed.value,
                    error_message=str(e),
                    row_number=menu_data.get('row_number')
                )
                self.db.add(detail)
                upload_task.failed += 1

        await self.db.commit()

    async def _check_duplicate(self, name_ko: str) -> bool:
        """중복 메뉴 확인"""
        result = await self.db.execute(
            select(CanonicalMenu).where(CanonicalMenu.name_ko == name_ko)
        )
        existing = result.scalars().first()
        return existing is not None

    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def _create_menu(self, menu_data: Dict[str, Any]) -> uuid.UUID:
        """
        메뉴 생성 (자동 번역 포함)

        1. 기본 정보로 CanonicalMenu 생성
        2. GPT-4o로 자동 번역 (JA, ZH)
        3. DB 저장
        """
        # 1. 기본 메뉴 생성
        menu = CanonicalMenu(
            name_ko=menu_data['name_ko'],
            name_en=menu_data.get('name_en', menu_data['name_ko']),  # Default to Korean name if EN missing
            typical_price_min=menu_data.get('price'),
            typical_price_max=menu_data.get('price')
        )

        # 2. 자동 번역 (description_en이 있으면)
        if menu_data.get('description_en'):
            translations = await self._translate_menu(
                menu_data['name_ko'],
                menu_data['description_en']
            )

            menu.explanation_short = translations

        self.db.add(menu)
        await self.db.commit()
        await self.db.refresh(menu)

        return menu.id

    async def _translate_menu(
        self,
        name_ko: str,
        description_en: str
    ) -> Dict[str, str]:
        """
        GPT-4o로 자동 번역

        EN은 이미 있으므로 JA, ZH만 번역
        """
        prompt = f"""Translate this Korean menu item to Japanese and Chinese:

Menu: {name_ko}
English Description: {description_en}

Return ONLY a JSON object with this exact format:
{{
  "ja": "Japanese translation",
  "zh": "Chinese translation"
}}

Keep it concise (under 50 words each)."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in Korean food menus."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        # 응답 파싱
        content = response.choices[0].message.content.strip()

        # JSON 추출 (```json ... ``` 제거)
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]

        translations = json.loads(content.strip())

        # EN 추가
        translations['en'] = description_en

        return translations
