#!/usr/bin/env python3
"""
GOST 端口映射管理工具
交互式菜单，支持多个GOST服务器
"""
import json
import requests
from requests.auth import HTTPBasicAuth
import sys
import os
from datetime import datetime

# GOST 服务器配置
GOST_SERVERS = {
    "1": {"name": "YTLC1", "url": "http://192.168.123.239:8090", "user": "admin", "pass": "Enabling@2025"},
    "2": {"name": "YTLC2", "url": "http://192.168.123.224:8090", "user": "admin", "pass": "Enabling@2025"},
    "3": {"name": "ECSHK", "url": "http://192.168.123.1:18080", "user": "admin", "pass": "Enabling@2025"},
    "4": {"name": "FSMTC", "url": "http://192.168.123.180:8090", "user": "admin", "pass": "Enabling@2025"},
    "5": {"name": "KTRN", "url": "http://192.168.123.163:18080", "user": "admin", "pass": "Enabling@2025"},
}

# 当前选中的服务器
current_server = None

def clear_screen():
    """清屏"""
    print("\033[2J\033[H", end="")

def print_header():
    """打印头部信息"""
    print("=" * 60)
    print("         GOST 端口映射管理工具")
    print("=" * 60)
    if current_server:
        server = GOST_SERVERS[current_server]
        print(f"当前服务器: {server['name']} ({server['url']})")
    else:
        print("当前服务器: 未选择")
    print("=" * 60)

def select_server():
    """选择GOST服务器"""
    global current_server
    while True:
        clear_screen()
        print_header()
        print("\n" + "=" * 60)
        print("                 选择GOST服务器")
        print("=" * 60)
        print()
        print("  ┌────┬──────────┬─────────────────────────────────┐")
        print("  │ 序号│  名称    │          API地址               │")
        print("  ├────┼──────────┼─────────────────────────────────┤")
        for key, server in GOST_SERVERS.items():
            marker = " ←" if key == current_server else "  "
            print(f"  │  {key}{marker} │ {server['name']:8} │ {server['url']:30} │")
        print("  └────┴──────────┴─────────────────────────────────┘")
        print()
        print("  0. 返回主菜单")
        print("-" * 60)

        choice = input("\n请输入选项: ").strip()
        if choice == "0":
            return
        elif choice in GOST_SERVERS:
            current_server = choice
            print(f"\n✅ 已切换到服务器: {GOST_SERVERS[choice]['name']} ({GOST_SERVERS[choice]['url']})")
            input("按回车继续...")
            return
        else:
            print("❌ 无效选项，请重新输入")
            input("按回车继续...")

def get_auth():
    """获取当前服务器的认证信息"""
    if not current_server:
        return None
    server = GOST_SERVERS[current_server]
    return HTTPBasicAuth(server['user'], server['pass'])

def get_api_url():
    """获取当前服务器的API URL"""
    if not current_server:
        return None
    return GOST_SERVERS[current_server]['url']

def list_services():
    """列出所有服务"""
    if not current_server:
        print("❌ 请先选择服务器")
        input("按回车继续...")
        return

    try:
        response = requests.get(
            f"{get_api_url()}/config/services",
            auth=get_auth(),
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            services = data.get("data", {}).get("list", [])

            clear_screen()
            print_header()
            print(f"\n服务列表 (共 {len(services)} 个):")
            print("-" * 60)
            print(f"{'序号':<4} {'服务名称':<35} {'端口':<8} {'目标地址'}")
            print("-" * 60)

            for i, svc in enumerate(services, 1):
                name = svc.get("name", "N/A")
                addr = svc.get("addr", "N/A")
                nodes = svc.get("forwarder", {}).get("nodes", [])
                target = nodes[0].get("addr", "N/A") if nodes else "N/A"
                print(f"{i:<4} {name:<35} {addr:<8} {target}")

            print("-" * 60)
        else:
            print(f"❌ 获取服务列表失败: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ 连接失败: {e}")

    input("\n按回车继续...")

def auto_backup():
    """自动备份配置（内部使用，无交互）"""
    from datetime import datetime

    server = GOST_SERVERS[current_server]
    server_name = server['name']
    backup_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(__file__), "backups")

    # 创建备份目录
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    backup_file = os.path.join(backup_dir, f"{server_name}_{backup_date}.json")

    try:
        # 获取完整配置
        response = requests.get(
            f"{get_api_url()}/config",
            auth=get_auth(),
            timeout=30
        )

        if response.status_code == 200:
            config_data = response.json()

            # 添加备份元信息
            backup_data = {
                "backup_info": {
                    "server_name": server_name,
                    "server_url": server['url'],
                    "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "backup_by": "gost_manager_auto"
                },
                "config": config_data
            }

            # 写入备份文件
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            return backup_file
        else:
            return None
    except Exception as e:
        return None

