import request from './request'

/**
 * 获取 IP 地址列表
 */
export function getIPs(params) {
  return request({
    url: '/ips',
    method: 'get',
    params
  })
}

/**
 * 获取 IP 地址详情
 */
export function getIP(id) {
  return request({
    url: `/ips/${id}`,
    method: 'get'
  })
}

/**
 * 分配 IP 地址
 */
export function allocateIP(data) {
  return request({
    url: '/ips/allocate',
    method: 'post',
    data
  })
}

/**
 * 回收 IP 地址
 */
export function releaseIP(data) {
  return request({
    url: '/ips/release',
    method: 'post',
    data
  })
}

/**
 * 更新 IP 地址
 */
export function updateIP(id, data) {
  return request({
    url: `/ips/${id}`,
    method: 'put',
    data
  })
}

/**
 * 检查 IP 冲突
 */
export function checkConflict(data) {
  return request({
    url: '/ips/check-conflict',
    method: 'post',
    data
  })
}

/**
 * 扫描网段
 */
export function scanSegment(data) {
  return request({
    url: '/ips/scan',
    method: 'post',
    data
  })
}

/**
 * 获取扫描历史
 * 版本: 2026-02-07-v2
 */
export function getScanHistory(params) {
  console.log('getScanHistory被调用，参数:', params)
  console.log('请求URL: /ips/scan-history')
  return request({
    url: '/ips/scan-history',
    method: 'get',
    params
  })
}

/**
 * 批量更新 IP 状态
 */
export function batchUpdateIPStatus(data) {
  return request({
    url: '/ips/batch/update-status',
    method: 'put',
    data
  })
}
