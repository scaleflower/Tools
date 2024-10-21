# Tools
# SSH 一键工具
- [SSH一键工具](https://github.com/scaleflower/Tools/blob/main/scripts/ssh_tool.sh)
  来源于：https://github.com/eooce/Sing-box
  ```ssh综合工具箱一键脚本
  curl -fsSL https://raw.githubusercontent.com/eooce/ssh_tool/main/ssh_tool.sh -o ssh_tool.sh && chmod +x ssh_tool.sh && ./ssh_tool.sh
  ```
# DD 一键重新安装系统
-DD重装一键脚本
```DD脚本
curl -O https://raw.githubusercontent.com/bin456789/reinstall/main/reinstall.sh && bash reinstall.sh
```
功能 : 安装 Linux不输入版本号，则安装最新版不含 boot 分区（Fedora 例外），不含 swap 分区，最大化利用磁盘空间在虚拟机上，会自动安装官方精简内核安装 Debian / Kali 时，x86 可通过后台 VNC 查看安装进度，ARM 可通过串行控制台查看安装进度。安装其它系统时，可通过多种方式（SSH、HTTP 80 端口、后台 VNC、串行控制台）查看安装进度。
