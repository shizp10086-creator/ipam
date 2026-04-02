#!/usr/bin/env python3
"""
Ping 代理服务
运行在宿主机上，为容器化的后端提供 ping 功能
"""
import asyncio
import platform
import json
from aiohttp import web
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ping_ip(ip_address: str, timeout: int = 2, count: int = 1, source_ip: str = None) -> dict:
    """
    执行 ping 操作
    
    Args:
        ip_address: 目标 IP 地址
        timeout: 超时时间（秒）
        count: ping 次数
        source_ip: 源 IP 地址（可选，用于指定从哪个网络接口发送 ping）
        
    Returns:
        dict: ping 结果
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000)]
            # Windows: 使用 -S 参数指定源 IP
            if source_ip:
                cmd.extend(["-S", source_ip])
            cmd.append(ip_address)
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout)]
            # Linux: 使用 -I 参数指定源 IP 或网络接口
            if source_ip:
                cmd.extend(["-I", source_ip])
            cmd.append(ip_address)
        
        logger.debug(f"执行 ping 命令: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout + 2
        )
        
        is_online = process.returncode == 0
        output = stdout.decode('utf-8', errors='ignore')
        error_output = stderr.decode('utf-8', errors='ignore')
        
        if is_online:
            logger.info(f"Ping {ip_address} 成功 (源IP: {source_ip or '默认'})")
        else:
            logger.warning(f"Ping {ip_address} 失败 (源IP: {source_ip or '默认'}): {error_output}")
        
        return {
            "ip_address": ip_address,
            "is_online": is_online,
            "source_ip": source_ip,
            "output": output if is_online else None,
            "error": error_output if not is_online else None
        }
        
    except asyncio.TimeoutError:
        logger.warning(f"Ping {ip_address} 超时 (源IP: {source_ip or '默认'})")
        return {
            "ip_address": ip_address,
            "is_online": False,
            "source_ip": source_ip,
            "error": "Timeout"
        }
    except Exception as e:
        logger.error(f"Ping {ip_address} 异常 (源IP: {source_ip or '默认'}): {e}")
        return {
            "ip_address": ip_address,
            "is_online": False,
            "source_ip": source_ip,
            "error": str(e)
        }


async def handle_ping_single(request):
    """处理单个 IP 的 ping 请求"""
    try:
        data = await request.json()
        ip_address = data.get('ip_address')
        timeout = data.get('timeout', 2)
        count = data.get('count', 1)
        source_ip = data.get('source_ip')  # 新增：源 IP 参数
        
        if not ip_address:
            return web.json_response(
                {"error": "ip_address is required"},
                status=400
            )
        
        result = await ping_ip(ip_address, timeout, count, source_ip)
        return web.json_response(result)
        
    except Exception as e:
        logger.error(f"Error handling ping request: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )


async def handle_ping_batch(request):
    """处理批量 IP 的 ping 请求"""
    try:
        data = await request.json()
        ip_addresses = data.get('ip_addresses', [])
        timeout = data.get('timeout', 2)
        count = data.get('count', 1)
        max_concurrent = data.get('max_concurrent', 50)
        source_ip = data.get('source_ip')  # 新增：源 IP 参数
        
        if not ip_addresses:
            return web.json_response(
                {"error": "ip_addresses is required"},
                status=400
            )
        
        logger.info(f"开始批量 ping {len(ip_addresses)} 个 IP (源IP: {source_ip or '默认'})")
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def ping_with_limit(ip):
            async with semaphore:
                return await ping_ip(ip, timeout, count, source_ip)
        
        # 并发执行所有 ping
        tasks = [ping_with_limit(ip) for ip in ip_addresses]
        results = await asyncio.gather(*tasks)
        
        online_count = sum(1 for r in results if r['is_online'])
        logger.info(f"批量 ping 完成: {online_count}/{len(results)} 在线")
        
        return web.json_response({
            "results": results,
            "total": len(results),
            "online": online_count,
            "source_ip": source_ip
        })
        
    except Exception as e:
        logger.error(f"Error handling batch ping request: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )


async def handle_health(request):
    """健康检查"""
    return web.json_response({"status": "healthy"})


def create_app():
    """创建应用"""
    app = web.Application()
    app.router.add_post('/ping', handle_ping_single)
    app.router.add_post('/ping/batch', handle_ping_batch)
    app.router.add_get('/health', handle_health)
    return app


if __name__ == '__main__':
    app = create_app()
    logger.info("Starting Ping Proxy Service on http://0.0.0.0:8001")
    web.run_app(app, host='0.0.0.0', port=8001)
