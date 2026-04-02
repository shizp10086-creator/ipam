import request from './request'

/**
 * 获取告警列表
 */
export function getAlerts(params) {
  return request({
    url: '/alerts',
    method: 'get',
    params
  })
}

/**
 * 获取告警详情
 */
export function getAlert(id) {
  return request({
    url: `/alerts/${id}`,
    method: 'get'
  })
}

/**
 * 解决告警
 */
export function resolveAlert(id) {
  return request({
    url: `/alerts/${id}/resolve`,
    method: 'put'
  })
}
