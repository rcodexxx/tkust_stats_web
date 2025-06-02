# backend/app/api/organization_routes.py
from flask import request, jsonify, current_app

from . import bp  # API 藍圖
from ..extensions import db
from ..models.organization import Organization


@bp.route("/organizations", methods=["POST"])
# @admin_required # 只有管理員可以新增組織
def create_organization():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Organization name is required"}), 400

    name = data.get("name")
    city = data.get("city")
    notes = data.get("notes")

    if Organization.query.filter_by(name=name).first():
        return (
            jsonify({"error": f"Organization with name '{name}' already exists."}),
            409,
        )

    try:
        new_org = Organization(name=name, city=city, notes=notes)
        db.session.add(new_org)
        db.session.commit()
        return jsonify(new_org.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error creating organization: {str(e)}", exc_info=True
        )
        return jsonify({"error": "Failed to create organization."}), 500


@bp.route("/organizations", methods=["GET"])
def get_organizations():
    """獲取所有組織列表，用於前端下拉選單等"""
    try:
        # 可以加入排序，例如按名稱
        orgs = Organization.query.order_by(Organization.name).all()
        return jsonify([org.to_dict() for org in orgs])
    except Exception as e:
        current_app.logger.error(
            f"Error fetching organizations: {str(e)}", exc_info=True
        )
        return jsonify({"error": "Failed to fetch organizations."}), 500


@bp.route("/organizations/<int:org_id>", methods=["GET"])
def get_organization(org_id):
    org = db.session.get(Organization, org_id)
    if not org:
        return jsonify({"error": "Organization not found"}), 404
    return jsonify(org.to_dict())


@bp.route("/organizations/<int:org_id>", methods=["PUT"])
# @admin_required
def update_organization(org_id):
    org = db.session.get(Organization, org_id)
    if not org:
        return jsonify({"error": "Organization not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request payload must be JSON"}), 400

    errors = {}
    if "name" in data and data["name"] != org.name:
        if Organization.query.filter(
            Organization.id != org_id, Organization.name == data["name"]
        ).first():
            errors["name"] = f"Organization name '{data['name']}' already exists."

    if errors:
        return jsonify({"message": "Validation failed", "errors": errors}), 400

    try:
        org.name = data.get("name", org.name)
        org.city = data.get("city", org.city)
        org.notes = data.get("notes", org.notes)
        db.session.commit()
        return jsonify(org.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error updating organization {org_id}: {str(e)}", exc_info=True
        )
        return jsonify({"error": "Failed to update organization."}), 500


@bp.route("/organizations/<int:org_id>", methods=["DELETE"])
# @admin_required
def delete_organization(org_id):
    org = db.session.get(Organization, org_id)
    if not org:
        return jsonify({"error": "Organization not found"}), 404

    # 檢查是否有成員關聯到這個組織
    if org.members.first():  # 如果 lazy='dynamic'
        return (
            jsonify(
                {
                    "error": "Cannot delete organization: It has associated members. Please reassign members first."
                }
            ),
            400,
        )
        # 或者，您可以選擇將關聯成員的 organization_id 設為 NULL (如果模型允許)
        # for member in org.members:
        #     member.organization_id = None
        #     member.organization_profile = None
        # db.session.flush()

    try:
        db.session.delete(org)
        db.session.commit()
        return jsonify({"message": "Organization deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting organization {org_id}: {str(e)}", exc_info=True
        )
        return jsonify({"error": "Failed to delete organization."}), 500