def add_service():
    """添加服务"""
    if not current_server:
        print("❌ 请先选择服务器")
        input("按回车继续...")
        return

    clear_screen()
    print_header()
    print("\n添加新服务")
    print("-" * 40)

    # 先自动备份
    print("正在备份当前配置...")
    backup_file = auto_backup()
    if backup_file:
        print(f"✅ 已备份到: {os.path.basename(backup_file)}")
    else:
        print("⚠️  备份失败，继续操作...")
    print("-" * 40)

    try:
        name = input("服务名称: ").strip()
        if not name:
            print("❌ 服务名称不能为空")
            input("按回车继续...")
            return

        gost_port = input("GOST监听端口: ").strip()
        if not gost_port:
            print("❌ 端口不能为空")
            input("按回车继续...")
            return

        target_ip = input("目标IP地址: ").strip()
        if not target_ip:
            print("❌ 目标IP不能为空")
            input("按回车继续...")
            return

        target_port = input("目标端口: ").strip()
        if not target_port:
            print("❌ 目标端口不能为空")
            input("按回车继续...")
            return

        # 确认添加
        print("\n" + "-" * 40)
        print(f"服务名称: {name}")
        print(f"监听端口: :{gost_port}")
        print(f"目标地址: {target_ip}:{target_port}")
        print("-" * 40)

        confirm = input("确认添加? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            input("按回车继续...")
            return

        # 构建配置
        config = {
            "name": name,
            "addr": f":{gost_port}",
            "handler": {
                "type": "tcp"
            },
            "listener": {
                "type": "tcp"
            },
            "forwarder": {
                "nodes": [
                    {
                        "name": name.replace("-ssh", "").replace("-listen-port", ""),
                        "addr": f"{target_ip}:{target_port}"
                    }
                ]
            }
        }

        # 发送请求
        response = requests.post(
            f"{get_api_url()}/config/services",
            auth=get_auth(),
            headers={"Content-Type": "application/json"},
            json=config,
            timeout=10
        )

        if response.status_code in [200, 201]:
            print(f"\n✅ 服务 '{name}' 添加成功!")
        else:
            print(f"\n❌ 添加失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"❌ 添加服务时发生异常: {e}")

    input("\n按回车继续...")

def delete_service():
    """删除服务"""
    if not current_server:
        print("❌ 请先选择服务器")
        input("按回车继续...")
        return

    clear_screen()
    print_header()
    print("\n删除服务")
    print("-" * 40)

    service_name = input("请输入要删除的服务名称: ").strip()
    if not service_name:
        print("❌ 服务名称不能为空")
        input("按回车继续...")
        return

    confirm = input(f"确认删除服务 '{service_name}'? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        input("按回车继续...")
        return

    try:
        response = requests.delete(
            f"{get_api_url()}/config/services/{service_name}",
            auth=get_auth(),
            timeout=10
        )

        if response.status_code in [200, 204]:
            print(f"\n✅ 服务 '{service_name}' 删除成功!")
        else:
            print(f"\n❌ 删除失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"❌ 删除服务时发生异常: {e}")

    input("\n按回车继续...")

def batch_add_services():
    """批量添加服务"""
    if not current_server:
        print("❌ 请先选择服务器")
        input("按回车继续...")
        return

    clear_screen()
    print_header()
    print("\n" + "=" * 60)
    print("                    批量添加服务")
    print("=" * 60)

    # 先自动备份
    print("\n正在备份当前配置...")
    backup_file = auto_backup()
    if backup_file:
        print(f"✅ 已备份到: {os.path.basename(backup_file)}")
    else:
        print("⚠️  备份失败，继续操作...")

    print()
    print("  ┌────────────────────────────────────────────────────┐")
    print("  │  输入格式 (用空格分隔):                            │")
    print("  │                                                    │")
    print("  │  服务名称    GOST端口    目标IP    目标端口        │")
    print("  │                                                    │")
    print("  │  示例:                                             │")
    print("  │  ktrn-pr-ocs01-ssh 52001 192.168.20.140 22        │")
    print("  │  ktrn-pr-app01-ssh 52011 192.168.20.152 22        │")
    print("  │  my-db-forward     53000 192.168.10.100 3306      │")
    print("  └────────────────────────────────────────────────────┘")
    print()
    print("  输入空行结束输入")
    print("-" * 60)

    services = []
    while True:
        line = input(f"服务 {len(services) + 1}: ").strip()
        if not line:
            break

        parts = line.split()
        if len(parts) != 4:
            print("❌ 格式错误，请重新输入")
            continue

        services.append({
            "name": parts[0],
            "gost_port": parts[1],
            "target_ip": parts[2],
            "target_port": parts[3]
        })

    if not services:
        print("未输入任何服务")
        input("按回车继续...")
        return

    print(f"\n共输入 {len(services)} 个服务")
    confirm = input("确认批量添加? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        input("按回车继续...")
        return

    # 批量添加
    success_count = 0
    fail_count = 0

    for i, svc in enumerate(services, 1):
        config = {
            "name": svc["name"],
            "addr": f":{svc['gost_port']}",
            "handler": {"type": "tcp"},
            "listener": {"type": "tcp"},
            "forwarder": {
                "nodes": [{
                    "name": svc["name"].replace("-ssh", "").replace("-listen-port", ""),
                    "addr": f"{svc['target_ip']}:{svc['target_port']}"
                }]
            }
        }

        try:
            response = requests.post(
                f"{get_api_url()}/config/services",
                auth=get_auth(),
                headers={"Content-Type": "application/json"},
                json=config,
                timeout=10
            )

            if response.status_code in [200, 201]:
                print(f"  [{i}/{len(services)}] ✅ {svc['name']}")
                success_count += 1
            else:
                print(f"  [{i}/{len(services)}] ❌ {svc['name']} - HTTP {response.status_code}")
                fail_count += 1
        except Exception as e:
            print(f"  [{i}/{len(services)}] ❌ {svc['name']} - {e}")
            fail_count += 1

    print("-" * 40)
    print(f"完成: 成功 {success_count}, 失败 {fail_count}")

    input("\n按回车继续...")

def delete_all_services():
    """删除所有服务"""
    if not current_server:
        print("❌ 请先选择服务器")
        input("按回车继续...")
        return

    clear_screen()
    print_header()
    print("\n" + "=" * 60)
    print("          ⚠️  危险操作：删除所有服务 ⚠️")
    print("=" * 60)
    print()
    print("  此操作将删除当前服务器上的所有端口映射服务！")
    print("  此操作不可恢复！")
    print()
    print("-" * 60)

    # 输入管理密码验证
    admin_password = input("请输入管理密码以确认操作: ").strip()
    if admin_password != "iWhale@2023":
        print("\n❌ 密码错误，操作已取消")
        input("按回车继续...")
        return

    confirm = input("\n再次确认删除所有服务? 输入 'DELETE ALL' 确认: ").strip()
    if confirm != "DELETE ALL":
        print("已取消")
        input("按回车继续...")
        return

    try:
        # 获取所有服务
        response = requests.get(
            f"{get_api_url()}/config/services",
            auth=get_auth(),
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            services = data.get("data", {}).get("list", [])

            print(f"\n正在删除 {len(services)} 个服务...")

            success_count = 0
            for svc in services:
                name = svc.get("name")
                try:
                    del_response = requests.delete(
                        f"{get_api_url()}/config/services/{name}",
                        auth=get_auth(),
                        timeout=10
                    )
                    if del_response.status_code in [200, 204]:
                        print(f"  ✅ 已删除: {name}")
                        success_count += 1
                    else:
                        print(f"  ❌ 失败: {name}")
                except Exception as e:
                    print(f"  ❌ 异常: {name} - {e}")

            print("-" * 40)
            print(f"完成: 成功删除 {success_count}/{len(services)} 个服务")
        else:
            print(f"❌ 获取服务列表失败: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ 操作失败: {e}")

    input("\n按回车继续...")

def test_connection():
    """测试服务器连接"""
    if not current_server:
        print("❌ 请先选择服务器")
        input("按回车继续...")
        return

    server = GOST_SERVERS[current_server]
    print(f"\n正在测试连接: {server['name']} ({server['url']})...")

    try:
        response = requests.get(
            f"{get_api_url()}/config",
            auth=get_auth(),
            timeout=5
        )

        if response.status_code == 200:
            print(f"✅ 连接成功!")
            data = response.json()
            print(f"   API地址: {data.get('api', {}).get('addr', 'N/A')}")
            authers = data.get('authers', [])
            if authers:
                print(f"   认证用户: {authers[0].get('auths', [{}])[0].get('username', 'N/A')}")
        else:
            print(f"❌ 连接失败: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ 连接失败: {e}")

    input("\n按回车继续...")

def backup_config():
    """备份配置到本地"""
    if not current_server:
        print("❌ 请先选择服务器")
        input("按回车继续...")
        return

    from datetime import datetime

    server = GOST_SERVERS[current_server]
    server_name = server['name']
    backup_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(__file__), "backups")

    # 创建备份目录
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    backup_file = os.path.join(backup_dir, f"{server_name}_{backup_date}.json")

    print(f"\n正在备份服务器配置: {server_name}...")
    print("-" * 40)

    try:
        # 获取完整配置
        response = requests.get(
            f"{get_api_url()}/config",
            auth=get_auth(),
            timeout=30
        )

        if response.status_code == 200:
            config_data = response.json()

            # 添加备份元信息
            backup_data = {
                "backup_info": {
                    "server_name": server_name,
                    "server_url": server['url'],
                    "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "backup_by": "gost_manager"
                },
                "config": config_data
            }

            # 写入备份文件
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            # 统计信息
            services = config_data.get('services', [])
            authers = config_data.get('authers', [])
            chains = config_data.get('chains', [])

            print(f"✅ 备份成功!")
            print()
            print(f"  备份文件: {backup_file}")
            print(f"  文件大小: {os.path.getsize(backup_file)} 字节")
            print()
            print(f"  配置统计:")
            print(f"    - 服务数量: {len(services)}")
            print(f"    - 认证器数量: {len(authers)}")
            print(f"    - 链路数量: {len(chains)}")

        else:
            print(f"❌ 获取配置失败: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ 备份失败: {e}")

    input("\n按回车继续...")

def main():
    """主菜单"""
    while True:
        clear_screen()
        print_header()
        print("\n主菜单:")
        print("-" * 40)
        print("  1. 选择GOST服务器")
        print("  2. 查看所有服务")
        print("  3. 添加单个服务")
        print("  4. 删除单个服务")
        print("  5. 批量添加服务")
        print("  6. 删除所有服务 (需管理密码)")
        print("  7. 测试服务器连接")
        print("  8. 备份服务器配置")
        print("  0. 退出")
        print("-" * 40)

        choice = input("\n请输入选项: ").strip()

        if choice == "1":
            select_server()
        elif choice == "2":
            list_services()
        elif choice == "3":
            add_service()
        elif choice == "4":
            delete_service()
        elif choice == "5":
            batch_add_services()
        elif choice == "6":
            delete_all_services()
        elif choice == "7":
            test_connection()
        elif choice == "8":
            backup_config()
        elif choice == "0":
            print("\n再见!")
            sys.exit(0)
        else:
            print("❌ 无效选项")
            input("按回车继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
