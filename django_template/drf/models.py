import logging
import time
from functools import wraps

from django import db
from django.db import models

logger = logging.getLogger("django")


class BasicModel(models.Model):
    """
    创建更新时间

    """

    create_ts = models.DateTimeField(auto_now_add=True)
    update_ts = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class _SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(delete_ts=int(time.time() * 1000))

    def hard_delete(self):
        return super().delete()


class _SoftDeleteManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset().filter(delete_ts=0)
        if not issubclass(qs.__class__, _SoftDeleteQuerySet):
            qs.__class__ = _SoftDeleteQuerySet
        return qs


class _SoftDeleteModel(models.Model):
    delete_ts = models.BigIntegerField(default=0)

    objects = _SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.delete_ts = int(time.time() * 1000)
        self.save(update_fields=["delete_ts"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using, keep_parents)


class SDBasicModel(_SoftDeleteModel, BasicModel):
    """
    软删除 model

    """

    class Meta:
        abstract = True


def close_db(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        db.close_old_connections()
        try:
            return func(*args, **kwargs)
        finally:
            db.close_old_connections()

    return func_wrapper


class RollbackException(Exception):
    pass


class LoggingRequestMiddleware:
    """
    打印接口耗时
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.time()
        response = self.get_response(request)

        t = int((time.time() - t0) * 1000)
        logger.info(f"request: {request.get_full_path()} {t} ms")
        return response


class DynamicModel:
    """
    动态模型

    """

    _instance = {}

    def __new__(cls, base_cls, **kwargs):
        table_name = base_cls.get_table_name(**kwargs)
        new_cls_name = "".join(map(lambda x: x.capitalize(), table_name.split("_")))

        if new_cls_name not in cls._instance:
            meta_cls = base_cls.Meta
            meta_cls.db_table = table_name
            model_cls = type(
                new_cls_name,
                (base_cls,),
                {
                    "Meta": meta_cls,
                    "__module__": cls.__module__,
                },
            )
            cls._instance[new_cls_name] = model_cls

        return cls._instance[new_cls_name]
