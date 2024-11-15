import os
import sys
from inspect import getmembers, isclass
from typing import List, Type

from sqlalchemy import Column
from sqlalchemy.orm import DeclarativeMeta, RelationshipProperty

from app import models


def get_column_type(column: Column) -> str:
    """获取列的数据类型"""
    python_type = str(column.type)
    # 移除括号中的参数
    return python_type.split("(")[0]


def get_relationship_details(prop: RelationshipProperty) -> str:
    """获取关系的详细信息"""
    if prop.uselist:
        # 一对多关系
        return "||--o{"
    else:
        # 一对一关系
        return "||--||"


def check_graphviz_installation():
    """检查是否安装了 Graphviz"""
    if sys.platform.startswith("win"):
        # Windows 系统
        from subprocess import DEVNULL, PIPE, Popen

        try:
            Popen(["dot", "-V"], stdout=PIPE, stderr=PIPE).communicate()
            return True
        except FileNotFoundError:
            print("错误: 未找到 Graphviz。")
            print("请访问 https://graphviz.org/download/ 下载并安装 Graphviz。")
            print("Windows 用户也可以使用命令: winget install graphviz")
            return False
    else:
        # Linux/MacOS 系统
        if os.system("which dot > /dev/null 2>&1") != 0:
            print("错误: 未找到 Graphviz。")
            print("请使用包管理器安装 Graphviz:")
            print("MacOS: brew install graphviz")
            print("Ubuntu/Debian: sudo apt-get install graphviz")
            print("CentOS/RHEL: sudo yum install graphviz")
            return False
        return True


def generate_plantuml(output_file: str = "er_diagram.puml") -> None:
    """生成 PlantUML 格式的 ER 图"""
    if not check_graphviz_installation():
        return

    model_classes = [
        cls
        for _, cls in getmembers(models, isclass)
        if isinstance(cls, DeclarativeMeta) and cls.__name__ != "Base"
    ]

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # 写入 PlantUML 头部
            f.write("@startuml\n\n")
            f.write("!theme plain\n")
            f.write("skinparam linetype ortho\n")
            f.write("skinparam rankdir TB\n")
            f.write("skinparam dpi 300\n")
            f.write("skinparam nodesep 80\n")
            f.write("skinparam ranksep 100\n\n")

            # 生成实体定义
            for model in model_classes:
                f.write(f'entity "{model.__tablename__}" as {model.__tablename__} {{\n')
                # 写入主键
                for column in model.__table__.columns:
                    if column.primary_key:
                        f.write(f"  + {column.name}: {get_column_type(column)}\n")
                # 写入其他列
                for column in model.__table__.columns:
                    if not column.primary_key:
                        nullable = "nullable" if column.nullable else "not null"
                        comment = f"// {column.comment}" if column.comment else ""
                        f.write(
                            f"  {column.name}: {get_column_type(column)} [{nullable}] {comment}\n"
                        )
                f.write("}\n\n")

            # 生成关系
            for model in model_classes:
                for relationship in model.__mapper__.relationships:
                    parent = model.__tablename__
                    child = relationship.mapper.class_.__tablename__
                    relation_type = get_relationship_details(relationship)
                    f.write(f'"{parent}" {relation_type} "{child}"\n')

            # 写入 PlantUML 结尾
            f.write("\n@enduml\n")

        print(f"ER 图已生成到: {os.path.abspath(output_file)}")
        print("你可以使用以下方式查看生成的图：")
        print("1. 使用支持 PlantUML 的 IDE 插件")
        print("2. 在线查看：http://www.plantuml.com/plantuml/uml/")
        print("3. 使用命令行工具：java -jar plantuml.jar er_diagram.puml")

    except Exception as e:
        print(f"生成 ER 图时发生错误: {str(e)}")


if __name__ == "__main__":
    generate_plantuml()
