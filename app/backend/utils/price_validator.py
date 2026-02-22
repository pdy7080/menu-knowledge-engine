"""
Price validation utilities for menu data

Rules:
- 500원 단위 (0, 500, 1000, 1500, ...)
- 2000원 ~ 50000원 범위
- 할인가 < 원가
- 다중 가격 배열 (최대 5개 아이템)
"""

import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class PriceValidator:
    """가격 데이터 유효성 검증"""

    PRICE_STEP = 500  # 500원 단위
    MIN_PRICE = 2000
    MAX_PRICE = 50000
    MAX_PRICE_ITEMS = 5  # 다중 가격 배열 최대 개수

    @staticmethod
    def validate_price(price: Optional[int]) -> Tuple[bool, Optional[str]]:
        """
        단일 가격 검증

        Args:
            price: 검증할 가격

        Returns:
            (is_valid, error_message)
        """
        if price is None:
            return True, None  # None은 유효 (선택사항)

        if not isinstance(price, int):
            return False, f"가격이 정수가 아님: {type(price).__name__}"

        if price % PriceValidator.PRICE_STEP != 0:
            return False, f"가격이 {PriceValidator.PRICE_STEP}원 단위가 아님: {price}원"

        if price < PriceValidator.MIN_PRICE or price > PriceValidator.MAX_PRICE:
            return False, (
                f"가격 범위 초과: {price}원 "
                f"({PriceValidator.MIN_PRICE}~{PriceValidator.MAX_PRICE})"
            )

        return True, None

    @staticmethod
    def validate_prices_array(prices: Optional[List[dict]]) -> Tuple[bool, List[str]]:
        """
        다중 가격 배열 검증

        Args:
            prices: 다중 가격 배열
            # 예: [
            #   {"size": "소", "price": 8000},
            #   {"size": "중", "price": 10000},
            #   {"size": "대", "price": 12000}
            # ]

        Returns:
            (is_valid, error_list)
        """
        errors = []

        if prices is None:
            return True, []

        if not isinstance(prices, list):
            errors.append(f"가격 배열이 list가 아님: {type(prices).__name__}")
            return False, errors

        if not prices:
            return True, []  # 빈 배열은 유효

        if len(prices) > PriceValidator.MAX_PRICE_ITEMS:
            errors.append(
                f"가격 아이템이 너무 많음: {len(prices)}개 (최대 {PriceValidator.MAX_PRICE_ITEMS}개)"
            )

        for i, price_item in enumerate(prices):
            if not isinstance(price_item, dict):
                errors.append(
                    f"가격 아이템 {i}이 dict가 아님: {type(price_item).__name__}"
                )
                continue

            # 필수 필드: price
            price = price_item.get("price")
            is_valid, error = PriceValidator.validate_price(price)
            if not is_valid:
                errors.append(f"가격 아이템 {i}: {error}")

            # 선택 필드: size, label 등 (검증 생략)

        return len(errors) == 0, errors

    @staticmethod
    def validate_discount(
        original_price: Optional[int],
        discount_price: Optional[int],
    ) -> Tuple[bool, Optional[str]]:
        """
        할인 가격 검증

        Args:
            original_price: 원가 (할인 전)
            discount_price: 할인가

        Returns:
            (is_valid, error_message)
        """
        if original_price is None or discount_price is None:
            return True, None  # 둘 다 None이면 할인 없음

        # 할인가 < 원가 검증
        if discount_price >= original_price:
            return False, (
                f"할인가가 원가 이상: {discount_price}원 >= {original_price}원"
            )

        # 원가 검증
        is_valid, error = PriceValidator.validate_price(original_price)
        if not is_valid:
            return False, f"원가 검증 실패: {error}"

        # 할인가 검증
        is_valid, error = PriceValidator.validate_price(discount_price)
        if not is_valid:
            return False, f"할인가 검증 실패: {error}"

        return True, None

    @staticmethod
    def validate_menu_item_prices(
        price: Optional[int] = None,
        prices: Optional[List[dict]] = None,
        original_price: Optional[int] = None,
        discount_price: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """
        메뉴 아이템의 모든 가격 필드 검증

        규칙:
        - price 또는 prices 중 하나는 있어야 함 (둘 다 가능)
        - discount_price가 있으면 original_price도 있어야 함
        - 할인가 < 원가

        Args:
            price: 단일 가격
            prices: 다중 가격 배열
            original_price: 원가
            discount_price: 할인가

        Returns:
            (is_valid, error_list)
        """
        errors = []

        # 최소 하나의 가격 필드 필요
        if price is None and not prices:
            errors.append("가격이 없음 (price 또는 prices 중 하나 필요)")
            return False, errors

        # 단일 가격 검증
        if price is not None:
            is_valid, error = PriceValidator.validate_price(price)
            if not is_valid:
                errors.append(f"단일 가격: {error}")

        # 다중 가격 배열 검증
        if prices:
            is_valid, price_errors = PriceValidator.validate_prices_array(prices)
            if not is_valid:
                errors.extend(price_errors)

        # 할인가 검증
        if discount_price is not None:
            if original_price is None:
                errors.append("할인가가 있으면 원가(original_price)도 필요")
            else:
                is_valid, error = PriceValidator.validate_discount(
                    original_price, discount_price
                )
                if not is_valid:
                    errors.append(error)

        return len(errors) == 0, errors

    @staticmethod
    def is_price_reasonable(
        price: int, category: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        가격이 카테고리 내에서 합리적인지 판단

        예: 찌개류는 보통 8000~12000원대

        Args:
            price: 검증할 가격
            category: 카테고리 (선택)

        Returns:
            (is_reasonable, note)
        """
        # 이 메서드는 향후 카테고리별 가격 범위 모델 추가 시 구현
        # 현재는 기본 유효성 검증만 수행
        is_valid, _ = PriceValidator.validate_price(price)
        return is_valid, None
