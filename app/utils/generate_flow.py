import inspect
import os
from typing import Dict, List, Union, get_args, get_origin

from fastapi import APIRouter

from app.routers import auth, classrooms, courses, schedules, students


def get_type_name(annotation) -> str:
    """获取类型注解的名称"""
    # 处理 Union 类型
    if get_origin(annotation) is Union:
        return " | ".join(arg.__name__ for arg in get_args(annotation))
    # 处理其他类型
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    # 处理 Optional 类型
    if str(annotation).startswith("typing.Optional"):
        return f"Optional[{get_type_name(get_args(annotation)[0])}]"
    # 处理其他情况
    return str(annotation).replace("typing.", "")


def get_router_endpoints(router: APIRouter) -> List[Dict]:
    """获取路由器中的所有端点信息"""
    endpoints = []
    for route in router.routes:
        # 获取视图函数的文档字符串
        docstring = inspect.getdoc(route.endpoint) or ""

        # 获取参数信息
        params = []
        for param in inspect.signature(route.endpoint).parameters.values():
            if param.name not in ["request", "db"]:  # 排除通用参数
                type_name = get_type_name(param.annotation)
                params.append(f"{param.name}: {type_name}")

        endpoints.append(
            {
                "path": route.path,
                "method": route.methods.pop() if route.methods else "GET",
                "name": route.name,
                "description": docstring.split("\n")[0],  # 获取第一行作为描述
                "parameters": params,
            }
        )
    return endpoints


def generate_flow_diagram(output_file: str = "flow_diagram.puml") -> None:
    """生成 PlantUML 格式的流程图"""
    routers = {
        "Auth": auth.router,
        "Courses": courses.router,
        "Students": students.router,
        "Classrooms": classrooms.router,
        "Schedules": schedules.router,
    }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # 写入 PlantUML 头部
            f.write("@startuml\n\n")
            f.write("!theme plain\n")
            f.write("skinparam handwritten true\n")
            f.write('skinparam defaultFontName "Microsoft YaHei"\n')
            f.write("skinparam activity {\n")
            f.write("  BackgroundColor LightYellow\n")
            f.write("  BorderColor Black\n")
            f.write("  FontSize 14\n")
            f.write("}\n\n")

            # 为每个路由模块生成泳道
            f.write("|Client|\n")

            # 开始节点
            f.write("start\n")
            f.write(":发起请求;\n\n")

            # 认证中间件
            f.write("|Authentication|\n")
            f.write("if (需要认证?) then (yes)\n")
            f.write("  :验证 JWT Token;\n")
            f.write("  if (Token 有效?) then (yes)\n")
            f.write("  else (no)\n")
            f.write("    :返回认证错误;\n")
            f.write("    end\n")
            f.write("  endif\n")
            f.write("endif\n\n")

            # 为每个路由模块生成处理流程
            for module_name, router in routers.items():
                f.write(f"|{module_name}|\n")
                endpoints = get_router_endpoints(router)

                for endpoint in endpoints:
                    # 生成端点处理流程
                    f.write(f":{endpoint['method']} {endpoint['path']}\\n")
                    f.write(f"{endpoint['description']};\n")

                    if endpoint["parameters"]:
                        f.write("note right\n")
                        f.write("参数:\n")
                        for param in endpoint["parameters"]:
                            f.write(f"* {param}\n")
                        f.write("end note\n")

                    f.write("\n")

            # 响应处理
            f.write("|Response|\n")
            f.write("if (处理成功?) then (yes)\n")
            f.write("  :返回成功响应;\n")
            f.write("else (no)\n")
            f.write("  :返回错误信息;\n")
            f.write("endif\n\n")

            # 结束节点
            f.write("stop\n\n")

            # 写入 PlantUML 结尾
            f.write("@enduml\n")

        print(f"流程图已生成到: {os.path.abspath(output_file)}")
        print("你可以使用以下方式查看生成的图：")
        print("1. 使用支持 PlantUML 的 IDE 插件")
        print("2. 在线查看：http://www.plantuml.com/plantuml/uml/")
        print("3. 使用命令行工具：java -jar plantuml.jar flow_diagram.puml")

    except Exception as e:
        print(f"生成流程图时发生错误: {str(e)}")


if __name__ == "__main__":
    generate_flow_diagram()
