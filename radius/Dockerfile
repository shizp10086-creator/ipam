# FreeRADIUS 自定义镜像
# 基于官方镜像，预装 SQL 模块并配置好 IPAM 数据库对接
FROM freeradius/freeradius-server:latest

# 安装 MySQL 客户端库（SQL 模块依赖）
USER root
RUN apt-get update && apt-get install -y libmysqlclient-dev default-mysql-client && rm -rf /var/lib/apt/lists/*

# 复制自定义配置
COPY raddb/mods-available/sql /etc/raddb/mods-available/sql
COPY raddb/mods-available/eap /etc/raddb/mods-available/eap
COPY raddb/sites-available/default /etc/raddb/sites-available/default
COPY raddb/clients.conf /etc/raddb/clients.conf

# 启用 SQL 模块
RUN ln -sf /etc/raddb/mods-available/sql /etc/raddb/mods-enabled/sql

# 设置权限
RUN chown -R freerad:freerad /etc/raddb

USER freerad

# 以调试模式启动（生产环境去掉 -X）
CMD ["freeradius", "-f"]
