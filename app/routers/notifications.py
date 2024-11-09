from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..utils.auth import get_current_user
from ..utils.response import response
from datetime import datetime

router = APIRouter()

@router.post("/")
def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限发送通知")

    # 检查接收用户是否存在
    user = db.query(models.User).filter(models.User.id == notification.user_id).first()
    if not user:
        return response(code=404, message="接收用户不存在")

    db_notification = models.Notification(
        **notification.dict(),
        is_read=False,
        created_at=datetime.now()
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return response(data=db_notification)

@router.get("/user/{user_id}")
def get_user_notifications(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 检查权限
    if current_user.id != user_id and current_user.role not in ["admin"]:
        return response(code=403, message="只能查看自己的通知")

    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == user_id
    ).order_by(
        models.Notification.created_at.desc()
    ).offset(skip).limit(limit).all()

    return response(data=notifications)

@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id
    ).first()

    if not notification:
        return response(code=404, message="通知不存在")

    # 检查权限
    if notification.user_id != current_user.id and current_user.role not in ["admin"]:
        return response(code=403, message="只能标记自己的通知为已读")

    notification.is_read = True
    db.commit()
    return response(message="已标记为已读")

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id
    ).first()

    if not notification:
        return response(code=404, message="通知不存在")

    # 检查权限
    if notification.user_id != current_user.id and current_user.role not in ["admin"]:
        return response(code=403, message="只能删除自己的通知")

    db.delete(notification)
    db.commit()
    return response(message="删除成功")

@router.post("/batch")
def send_batch_notifications(
    notifications: list[schemas.NotificationCreate],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        return response(code=403, message="没有权限发送批量通知")

    results = {"success": [], "failed": []}

    for notification in notifications:
        try:
            # 检查接收用户是否存在
            user = db.query(models.User).filter(models.User.id == notification.user_id).first()
            if not user:
                results["failed"].append({
                    "user_id": notification.user_id,
                    "reason": "用户不存在"
                })
                continue

            db_notification = models.Notification(
                **notification.dict(),
                is_read=False,
                created_at=datetime.now()
            )
            db.add(db_notification)
            results["success"].append(notification.user_id)

        except Exception as e:
            results["failed"].append({
                "user_id": notification.user_id,
                "reason": str(e)
            })

    db.commit()
    return response(data=results)

@router.get("/unread/count/{user_id}")
def get_unread_count(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 检查权限
    if current_user.id != user_id and current_user.role not in ["admin"]:
        return response(code=403, message="只能查看自己的未读通知数量")

    count = db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).count()

    return response(data={"unread_count": count})

@router.put("/read/all/{user_id}")
def mark_all_as_read(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 检查权限
    if current_user.id != user_id and current_user.role not in ["admin"]:
        return response(code=403, message="只能标记自己的通知为已读")

    db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).update({"is_read": True})

    db.commit()
    return response(message="所有通知已标记为已读")