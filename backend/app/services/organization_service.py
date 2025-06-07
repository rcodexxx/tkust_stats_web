# backend/app/services/organization_service.py
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Organization  # 假設您的 Organization 模型在 models/__init__.py 或直接導入
from ..tools.exceptions import AppException  # 假設您有自訂的 AppException


# --- 為此服務定義特定的業務異常 ---
# 建議將這些異常定義在一個共享的 exceptions.py 檔案中，以便路由層也能導入
class OrganizationNotFoundError(AppException):
    status_code = 404
    error_code = "organization_not_found"
    message = "找不到指定的組織。"


class OrganizationInUseError(AppException):
    status_code = 409  # 409 Conflict 更適合這種情況
    error_code = "organization_in_use"
    message = "無法刪除：此組織尚有關聯的成員。"


class OrganizationAlreadyExistsError(AppException):
    status_code = 409  # 409 Conflict
    error_code = "organization_already_exists"
    # 訊息會在拋出時動態設定


class OrganizationService:
    @staticmethod
    def get_all_organizations(args: dict):
        """
        獲取所有組織，並支援排序。
        'args' 是來自 request.args 的查詢參數字典。
        """
        sort_by = args.get("sort_by", "name")
        sort_order = args.get("sort_order", "asc")

        # 安全地獲取排序屬性，若無效則預設為 Organization.name
        sort_attr = getattr(Organization, sort_by, Organization.name)

        query = Organization.query.order_by(sort_attr.desc() if sort_order == "desc" else sort_attr.asc())
        return query.all()

    @staticmethod
    def get_organization_by_id(org_id: int) -> Organization | None:
        """根據 ID 查找組織。"""
        return db.session.get(Organization, org_id)

    @staticmethod
    def create_organization(data: dict) -> Organization:
        """
        創建一個新的組織。
        'data' 是經過 OrganizationCreateSchema 驗證後的數據。
        """
        # 業務邏輯：檢查名稱和簡稱是否已存在
        if Organization.query.filter_by(name=data["name"]).first():
            raise OrganizationAlreadyExistsError(f"組織名稱 '{data['name']}' 已存在。")
        if (
            "short_name" in data
            and data.get("short_name")
            and Organization.query.filter_by(short_name=data["short_name"]).first()
        ):
            raise OrganizationAlreadyExistsError(f"組織簡稱 '{data['short_name']}' 已存在。")

        new_org = Organization(**data)
        try:
            db.session.add(new_org)
            db.session.commit()
            return new_org
        except IntegrityError as e:  # 捕捉資料庫層級的唯一性衝突 (最終防線)
            db.session.rollback()
            raise AppException(f"資料庫錯誤，無法創建組織: {e.orig}", status_code=409)
        except Exception as e:
            db.session.rollback()
            raise AppException(f"創建組織時發生未預期錯誤: {e}")

    @staticmethod
    def update_organization(org: Organization, data: dict) -> Organization:
        """
        更新一個已存在的組織。
        'org' 是要更新的 Organization 模型實例。
        'data' 是經過 OrganizationUpdateSchema 驗證後的數據。
        """
        # 業務邏輯：如果正在更新名稱或簡稱，檢查新值是否已被其他組織使用
        if "name" in data and data["name"] != org.name:
            if Organization.query.filter(Organization.name == data["name"], Organization.id != org.id).first():
                raise OrganizationAlreadyExistsError(f"組織名稱 '{data['name']}' 已被其他組織使用。")

        if "short_name" in data and data.get("short_name") and data["short_name"] != org.short_name:
            if Organization.query.filter(
                Organization.short_name == data["short_name"], Organization.id != org.id
            ).first():
                raise OrganizationAlreadyExistsError(f"組織簡稱 '{data['short_name']}' 已被其他組織使用。")

        # 將驗證後的數據更新到模型實例上
        for field, value in data.items():
            if hasattr(org, field):
                setattr(org, field, value)

        try:
            db.session.commit()
            return org
        except Exception as e:
            db.session.rollback()
            raise AppException(f"更新組織時發生未預期錯誤: {e}")

    @staticmethod
    def delete_organization(org: Organization) -> bool:
        """
        刪除一個組織，在刪除前會檢查是否有成員關聯。
        """
        if not org:
            raise OrganizationNotFoundError()

        # 業務邏輯：檢查是否有成員關聯到這個組織
        if org.members:  # 檢查 'members' relationship 集合是否為空
            raise OrganizationInUseError(
                f"無法刪除組織 '{org.name}'，因其尚有關聯的 {len(org.members)} 位成員。請先將成員移至其他組織。"
            )

        try:
            db.session.delete(org)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise AppException(f"刪除組織時發生未預期錯誤: {e}")
