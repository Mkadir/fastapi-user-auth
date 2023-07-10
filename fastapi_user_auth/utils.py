from functools import lru_cache
from typing import Any, Dict, List

from casbin import Enforcer
from fastapi_amis_admin.admin import FormAdmin, ModelAdmin, PageSchemaAdmin
from fastapi_amis_admin.admin.admin import AdminGroup, BaseActionAdmin


@lru_cache()
def get_admin_action_options(group: AdminGroup) -> List[Dict[str, Any]]:
    """获取全部页面权限,用于amis组件"""
    options = []
    for admin in group:  # 这里已经同步了数据库,所以只从这里配置权限就行了
        admin: PageSchemaAdmin
        if not admin.page_schema:
            continue
        item = {"label": admin.page_schema.label, "value": f"{admin.unique_id}#admin:page", "sort": admin.page_schema.sort}
        if isinstance(admin, BaseActionAdmin):
            item["children"] = []
            if isinstance(admin, ModelAdmin):
                item["children"].append({"label": "查看列表", "value": f"{admin.unique_id}#admin:list"})
            elif isinstance(admin, FormAdmin) and "submit" not in admin.registered_admin_actions:
                item["children"].append({"label": "提交", "value": f"{admin.unique_id}#admin:submit"})
            for admin_action in admin.registered_admin_actions.values():
                item["children"].append({"label": admin_action.label, "value": f"{admin.unique_id}#admin:{admin_action.name}"})
        elif isinstance(admin, AdminGroup):
            item["children"] = get_admin_action_options(admin)
        options.append(item)
    if options:
        options.sort(key=lambda p: p["sort"] or 0, reverse=True)
    return options


async def casbin_update_subject_roles(enforcer: Enforcer, subject: str, role_keys: str = None):
    """更新casbin主体权限角色"""
    # 删除旧的角色
    await enforcer.remove_filtered_grouping_policy(0, subject)
    # 添加新的角色
    if role_keys:
        await enforcer.add_grouping_policies([(subject, "r:" + role) for role in role_keys.split(",") if role])


async def casbin_update_subject_permissions(enforcer: Enforcer, subject: str, permissions: List[str]) -> List[str]:
    """根据指定subject主体更新casbin规则,会删除旧的规则,添加新的规则"""
    # 删除旧的权限
    await enforcer.remove_filtered_policy(0, subject)
    # 添加新的权限
    await enforcer.add_policies([(subject, v1, v2) for v1, v2 in [permission.split("#") for permission in permissions]])
    # 返回动作处理结果
    return permissions


# print("get_roles_for_user",await enforcer.get_roles_for_user(subject))
# print("get_permissions_for_user", await enforcer.get_permissions_for_user(subject))
# print("get_implicit_permissions_for_user", await enforcer.get_implicit_permissions_for_user(subject))
# print("get_implicit_roles_for_user", await enforcer.get_implicit_roles_for_user(subject))