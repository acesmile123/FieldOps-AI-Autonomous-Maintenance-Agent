from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import MediaAsset, WorkOrder
from app.core.config import get_settings
from app.schemas.work_order import (
    AgentEventRead, AgentRunRead, MediaAssetRead, StatusUpdate, WorkOrderDetail,
    WorkOrderList, WorkOrderRead, WorkOrderStatus, WorkOrderUpdate,
)
from app.services.work_order_service import WorkOrderConflict, WorkOrderService, event
from app.storage.local_storage import LocalMediaStorage

router = APIRouter(prefix="/api/v1/work-orders")


def get_media_storage() -> LocalMediaStorage:
    return LocalMediaStorage(get_settings())


def error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def detail(order: WorkOrder) -> WorkOrderDetail:
    return WorkOrderDetail(
        work_order=WorkOrderRead.model_validate(order),
        media_assets=[MediaAssetRead.model_validate(asset) for asset in order.media_assets],
        agent_run=AgentRunRead.model_validate(order.agent_run),
        events=[AgentEventRead.model_validate(item) for item in order.agent_run.events],
    )


@router.get("", response_model=WorkOrderList)
def list_orders(
    status: WorkOrderStatus | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> WorkOrderList:
    condition = WorkOrder.status == status.value if status else True
    total = db.scalar(select(func.count()).select_from(WorkOrder).where(condition)) or 0
    orders = db.scalars(
        select(WorkOrder).where(condition)
        .order_by(WorkOrder.created_at.desc(), WorkOrder.id.desc())
        .limit(limit).offset(offset)
    ).all()
    return WorkOrderList(
        items=[WorkOrderRead.model_validate(order) for order in orders],
        total=total, limit=limit, offset=offset,
    )


@router.get("/{order_id}", response_model=WorkOrderDetail)
def get_order(order_id: UUID, db: Session = Depends(get_db)) -> WorkOrderDetail | JSONResponse:
    order = db.get(WorkOrder, str(order_id))
    return detail(order) if order else error("NOT_FOUND", "Work order not found.", 404)


@router.get("/{order_id}/media/{asset_id}")
def get_media(
    order_id: UUID,
    asset_id: UUID,
    db: Session = Depends(get_db),
    storage: LocalMediaStorage = Depends(get_media_storage),
):
    asset = db.get(MediaAsset, str(asset_id))
    if not asset or asset.work_order_id != str(order_id) or not db.get(WorkOrder, str(order_id)):
        return error("NOT_FOUND", "Media asset not found.", 404)
    path = Path(asset.storage_path).resolve()
    root = storage.directory.resolve()
    if not path.is_relative_to(root) or path.suffix.lower() not in {".jpg", ".wav"} or not path.is_file():
        return error("NOT_FOUND", "Media asset not found.", 404)
    return FileResponse(
        path,
        media_type=asset.mime_type,
        filename=asset.original_filename,
        content_disposition_type="inline",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.patch("/{order_id}", response_model=WorkOrderDetail)
def edit_order(order_id: UUID, patch: WorkOrderUpdate, db: Session = Depends(get_db)) -> WorkOrderDetail | JSONResponse:
    order = db.get(WorkOrder, str(order_id))
    if not order:
        return error("NOT_FOUND", "Work order not found.", 404)
    try:
        WorkOrderService.edit(order, patch)
    except WorkOrderConflict as exc:
        return error("INVALID_TRANSITION", str(exc), 409)
    except ValueError as exc:
        return error("INVALID_UPDATE", str(exc), 422)
    db.add(event(order.agent_run, "work_order_edited", "work_order", "succeeded", "Draft work order edited."))
    db.commit()
    return detail(order)


@router.post("/{order_id}/approve", response_model=WorkOrderDetail)
def approve_order(order_id: UUID, db: Session = Depends(get_db)) -> WorkOrderDetail | JSONResponse:
    order = db.get(WorkOrder, str(order_id))
    if not order:
        return error("NOT_FOUND", "Work order not found.", 404)
    try:
        WorkOrderService.approve(order)
    except WorkOrderConflict as exc:
        return error("INVALID_TRANSITION", str(exc), 409)
    db.add(event(order.agent_run, "work_order_approved", "approval", "succeeded",
                 "Work order explicitly approved by the operator."))
    db.commit()
    return detail(order)


@router.patch("/{order_id}/status", response_model=WorkOrderDetail)
def change_status(order_id: UUID, patch: StatusUpdate, db: Session = Depends(get_db)) -> WorkOrderDetail | JSONResponse:
    order = db.get(WorkOrder, str(order_id))
    if not order:
        return error("NOT_FOUND", "Work order not found.", 404)
    try:
        WorkOrderService.change_status(order, patch.status)
    except WorkOrderConflict as exc:
        return error("INVALID_TRANSITION", str(exc), 409)
    db.add(event(order.agent_run, "status_changed", "work_order", "succeeded",
                 f"Work order status changed to {patch.status.value}."))
    db.commit()
    return detail(order)
