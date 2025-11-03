# 🐳 BTAUTOCHECK Docker 部署指南

> **版本**: V2.0  
> **更新时间**: 2025-11-03

---

## 📖 简介

使用Docker部署BTAUTOCHECK，享受以下优势：

✅ **一键部署** - 无需手动安装依赖  
✅ **环境隔离** - 不影响宿主机环境  
✅ **自动重启** - 崩溃自动恢复  
✅ **数据持久化** - 配置、备份、日志持久保存  
✅ **健康检查** - 自动监控服务状态  

---

## 🚀 快速开始

### 方式1: Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/GSDPGIT/BTAUTOCHECK.git
cd BTAUTOCHECK

# 2. 准备配置文件
cp config.example.json config.json
nano config.json  # 编辑配置（可选）

# 3. 一键启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 访问Web界面
# http://你的服务器IP:5000
# 默认账号: admin
# 默认密码: admin123
```

### 方式2: 纯Docker命令

```bash
# 1. 构建镜像
docker build -t btautocheck:latest .

# 2. 运行容器
docker run -d \
  --name btautocheck \
  -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json \
  -v btautocheck-downloads:/app/downloads \
  -v btautocheck-backups:/app/backups \
  -v btautocheck-logs:/app/logs \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  btautocheck:latest

# 3. 查看日志
docker logs -f btautocheck

# 4. 访问Web界面
# http://你的服务器IP:5000
```

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TZ` | 时区 | `Asia/Shanghai` |
| `PYTHONUNBUFFERED` | Python输出不缓冲 | `1` |
| `FLASK_APP` | Flask应用 | `web_admin.py` |

### 数据卷

| 卷 | 路径 | 说明 |
|----|------|------|
| `btautocheck-downloads` | `/app/downloads` | 下载的面板升级包 |
| `btautocheck-backups` | `/app/backups` | 面板备份文件 |
| `btautocheck-logs` | `/app/logs` | 运行日志 |
| `btautocheck-admin` | `/app/.admin_password` | 管理员密码 |
| `btautocheck-key` | `/app/.config.key` | 加密密钥 |

### 端口映射

- `5000:5000` - Web管理界面

---

## 🔧 常用命令

### 启动/停止/重启

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 停止并删除数据卷（⚠️ 慎用）
docker-compose down -v
```

### 查看状态

```bash
# 查看运行状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100

# 查看容器详情
docker inspect btautocheck
```

### 进入容器

```bash
# 进入容器Shell
docker exec -it btautocheck /bin/bash

# 在容器中执行命令
docker exec btautocheck python3 auto_update.py
docker exec btautocheck ls -la downloads/
```

### 更新镜像

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 重启容器
docker-compose up -d --force-recreate
```

---

## 📂 目录结构（容器内）

```
/app/
├── config.json             # 配置文件（从宿主机挂载）
├── .admin_password         # 管理员密码（数据卷）
├── .config.key             # 加密密钥（数据卷）
├── downloads/              # 下载目录（数据卷）
│   ├── LinuxPanel-*.zip
│   ├── SECURITY_REPORT_*.md
│   └── security_report_*.json
├── backups/                # 备份目录（数据卷）
│   └── backup_*.tar.gz
├── logs/                   # 日志目录（数据卷）
│   └── auto_check_*.log
├── templates/              # Web模板
├── *.py                    # Python脚本
└── *.sh                    # Shell脚本
```

---

## 🌐 Web管理界面

### 访问地址

```
http://你的服务器IP:5000
```

### 默认账号

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **首次登录后请立即修改密码！**

### 功能特点

- ⏰ **自动检测调度器** - 默认每1小时检测一次
- 🚀 **一键立即检测** - 无需等待定时任务
- ⏸️ **暂停/启动** - 灵活控制调度器
- 📊 **实时状态** - 显示下次执行时间
- 📋 **报告查看** - Markdown渲染，美观易读
- ⚙️ **配置管理** - 可视化配置所有选项

---

## 🐛 故障排查

### 1. 容器无法启动

```bash
# 查看详细错误
docker-compose logs

# 检查端口占用
netstat -tlnp | grep 5000

# 查看容器状态
docker ps -a
```

