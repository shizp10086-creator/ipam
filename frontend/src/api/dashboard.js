import request from './request'

/**
 * 获取仪表板统计数据
 */
export function getStats(params) {
  return request({
    url: '/dashboard/stats',
    method: 'get',
    params
  })
}

/**
 * 获取图表数据
 */
export function getCharts(params) {
  return request({
    url: '/dashboard/charts',
    method: 'get',
    params
  })
}