### 2. Web界面无法访问

```bash
# 检查容器是否运行
docker ps | grep btautocheck

# 检查端口映射
docker port btautocheck

# 检查防火墙
firewall-cmd --list-ports
ufw status

# 开放端口
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --reload
# 或
ufw allow 5000/tcp
```

### 3. 调度器不工作

```bash
# 进入容器检查
docker exec -it btautocheck /bin/bash

# 查看配置
cat config.json | grep scheduler

# 手动运行检测
python3 auto_update.py

# 查看Web日志
docker logs -f btautocheck
```

### 4. 数据丢失

```bash
# 列出所有数据卷
docker volume ls | grep btautocheck

# 检查数据卷内容
docker run --rm -v btautocheck-downloads:/data alpine ls -la /data

# 备份数据卷
docker run --rm -v btautocheck-downloads:/data -v $(pwd):/backup \
  alpine tar czf /backup/downloads-backup.tar.gz -C /data .

# 恢复数据卷
docker run --rm -v btautocheck-downloads:/data -v $(pwd):/backup \
  alpine tar xzf /backup/downloads-backup.tar.gz -C /data
```

---

## 🔄 数据备份与恢复

### 备份所有数据

```bash
# 创建备份目录
mkdir -p ~/btautocheck-backup

# 备份配置文件
cp config.json ~/btautocheck-backup/

# 备份所有数据卷
docker run --rm \
  -v btautocheck-downloads:/downloads \
  -v btautocheck-backups:/backups \
  -v btautocheck-logs:/logs \
  -v $(pwd)/btautocheck-backup:/backup \
  alpine tar czf /backup/all-data-$(date +%Y%m%d).tar.gz \
    /downloads /backups /logs

echo "✅ 备份完成: ~/btautocheck-backup/all-data-$(date +%Y%m%d).tar.gz"
```

### 恢复数据

```bash
# 停止容器
docker-compose down

# 恢复数据卷
docker run --rm \
  -v btautocheck-downloads:/downloads \
  -v btautocheck-backups:/backups \
  -v btautocheck-logs:/logs \
  -v $(pwd)/btautocheck-backup:/backup \
  alpine tar xzf /backup/all-data-YYYYMMDD.tar.gz -C /

# 恢复配置文件
cp ~/btautocheck-backup/config.json ./

# 重启容器
docker-compose up -d

echo "✅ 恢复完成"
```

---

## 🔐 安全建议

### 1. 修改默认密码

首次登录后立即在Web界面修改密码：

```
http://你的IP:5000 → 🔐 修改密码
```

### 2. 配置防火墙

只允许特定IP访问Web界面：

```bash
# firewalld
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="你的IP" port port="5000" protocol="tcp" accept'
firewall-cmd --reload

# ufw
ufw allow from 你的IP to any port 5000
```

### 3. 使用反向代理（推荐）

通过Nginx反向代理，启用HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name btautocheck.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📊 性能优化

### 资源限制

在`docker-compose.yml`中添加资源限制：

```yaml
services:
  btautocheck:
    # ... 其他配置 ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 日志轮转

限制日志大小：

```yaml
services:
  btautocheck:
    # ... 其他配置 ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🎯 生产环境建议

### 1. 使用独立数据库（未来）

当前版本使用JSON配置文件，未来可考虑使用数据库。

### 2. 设置自动重启

```yaml
restart: unless-stopped  # 已在docker-compose.yml中配置
```

### 3. 定期备份

```bash
# 添加cron任务（宿主机）
0 2 * * * cd /path/to/BTAUTOCHECK && bash backup.sh
```

### 4. 监控告警

使用Prometheus + Grafana监控容器状态。

---

## 📞 获取帮助

- **GitHub**: https://github.com/GSDPGIT/BTAUTOCHECK
- **Issues**: 提交Bug和功能建议
- **文档**: 查看README.md

---

## 📝 更新日志

### V2.0 (2025-11-03)

- ✅ 添加自动检测调度器
- ✅ 完善Docker支持
- ✅ 添加健康检查
- ✅ 数据持久化
- ✅ docker-compose支持

---

**🎉 享受BTAUTOCHECK带来的便利！**

